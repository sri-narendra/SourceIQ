from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from middleware.auth import get_current_user
from models.entities import User
from schemas.contracts import WorkspaceCreate, WorkspaceOut
from services.workspace_service import WorkspaceService

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


@router.post("", status_code=201)
def create_workspace(
    body: WorkspaceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = WorkspaceService(db)
    ws = svc.create(str(user.id), body.name, body.description)
    return {"success": True, "workspace_id": str(ws.id)}


@router.get("", response_model=list[WorkspaceOut])
def list_workspaces(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = WorkspaceService(db)
    return svc.with_doc_counts(svc.list_for_user(str(user.id)))


@router.delete("/{workspace_id}")
def delete_workspace(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = WorkspaceService(db)
    ws = svc.get_for_user(workspace_id, str(user.id))
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if not svc.delete(workspace_id):
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"success": True, "message": "Workspace deleted"}
