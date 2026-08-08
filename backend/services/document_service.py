import json
import logging
import uuid
from threading import Thread
from urllib.request import Request, urlopen

from queueing.producer import publish_document_job
from sqlalchemy.orm import Session
from storage.s3.client import s3_client

from config.settings import settings
from models.entities import DocumentStatus
from repositories.base import DocumentRepository

log = logging.getLogger("document_service")


def _dispatch_worker():
    if not settings.github_token:
        return  # no token configured — rely on the 5-min cron
    body = json.dumps({"ref": "master"}).encode()
    req = Request(
        f"https://api.github.com/repos/{settings.github_repo}/actions/workflows/"
        f"{settings.github_workflow}/dispatches",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(req, timeout=10):
            pass
        log.info("Kicked worker dispatch (workflow_dispatch)")
    except Exception as exc:  # never block an upload over GitHub
        log.warning("Worker dispatch failed; cron will catch it: %s", exc)


def _process_background(document_id, s3_key):
    from workers.document_worker.main import process_document

    process_document(document_id, s3_key)


class DocumentService:
    ALLOWED_TYPES = set(settings.allowed_file_types.split(","))
    MAX_SIZE = settings.max_file_size_mb * 1024 * 1024

    def __init__(self, db: Session):
        self.repo = DocumentRepository(db)

    def validate(self, filename: str, data: bytes) -> bool:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return ext in self.ALLOWED_TYPES

    def upload(self, workspace_id: str, user_id: str, file) -> dict:
        data = file.file.read()
        file.file.seek(0)
        if not self.validate(file.filename, data):
            # Caller maps this to HTTP 415/413.
            raise ValueError("invalid_type")
        if len(data) > self.MAX_SIZE:
            raise ValueError("too_large")

        s3_key = f"docs/{workspace_id}/{uuid.uuid4()}_{file.filename}"
        s3_client.upload_fileobj(file.file, s3_key)

        doc = self.repo.create(
            workspace_id=workspace_id,
            uploaded_by=user_id,
            filename=s3_key,
            original_name=file.filename,
            file_type=file.filename.rsplit(".", 1)[-1].lower(),
            file_size=len(data),
            s3_key=s3_key,
            status=DocumentStatus.uploading,
        )

        publish_document_job(doc.id, job_type="extract", s3_key=s3_key)
        Thread(target=_dispatch_worker, daemon=True).start()
        self.repo.get(doc.id).status = DocumentStatus.processing
        self.repo.db.commit()

        if not settings.sqs_queue_url:
            # ponytail: local dev with no SQS — process inline in a background
            # thread; a real queue+worker is the scale-up path.
            Thread(
                target=_process_background,
                args=(str(doc.id), s3_key),
                daemon=True,
            ).start()

        return {"document_id": doc.id, "status": "processing"}

    def get(self, document_id: str):
        return self.repo.get(document_id)

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
