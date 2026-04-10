from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TotalTimeResponse(BaseModel):
    total_minutes: float


class TagTimeEntry(BaseModel):
    tag_id: int
    tag_name: str
    total_minutes: float


class TagTimeResponse(BaseModel):
    by_tags: list[TagTimeEntry]


class WorkspaceTimeEntry(BaseModel):
    workspace_id: Optional[int]
    workspace_name: Optional[str]
    total_minutes: float


class WorkspaceTimeResponse(BaseModel):
    by_workspaces: list[WorkspaceTimeEntry]


class PeriodTimeResponse(BaseModel):
    total_minutes: float
    start_date: datetime
    end_date: datetime


class TaskTimeLog(BaseModel):
    id: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: float


class TaskTimeResponse(BaseModel):
    task_id: int
    task_title: str
    total_minutes: float
    logs: list[TaskTimeLog]
