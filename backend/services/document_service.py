import uuid

from queueing.producer import publish_document_job
from sqlalchemy.orm import Session
from storage.s3.client import s3_client

from models.entities import DocumentStatus
from repositories.base import DocumentRepository


class DocumentService:
    ALLOWED_TYPES = {"pdf", "docx", "txt"}
    MAX_SIZE = 25 * 1024 * 1024

    def __init__(self, db: Session):
        self.repo = DocumentRepository(db)

    def validate(self, filename: str, content) -> bool:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in self.ALLOWED_TYPES:
            return False
        return content.size <= self.MAX_SIZE

    def upload(self, workspace_id: str, user_id: str, file) -> dict:
        if not self.validate(file.filename, file):
            # Caller maps this to HTTP 415/413.
            raise ValueError("invalid_file")

        s3_key = f"docs/{workspace_id}/{uuid.uuid4()}_{file.filename}"
        s3_client.upload_fileobj(file.file, s3_key)

        doc = self.repo.create(
            workspace_id=workspace_id,
            uploaded_by=user_id,
            filename=s3_key,
            original_name=file.filename,
            file_type=file.filename.rsplit(".", 1)[-1].lower(),
            file_size=file.size,
            s3_key=s3_key,
            status=DocumentStatus.uploading,
        )

        publish_document_job(doc.id, job_type="extract", s3_key=s3_key)
        self.repo.get(doc.id).status = DocumentStatus.processing
        self.repo.db.commit()

        return {"document_id": doc.id, "status": "processing"}

    def list(self, workspace_id: str | None = None):
        return self.repo.get_many(workspace_id)

    def delete(self, document_id: str):
        doc = self.repo.get(document_id)
        if not doc:
            return False
        if doc.s3_key:
            s3_client.delete(doc.s3_key)
        self.repo.db.delete(doc)
        self.repo.db.commit()
        return True
