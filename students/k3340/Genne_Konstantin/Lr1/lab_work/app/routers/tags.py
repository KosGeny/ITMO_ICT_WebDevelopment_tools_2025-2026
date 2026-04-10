from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagUpdate, TagRead, TagListOut

router = APIRouter(prefix="/tags", tags=["Tags"])

@router.post("/", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_in: TagCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Tag:
    existing = session.exec(select(Tag.id).where(Tag.name == tag_in.name, Tag.owner_id == current_user.id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Тег с таким именем уже существует")
    
    tag = Tag.model_validate(tag_in, update={"owner_id": current_user.id})
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag

@router.get("/", response_model=TagListOut)
def list_tags(
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TagListOut:
    stmt = select(Tag).where(Tag.owner_id == current_user.id)
    total = session.exec(select(func.count(Tag.id)).where(Tag.owner_id == current_user.id)).one()
    tags = session.exec(stmt.limit(limit).offset(offset)).all()
    return TagListOut(tags=tags, total=total)

@router.get("/{tag_id}", response_model=TagRead)
def get_tag(
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Tag:
    tag = session.get(Tag, tag_id)
    if not tag or tag.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Тег не найден")
    return tag

@router.put("/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: int,
    tag_in: TagUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Tag:
    tag = session.get(Tag, tag_id)
    if not tag or tag.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Тег не найден или нет доступа")
    
    for key, value in tag_in.model_dump(exclude_unset=True).items():
        setattr(tag, key, value)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    tag = session.get(Tag, tag_id)
    if not tag or tag.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Тег не найден или нет доступа")
    session.delete(tag)
    session.commit()