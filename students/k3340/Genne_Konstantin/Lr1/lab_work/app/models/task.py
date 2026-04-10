from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
import enum

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.task_tag import TaskTag
    from app.models.time_log import TimeLog
    from app.models.user import User


class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    paused = "paused"
    done = "done"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskBase(SQLModel):
    title: str = Field(max_length=300)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: TaskPriority = Field(default=TaskPriority.medium)
    deadline: Optional[datetime] = Field(default=None)
    workspace_id: Optional[int] = Field(default=None, foreign_key="workspaces.id", ondelete="SET NULL", index=True)


class TaskDefault(TaskBase):
    status: TaskStatus = Field(default=TaskStatus.todo)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner_id: int = Field(foreign_key="users.id", ondelete="CASCADE", index=True)


class Task(TaskDefault, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)

    owner: "User" = Relationship(back_populates="tasks")
    workspace: Optional["Workspace"] = Relationship(back_populates="tasks")
    task_tags: list["TaskTag"] = Relationship(
        back_populates="task",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )
    time_logs: list["TimeLog"] = Relationship(
        back_populates="task",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )
