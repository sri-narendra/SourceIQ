from sqlalchemy.orm import Session

from models.entities import (
    Conversation,
    Document,
    DocumentChunk,
    Embedding,
    Message,
    ProcessingJob,
    WorkspaceMember,
)
from repositories.base import WorkspaceRepository


class WorkspaceService:
    def __init__(self, db: Session):
        self.repo = WorkspaceRepository(db)
        self.db = db

    def create(self, owner_id: str, name: str, description: str | None = None):
        return self.repo.create(owner_id=owner_id, name=name, description=description)

    def list_for_user(self, user_id: str):
        return self.repo.list(owner_id=user_id)

    def get_for_user(self, workspace_id: str, user_id: str):
        return self.repo.get_for_user(workspace_id, user_id)

    def with_doc_counts(self, workspaces):
        return [
            {"id": w.id, "name": w.name, "documents": self.repo.count_documents(w.id)}
            for w in workspaces
        ]

    def delete(self, workspace_id: str) -> bool:
        ws = self.repo.get(workspace_id)
        if not ws:
            return False
        doc_ids = [d.id for d in self.db.query(Document).filter_by(workspace_id=workspace_id)]
        chunk_ids = [
            c.id
            for c in self.db.query(DocumentChunk).filter(DocumentChunk.document_id.in_(doc_ids))
        ]
        if chunk_ids:
            self.db.query(Embedding).filter(Embedding.chunk_id.in_(chunk_ids)).delete(
                synchronize_session=False
            )
            self.db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).delete(
                synchronize_session=False
            )
        if doc_ids:
            self.db.query(ProcessingJob).filter(ProcessingJob.document_id.in_(doc_ids)).delete(
                synchronize_session=False
            )
            self.db.query(Document).filter(Document.id.in_(doc_ids)).delete(
                synchronize_session=False
            )
        convo_ids = [
            c.id for c in self.db.query(Conversation).filter_by(workspace_id=workspace_id)
        ]
        if convo_ids:
            self.db.query(Message).filter(Message.conversation_id.in_(convo_ids)).delete(
                synchronize_session=False
            )
            self.db.query(Conversation).filter(Conversation.id.in_(convo_ids)).delete(
                synchronize_session=False
            )
        self.db.query(WorkspaceMember).filter_by(workspace_id=workspace_id).delete(
            synchronize_session=False
        )
        self.db.delete(ws)
        self.db.commit()
        return True
