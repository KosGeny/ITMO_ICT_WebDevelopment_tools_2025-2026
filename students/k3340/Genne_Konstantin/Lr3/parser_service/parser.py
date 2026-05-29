import os
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, select, create_engine

from app.models import Workspace, Tag, Task, TaskTag, TaskStatus, TaskPriority


DATABASE_URL = os.getenv("DATABASE_URL")


def extract_owner_repo_from_url(url):
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]
    return path_parts[0], path_parts[1]


def parse_issues_from_page(soup):
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


def get_or_create_workspace(db: Session, full_name: str, description: str, owner_id: int):
    result = db.exec(select(Workspace).where(Workspace.name == full_name))
    workspace = result.first()
    if not workspace:
        workspace = Workspace(name=full_name, description=description, owner_id=owner_id)
        db.add(workspace)
        db.flush()
    return workspace


def task_exists(db: Session, title: str, workspace_id: int) -> bool:
    result = db.exec(
        select(Task).where(Task.title == title, Task.workspace_id == workspace_id)
    )
    return result.first() is not None


def parse_github_issues(url: str, user_id: int, html_content: str = None):
    engine = create_engine(DATABASE_URL, echo=False, pool_size=5)
    
    owner, repo = extract_owner_repo_from_url(url)
    full_name = f"{owner}/{repo}"
    
    if html_content:
        html = html_content
    else:
        headers = {"User-Agent": "Lab-Parser/1.0"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text
    
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else None
    description = f"{page_title} | {url}" if page_title else url
    
    issues = parse_issues_from_page(soup)
    
    db = Session(engine)
    try:
        workspace = get_or_create_workspace(db, full_name, description, user_id)
        
        tasks_created = 0
        tags_created = 0
        tag_cache = {}
        
        for issue in issues:
            if task_exists(db, issue["title"], workspace.id):
                continue
            
            task = Task(
                title=issue["title"][:300],
                description=issue["url"],
                status=TaskStatus.todo,
                priority=TaskPriority.medium,
                owner_id=user_id,
                workspace_id=workspace.id,
            )
            db.add(task)
            db.flush()
            tasks_created += 1
            
            seen_labels = set()
            for label_name in issue["labels"]:
                label_name = label_name.strip()
                if not label_name or label_name in seen_labels:
                    continue
                seen_labels.add(label_name)
                
                cache_key = (label_name, user_id)
                tag = tag_cache.get(cache_key)
                if tag is None:
                    result = db.exec(
                        select(Tag).where(Tag.name == label_name, Tag.owner_id == user_id)
                    )
                    tag = result.first()
                    if not tag:
                        tag = Tag(name=label_name, owner_id=user_id)
                        db.add(tag)
                        db.flush()
                        tags_created += 1
                    tag_cache[cache_key] = tag
                
                task_tag = TaskTag(task_id=task.id, tag_id=tag.id, is_primary=False)
                db.add(task_tag)
        
        db.commit()
        
        return {
            "success": True,
            "tasks_created": tasks_created,
            "tags_created": tags_created,
            "workspace": full_name,
            "total_issues_found": len(issues)
        }
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
        engine.dispose()