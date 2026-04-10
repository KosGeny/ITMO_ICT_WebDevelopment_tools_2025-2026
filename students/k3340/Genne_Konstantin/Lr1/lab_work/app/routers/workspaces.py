from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.workspace import Workspace
from app.models.task import Task
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceRead, WorkspaceWithTasksRead, WorkspaceListOut

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.post("/", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace_in: WorkspaceCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Workspace:
    ws = Workspace.model_validate(workspace_in, update={"owner_id": current_user.id})
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return ws

@router.get("/", response_model=WorkspaceListOut)
def list_workspaces(
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> WorkspaceListOut:
    stmt = select(Workspace).where(Workspace.owner_id == current_user.id)
    total = session.exec(select(func.count(Workspace.id)).where(Workspace.owner_id == current_user.id)).one()
    workspaces = session.exec(stmt.limit(limit).offset(offset)).all()
    return WorkspaceListOut(workspaces=workspaces, total=total)

@router.get("/{workspace_id}", response_model=WorkspaceWithTasksRead)
def get_workspace(
    workspace_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Workspace:
    stmt = select(Workspace).where(Workspace.id == workspace_id, Workspace.owner_id == current_user.id)
    workspace = session.exec(stmt).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Рабочее пространство не найдено")
    return workspace

@router.patch("/{workspace_id}", response_model=WorkspaceRead)
def update_workspace(
    workspace_id: int,
    workspace_in: WorkspaceUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Workspace:
    workspace = session.get(Workspace, workspace_id)
    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Рабочее пространство не найдено")
    
    for key, value in workspace_in.model_dump(exclude_unset=True).items():
        setattr(workspace, key, value)
    session.add(workspace)
    session.commit()
    session.refresh(workspace)
    return workspace

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    workspace = session.get(Workspace, workspace_id)
    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Рабочее пространство не найдено")
    session.delete(workspace)
    session.commit()