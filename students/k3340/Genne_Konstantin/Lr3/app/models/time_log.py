from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.task import Task


class TimeLogBase(SQLModel):
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = Field(default=None)


class TimeLogDefault(TimeLogBase):
    task_id: int = Field(foreign_key="tasks.id", ondelete="CASCADE", index=True)


class TimeLog(TimeLogDefault, table=True):
    __tablename__ = "time_logs"

    id: Optional[int] = Field(default=None, primary_key=True)

    task: "Task" = Relationship(back_populates="time_logs")
