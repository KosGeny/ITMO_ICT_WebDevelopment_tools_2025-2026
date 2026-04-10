from sqlmodel import SQLModel
from pydantic import ConfigDict
from typing import Optional

class TagBase(SQLModel):
    name: str

class TagCreate(TagBase): pass

class TagUpdate(SQLModel):
    name: Optional[str] = None

class TagRead(TagBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int

class TagListOut(SQLModel):
    tags: list[TagRead]
    total: int