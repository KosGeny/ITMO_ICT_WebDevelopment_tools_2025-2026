# app/schemas/time_log.py
from sqlmodel import SQLModel
from pydantic import ConfigDict, computed_field
from typing import Optional
from datetime import datetime, timezone


class TimeLogCreate(SQLModel):
    task_id: int


class TimeLogRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_id: int
    start_time: datetime
    end_time: Optional[datetime] = None

    @computed_field
    @property
    def duration_minutes(self) -> float:
        end = self.end_time or datetime.now(timezone.utc)
        start = self.start_time
        
        if start.tzinfo is None and end.tzinfo is not None:
            start = start.replace(tzinfo=timezone.utc)
        elif start.tzinfo is not None and end.tzinfo is None:
            end = end.replace(tzinfo=None)
            
        return round((end - start).total_seconds() / 60, 2)