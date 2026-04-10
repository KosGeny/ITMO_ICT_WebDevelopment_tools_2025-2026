from sqlmodel import SQLModel
from pydantic import ConfigDict
from typing import Optional
from datetime import datetime

class WorkspaceBase(SQLModel):
    name: str
    description: Optional[str] = None

class WorkspaceCreate(WorkspaceBase): pass

class WorkspaceUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None

class WorkspaceRead(WorkspaceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int

class TaskBrief(SQLModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    status: str
    priority: str
    deadline: Optional[datetime] = None

class WorkspaceWithTasksRead(WorkspaceRead):
    tasks: list[TaskBrief] = []

class WorkspaceListOut(SQLModel):
    workspaces: list[WorkspaceRead]
    total: int