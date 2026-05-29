from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserDefault, UserRole


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class UserOut(UserDefault):
    id: int

    class Config:
        from_attributes = True


class UserListOut(BaseModel):
    users: list[UserOut]
    total: int


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
