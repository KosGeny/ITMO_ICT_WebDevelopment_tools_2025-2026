from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user, require_admin,
)
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate, UserUpdate, UserOut, UserListOut,
    PasswordChange, Token,
)
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    session: Session = Depends(get_session),
) -> User:
    existing = session.exec(select(User).where(User.username == user_in.username)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Имя пользователя занято")
    existing_email = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован")

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=token, token_type="bearer")


@router.get("/me", response_model=UserOut)
def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.put("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: PasswordChange,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    from app.core.auth import verify_password, get_password_hash
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный старый пароль")
    current_user.hashed_password = get_password_hash(password_data.new_password)
    session.add(current_user)
    session.commit()
    return {"message": "Пароль успешно изменён"}


@router.get("/users", response_model=UserListOut)
def list_users(
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
    _admin: User = Depends(require_admin),
) -> UserListOut:
    statement = select(User)
    total = len(session.exec(statement).all())
    statement = statement.limit(limit).offset(offset)
    users = session.exec(statement).all()
    return UserListOut(users=users, total=total)
