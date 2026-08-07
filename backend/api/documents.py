from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from database.session import get_db
from middleware.auth import get_current_user
from models.entities import User
from services.document_service import DocumentService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/upload", status_code=202)
def upload_document(
    workspace_id: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = DocumentService(db)
    try:
        result = svc.upload(workspace_id, str(user.id), file)
    except ValueError as exc:
        if str(exc) == "invalid_file":
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type"
            )
        raise
    return {"success": True, **result}


@router.get("")
def list_documents(
    workspace_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = DocumentService(db)
    docs = svc.list(workspace_id)
    return [
        {
            "id": d.id,
            "name": d.original_name,
            "status": d.status.value,
            "uploaded_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = DocumentService(db)
    if not svc.delete(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True, "message": "Document deleted successfully"}
