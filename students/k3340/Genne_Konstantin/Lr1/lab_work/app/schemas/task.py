from sqlmodel import SQLModel, Field
from pydantic import ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority
from app.schemas.time_log import TimeLogRead
from app.schemas.task_tag import TaskTagRead

class TaskTagInput(SQLModel):
    tag_id: int
    is_primary: bool = False

class WorkspaceBrief(SQLModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class TaskBase(SQLModel):
    title: str = Field(max_length=300)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: TaskPriority = TaskPriority.medium
    deadline: Optional[datetime] = None
    workspace_id: Optional[int] = None
    status: TaskStatus = TaskStatus.todo

class TaskCreate(TaskBase):
    tag_ids: List[TaskTagInput] = []

class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime] = None
    workspace_id: Optional[int] = None
    tag_ids: Optional[List[TaskTagInput]] = None

class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

class TaskOut(TaskRead):
    workspace: Optional[WorkspaceBrief] = None
    task_tags: List[TaskTagRead] = []
    time_logs: List[TimeLogRead] = []

class TaskListOut(SQLModel):
    tasks: List[TaskOut]
    total: int