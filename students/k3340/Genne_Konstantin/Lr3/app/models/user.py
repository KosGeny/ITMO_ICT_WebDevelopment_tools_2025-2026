from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship
import enum

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.tag import Tag
    from app.models.task import Task


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class UserDefault(SQLModel):
    username: str = Field(index=True, unique=True, max_length=100)
    email: str = Field(index=True, unique=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.user)


class User(UserDefault, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    workspaces: List["Workspace"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )
    tags: List["Tag"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )
    tasks: List["Task"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "passive_deletes": True},
    )
