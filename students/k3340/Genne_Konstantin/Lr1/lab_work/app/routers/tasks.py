from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.task import Task, TaskStatus
from app.models.task_tag import TaskTag
from app.models.tag import Tag
from app.models.workspace import Workspace
from app.models.time_log import TimeLog
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut, TaskListOut, TimeLogRead

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Task:
    if task_in.workspace_id:
        ws = session.get(Workspace, task_in.workspace_id)
        if not ws or ws.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к рабочему пространству")

    task = Task.model_validate(task_in, update={"owner_id": current_user.id})
    session.add(task)
    session.flush()

    for tag_entry in task_in.tag_ids:
        tag = session.get(Tag, tag_entry.tag_id)
        if tag and tag.owner_id == current_user.id:
            session.add(TaskTag(task_id=task.id, tag_id=tag.id, is_primary=tag_entry.is_primary))

    session.commit()
    session.refresh(task)
    return task

@router.get("/", response_model=TaskListOut)
def list_tasks(
    limit: int = Query(20, le=100),
    offset: int = 0,
    status_filter: Optional[TaskStatus] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskListOut:
    stmt = select(Task).where(Task.owner_id == current_user.id)
    if status_filter:
        stmt = stmt.where(Task.status == status_filter)

    count_stmt = select(func.count(Task.id)).where(Task.owner_id == current_user.id)
    if status_filter:
        count_stmt = count_stmt.where(Task.status == status_filter)
    total = session.exec(count_stmt).one()

    tasks = session.exec(stmt.offset(offset).limit(limit)).all()
    return TaskListOut(tasks=tasks, total=total)

@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = session.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task

@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = session.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена или нет доступа")

    if task_in.workspace_id is not None:
        ws = session.get(Workspace, task_in.workspace_id)
        if not ws or ws.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к рабочему пространству")

    update_data = task_in.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)

    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.now(timezone.utc)

    if tag_ids is not None:
        session.exec(select(TaskTag).where(TaskTag.task_id == task.id).delete())
        for tag_entry in tag_ids:
            tag = session.get(Tag, tag_entry.tag_id)
            if tag and tag.owner_id == current_user.id:
                session.add(TaskTag(task_id=task.id, tag_id=tag.id, is_primary=tag_entry.is_primary))

    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    task = session.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена или нет доступа")
    session.delete(task)
    session.commit()

@router.post("/{task_id}/timer/start", response_model=TimeLogRead, status_code=status.HTTP_201_CREATED)
def start_timer(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TimeLog:
    task = session.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if task.status == TaskStatus.done:
        raise HTTPException(status_code=400, detail="Нельзя запустить таймер для завершённой задачи")

    time_log = TimeLog(task_id=task_id, start_time=datetime.now(timezone.utc))
    task.status = TaskStatus.in_progress
    task.updated_at = datetime.now(timezone.utc)
    session.add(time_log)
    session.add(task)
    session.commit()
    session.refresh(time_log)
    return time_log

@router.post("/{task_id}/timer/pause", response_model=TimeLogRead)
def pause_timer(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TimeLog:
    task = session.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    active_log = session.exec(
        select(TimeLog).where(TimeLog.task_id == task_id, TimeLog.end_time == None).order_by(TimeLog.start_time.desc())
    ).first()
    if not active_log:
        raise HTTPException(status_code=400, detail="Активный таймер не найден")

    active_log.end_time = datetime.now(timezone.utc)
    task.status = TaskStatus.paused
    task.updated_at = datetime.now(timezone.utc)
    session.add(active_log)
    session.add(task)
    session.commit()
    session.refresh(active_log)
    return active_log

@router.post("/{task_id}/timer/stop", response_model=TimeLogRead)
def stop_timer(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TimeLog:
    task = session.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    active_log = session.exec(
        select(TimeLog).where(TimeLog.task_id == task_id, TimeLog.end_time == None).order_by(TimeLog.start_time.desc())
    ).first()
    if not active_log:
        raise HTTPException(status_code=400, detail="Активный таймер не найден")

    active_log.end_time = datetime.now(timezone.utc)
    task.status = TaskStatus.todo
    task.updated_at = datetime.now(timezone.utc)
    session.add(active_log)
    session.add(task)
    session.commit()
    session.refresh(active_log)
    return active_log

@router.get("/upcoming-deadlines/", response_model=TaskListOut)
def upcoming_deadlines(
    hours: int = Query(default=24, ge=1, le=168),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskListOut:
    now = datetime.now(timezone.utc)
    deadline_limit = now + timedelta(hours=hours)
    
    stmt = (
        select(Task)
        .where(Task.owner_id == current_user.id)
        .where(Task.deadline != None)
        .where(Task.deadline <= deadline_limit)
        .where(Task.deadline >= now)
        .where(Task.status != TaskStatus.done)
    )
    tasks = session.exec(stmt).all()
    return TaskListOut(tasks=tasks, total=len(tasks))