from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.task_tag import TaskTag
    from app.models.user import User


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
