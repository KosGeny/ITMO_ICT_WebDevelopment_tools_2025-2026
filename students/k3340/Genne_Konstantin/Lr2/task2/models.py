import enum
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from sqlalchemy import Column, Enum


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    
    workspaces: List["Workspace"] = Relationship(back_populates="owner")
    tags: List["Tag"] = Relationship(back_populates="owner")
    tasks: List["Task"] = Relationship(back_populates="owner")


class WorkspaceBase(SQLModel):
    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)


class WorkspaceDefault(WorkspaceBase):
    owner_id: int = Field(foreign_key="users.id", ondelete="CASCADE", index=True)


class Workspace(WorkspaceDefault, table=True):
    __tablename__ = "workspaces"

    id: Optional[int] = Field(default=None, primary_key=True)

    owner: "User" = Relationship(back_populates="workspaces")
    tasks: list["Task"] = Relationship(
        back_populates="workspace",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )


class TagBase(SQLModel):
    name: str = Field(max_length=100, index=True)


class TagDefault(TagBase):
    owner_id: int = Field(foreign_key="users.id", ondelete="CASCADE", index=True)


class Tag(TagDefault, table=True):
    __tablename__ = "tags"

    id: Optional[int] = Field(default=None, primary_key=True)

    owner: "User" = Relationship(back_populates="tags")
    task_tags: list["TaskTag"] = Relationship(
        back_populates="tag",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )


class TaskTagBase(SQLModel):
    is_primary: bool = Field(default=False)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)


class TaskTagDefault(TaskTagBase):
    task_id: int = Field(foreign_key="tasks.id", ondelete="CASCADE", index=True)
    tag_id: int = Field(foreign_key="tags.id", ondelete="CASCADE", index=True)


class TaskTag(TaskTagDefault, table=True):
    __tablename__ = "task_tags"
    __table_args__ = (UniqueConstraint("task_id", "tag_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)

    task: "Task" = Relationship(back_populates="task_tags")
    tag: "Tag" = Relationship(back_populates="task_tags")

    @property
    def name(self) -> str:
        """Возвращает имя связанного тега"""
        return self.tag.name if self.tag else ""


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


class TimeLog(SQLModel, table=True):
    __tablename__ = "time_logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: Optional[int] = Field(default=None, foreign_key="tasks.id", ondelete="CASCADE")
    task: Optional[Task] = Relationship(back_populates="time_logs")