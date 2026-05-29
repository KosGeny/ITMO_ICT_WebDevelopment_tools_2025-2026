from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from datetime import datetime

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.task import Task
from app.models.task_tag import TaskTag
from app.models.tag import Tag
from app.models.workspace import Workspace
from app.models.time_log import TimeLog
from app.models.user import User
from app.schemas.analytics import (
    TotalTimeResponse, TagTimeResponse, TagTimeEntry,
    WorkspaceTimeResponse, WorkspaceTimeEntry, PeriodTimeResponse,
    TaskTimeResponse, TaskTimeLog,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


_duration_sql = func.coalesce(
    func.extract("epoch", TimeLog.end_time - TimeLog.start_time) / 60,
    func.extract("epoch", func.now() - TimeLog.start_time) / 60,
    0
)


@router.get("/total-time", response_model=TotalTimeResponse)
def total_time(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TotalTimeResponse:
    statement = (
        select(func.coalesce(func.sum(_duration_sql), 0))
        .join(Task, TimeLog.task_id == Task.id)
        .where(Task.owner_id == current_user.id)
    )
    total = session.exec(statement).one()
    return TotalTimeResponse(total_minutes=round(float(total), 2))


@router.get("/by-tag", response_model=TagTimeResponse)
def time_by_tag(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TagTimeResponse:
    statement = (
        select(
            Tag.id,
            Tag.name,
            func.coalesce(func.sum(_duration_sql), 0),
        )
        .join(TaskTag, Tag.id == TaskTag.tag_id)
        .join(Task, TaskTag.task_id == Task.id)
        .join(TimeLog, Task.id == TimeLog.task_id)
        .where(Task.owner_id == current_user.id)
        .group_by(Tag.id, Tag.name)
    )
    rows = session.exec(statement).all()
    entries = [TagTimeEntry(tag_id=r[0], tag_name=r[1], total_minutes=round(float(r[2]), 2)) for r in rows]
    return TagTimeResponse(by_tags=entries)


@router.get("/by-workspace", response_model=WorkspaceTimeResponse)
def time_by_workspace(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> WorkspaceTimeResponse:
    statement = (
        select(
            Workspace.id,
            Workspace.name,
            func.coalesce(func.sum(_duration_sql), 0),
        )
        .join(Task, Workspace.id == Task.workspace_id)
        .join(TimeLog, Task.id == TimeLog.task_id)
        .where(Task.owner_id == current_user.id)
        .group_by(Workspace.id, Workspace.name)
    )
    rows = session.exec(statement).all()
    entries = [WorkspaceTimeEntry(workspace_id=r[0], workspace_name=r[1], total_minutes=round(float(r[2]), 2)) for r in rows]

    stmt_no_ws = (
        select(func.coalesce(func.sum(_duration_sql), 0))
        .join(Task, TimeLog.task_id == Task.id)
        .where(Task.owner_id == current_user.id)
        .where(Task.workspace_id == None)
    )
    no_ws_total = session.exec(stmt_no_ws).one()
    if float(no_ws_total) > 0:
        entries.append(WorkspaceTimeEntry(workspace_id=None, workspace_name="Без рабочего пространства", total_minutes=round(float(no_ws_total), 2)))

    return WorkspaceTimeResponse(by_workspaces=entries)


@router.get("/by-period", response_model=PeriodTimeResponse)
def time_by_period(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PeriodTimeResponse:
    if start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date должен быть меньше end_date")

    statement = (
        select(func.coalesce(func.sum(_duration_sql), 0))
        .join(Task, TimeLog.task_id == Task.id)
        .where(Task.owner_id == current_user.id)
        .where(TimeLog.start_time >= start_date)
        .where(TimeLog.start_time <= end_date)
    )
    total = session.exec(statement).one()
    return PeriodTimeResponse(total_minutes=round(float(total), 2), start_date=start_date, end_date=end_date)


@router.get("/task/{task_id}", response_model=TaskTimeResponse)
def task_time(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskTimeResponse:
    task = session.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")

    stmt_total = (
        select(func.coalesce(func.sum(_duration_sql), 0))
        .where(TimeLog.task_id == task_id)
    )
    total = session.exec(stmt_total).one()

    logs = session.exec(select(TimeLog).where(TimeLog.task_id == task_id).order_by(TimeLog.start_time.desc())).all()

    log_entries = []
    for log in logs:
        duration = round((log.end_time - log.start_time).total_seconds() / 60, 2) if log.end_time else \
            round((datetime.utcnow() - log.start_time).total_seconds() / 60, 2)
        log_entries.append(TaskTimeLog(
            id=log.id,
            start_time=log.start_time,
            end_time=log.end_time,
            duration_minutes=duration,
        ))

    return TaskTimeResponse(
        task_id=task_id,
        task_title=task.title,
        total_minutes=round(float(total), 2),
        logs=log_entries,
    )
