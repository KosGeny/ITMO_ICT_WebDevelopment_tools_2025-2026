from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.tag import Tag


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