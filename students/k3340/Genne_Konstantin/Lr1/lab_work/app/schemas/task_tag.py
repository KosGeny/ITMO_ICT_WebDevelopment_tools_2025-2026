from sqlmodel import SQLModel
from pydantic import ConfigDict
from datetime import datetime

class TaskTagRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)
    tag_id: int
    name: str
    is_primary: bool
    assigned_at: datetime