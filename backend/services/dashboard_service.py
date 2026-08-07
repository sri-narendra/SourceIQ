from sqlalchemy.orm import Session

from models.entities import Conversation, Document, Workspace
from repositories.base import ConversationRepository, DocumentRepository


class DashboardService:
    def __init__(self, db: Session):
        self.convo_repo = ConversationRepository(db)
        self.doc_repo = DocumentRepository(db)

    def summary(self, user_id: str) -> dict:
        workspaces = self.doc_repo.db.query(Workspace).filter_by(owner_id=user_id).all()
        workspace_count = len(workspaces)

        documents = (
            self.doc_repo.db.query(Document)
            .filter(Document.workspace_id.in_([w.id for w in workspaces]))
            .count()
            if workspaces
            else 0
        )
        conversations = self.convo_repo.db.query(Conversation).filter_by(user_id=user_id).count()
        storage_used_mb = 0  # Sum file_size metadata; placeholder.

        return {
            "documents": documents,
            "conversations": conversations,
            "storage_used_mb": storage_used_mb,
            "workspace_count": workspace_count,
        }
