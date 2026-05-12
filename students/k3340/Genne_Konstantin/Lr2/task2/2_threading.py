import os
import time
import threading
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select

from models import Workspace, Tag, Task, TaskTag, TaskStatus, TaskPriority

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("+asyncpg", "+psycopg2")
DEFAULT_USER_ID = 1


def extract_owner_repo_from_url(url):
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]
    return path_parts[0], path_parts[1]


def parse_issues_from_page(html):
    soup = BeautifulSoup(html, "html.parser")
    tasks = []
    seen_urls = set()

    title_links = soup.find_all("a", attrs={"data-testid": "issue-pr-title-link"})
    for link in title_links:
        issue_url = link.get("href", "")
        if not issue_url:
            continue
        if issue_url.startswith("/"):
            issue_url = urljoin("https://github.com", issue_url)
        if issue_url in seen_urls:
            continue
        seen_urls.add(issue_url)

        title = link.get_text(strip=True)
        if not title or len(title) < 3:
            continue

        labels = []
        issue_li = link.find_parent("li")
        if issue_li:
            for badge in issue_li.find_all("div", class_=lambda c: c and "TrailingBadge" in c):
                lbl_span = badge.find("span", class_=lambda c: c and "prc-Text-Text-" in c)
                if lbl_span:
                    label_text = lbl_span.get_text(strip=True)
                    if label_text:
                        labels.append(label_text)

        tasks.append({"title": title, "url": issue_url, "labels": labels})
    return tasks


def get_or_create_workspace(db, full_name, description, owner_id):
    workspace = db.execute(
        select(Workspace).where(Workspace.name == full_name)
    ).scalar_one_or_none()
    if not workspace:
        workspace = Workspace(name=full_name, description=description, owner_id=owner_id)
        db.add(workspace)
        db.flush()
    return workspace


def task_exists(db, title, workspace_id):
    return db.execute(
        select(Task).where(Task.title == title, Task.workspace_id == workspace_id)
    ).first() is not None


def parse_and_save(engine, issues_url, owner_id):
    owner, repo = extract_owner_repo_from_url(issues_url)
    full_name = f"{owner}/{repo}"

    headers = {"User-Agent": "Lab-Parser/1.0"}
    resp = requests.get(issues_url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else None
    description = f"{page_title} | {issues_url}" if page_title else issues_url

    print(f"[{threading.current_thread().name}] Заголовок страницы Issues {full_name}: {page_title}")

    issues = parse_issues_from_page(resp.text)

    with Session(engine) as db:
        workspace = get_or_create_workspace(db, full_name, description, owner_id)

        for issue in issues:
            if task_exists(db, issue["title"], workspace.id):
                continue

            task = Task(
                title=issue["title"][:300],
                description=issue["url"],
                status=TaskStatus.todo,
                priority=TaskPriority.medium,
                owner_id=owner_id,
                workspace_id=workspace.id,
            )
            db.add(task)
            db.flush()

            seen_labels = set()
            for label_name in issue["labels"]:
                label_name = label_name.strip()
                if not label_name or label_name in seen_labels:
                    continue
                seen_labels.add(label_name)

                tag = db.execute(
                    select(Tag).where(Tag.name == label_name, Tag.owner_id == owner_id)
                ).scalars().first()
                if not tag:
                    tag = Tag(name=label_name, owner_id=owner_id)
                    db.add(tag)
                    db.flush()

                task_tag = TaskTag(task_id=task.id, tag_id=tag.id, is_primary=False)
                db.add(task_tag)

        db.commit()


def thread_target(urls, owner_id, engine):
    for url in urls:
        parse_and_save(engine, url, owner_id)


def main():
    urls = [
        "https://github.com/psf/requests/issues",
        "https://github.com/tiangolo/fastapi/issues",
        "https://github.com/tiangolo/sqlmodel/issues",
        "https://github.com/langchain-ai/langchain/issues",
        "https://github.com/pytorch/pytorch/issues",
        "https://github.com/Kludex/uvicorn/issues",
    ]

    NUM_THREADS = 3
    chunk_size = len(urls) // NUM_THREADS + (1 if len(urls) % NUM_THREADS else 0)
    chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]

    engine = create_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=10)

    start = time.time()
    threads = []
    for chunk in chunks:
        t = threading.Thread(
            target=thread_target,
            args=(chunk, DEFAULT_USER_ID, engine),
            name=f"Thread-{len(threads)}"
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    engine.dispose()
    elapsed = time.time() - start
    print(f"\nThreading: выполнение завершено за {elapsed:.2f} сек")


if __name__ == "__main__":
    main()