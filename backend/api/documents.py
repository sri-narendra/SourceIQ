from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from storage.s3.client import s3_client

from database.session import get_db
from middleware.auth import get_current_user
from models.entities import DocumentChunk, User, Workspace
from repositories.base import WorkspaceRepository
from services.document_service import DocumentService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

_CONTENT_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "webp": "image/webp",
    "txt": "text/plain",
    "md": "text/markdown",
    "csv": "text/csv",
    "json": "application/json",
    "html": "text/html",
}


def _require_workspace(db: Session, workspace_id: str, user: User) -> Workspace:
    ws = WorkspaceRepository(db).get_for_user(workspace_id, str(user.id))
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ws


def _require_document_owner(db: Session, document_id: str, user: User):
    svc = DocumentService(db)
    doc = svc.get(document_id)
    if not doc or not WorkspaceRepository(db).get_for_user(str(doc.workspace_id), str(user.id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.post("/upload", status_code=202)
def upload_document(
    workspace_id: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_workspace(db, workspace_id, user)
    svc = DocumentService(db)
    try:
        result = svc.upload(workspace_id, str(user.id), file)
    except ValueError as exc:
        if str(exc) == "invalid_type":
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type"
            )
        if str(exc) == "too_large":
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="File too large"
            )
        raise
    return {"success": True, **result}


@router.get("")
def list_documents(
    workspace_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_workspace(db, workspace_id, user)
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


@router.get("/{document_id}/preview")
def document_preview(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _require_document_owner(db, document_id, user)
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc.id)
        .order_by(DocumentChunk.chunk_number)
        .all()
    )
    content = "\n\n".join(c.content for c in chunks) if chunks else ""
    return {"id": str(doc.id), "name": doc.original_name, "content": content[:8000]}


@router.get("/{document_id}/file")
def document_file(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = _require_document_owner(db, document_id, user)
    ext = doc.file_type.lower()
    data = s3_client.download(doc.s3_key) if doc.s3_key else b""
    if not data:
        raise HTTPException(status_code=404, detail="File not found")
    resp = Response(content=data, media_type=_CONTENT_TYPES.get(ext, "application/octet-stream"))
    resp.headers["Content-Disposition"] = f'inline; filename="{doc.original_name}"'
    return resp


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_document_owner(db, document_id, user)
    svc = DocumentService(db)
    if not svc.delete(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True, "message": "Document deleted successfully"}
