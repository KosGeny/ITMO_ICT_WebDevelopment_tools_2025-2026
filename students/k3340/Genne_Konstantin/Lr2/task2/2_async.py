import os
import asyncio
import time
from urllib.parse import urlparse, urljoin

import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import select

from models import Workspace, Tag, Task, TaskTag, TaskStatus, TaskPriority

load_dotenv()

DATABASE_URL_ASYNC = os.getenv("DATABASE_URL")
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


async def get_or_create_workspace(db, full_name, description, owner_id):
    result = await db.execute(select(Workspace).where(Workspace.name == full_name))
    workspace = result.scalar_one_or_none()
    if not workspace:
        workspace = Workspace(name=full_name, description=description, owner_id=owner_id)
        db.add(workspace)
        await db.flush()
    return workspace


async def task_exists(db: AsyncSession, title: str, workspace_id: int) -> bool:
    result = await db.execute(
        select(Task).where(Task.title == title, Task.workspace_id == workspace_id)
    )
    return result.first() is not None


async def parse_and_save(engine, session_factory, http_session, issues_url, owner_id):
    owner, repo = extract_owner_repo_from_url(issues_url)
    full_name = f"{owner}/{repo}"

    headers = {"User-Agent": "Lab-Parser/1.0"}
    async with http_session.get(issues_url, headers=headers) as resp:
        resp.raise_for_status()
        html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else None
    description = f"{page_title} | {issues_url}" if page_title else issues_url

    print(f"Заголовок страницы Issues {full_name}: {page_title}")

    issues = parse_issues_from_page(html)

    async with session_factory() as db:
        workspace = await get_or_create_workspace(db, full_name, description, owner_id)

        for issue in issues:
            if await task_exists(db, issue["title"], workspace.id):
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
            await db.flush()

            seen_labels = set()
            for label_name in issue["labels"]:
                label_name = label_name.strip()
                if not label_name or label_name in seen_labels:
                    continue
                seen_labels.add(label_name)

                result = await db.execute(
                    select(Tag).where(Tag.name == label_name, Tag.owner_id == owner_id)
                )
                tag = result.scalars().first()
                if not tag:
                    tag = Tag(name=label_name, owner_id=owner_id)
                    db.add(tag)
                    await db.flush()

                task_tag = TaskTag(task_id=task.id, tag_id=tag.id, is_primary=False)
                db.add(task_tag)

        await db.commit()


async def limited_parse(semaphore, *args, **kwargs):
    async with semaphore:
        await parse_and_save(*args, **kwargs)


async def main():
    urls = [
        "https://github.com/psf/requests/issues",
        "https://github.com/tiangolo/fastapi/issues",
        "https://github.com/tiangolo/sqlmodel/issues",
        "https://github.com/langchain-ai/langchain/issues",
        "https://github.com/pytorch/pytorch/issues",
        "https://github.com/Kludex/uvicorn/issues",
    ]

    engine = create_async_engine(DATABASE_URL_ASYNC, echo=False, pool_size=5)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    semaphore = asyncio.Semaphore(3)

    async with aiohttp.ClientSession() as http_session:
        tasks = [
            limited_parse(semaphore, engine, session_factory, http_session, url, DEFAULT_USER_ID)
            for url in urls
        ]
        start = time.time()
        await asyncio.gather(*tasks)

    await engine.dispose()
    elapsed = time.time() - start
    print(f"\nAsyncio: выполнение завершено за {elapsed:.2f} сек")


if __name__ == "__main__":
    asyncio.run(main())