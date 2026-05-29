from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


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
