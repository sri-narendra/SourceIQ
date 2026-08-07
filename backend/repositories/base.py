from typing import List, Optional, TypeVar

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.entities import (
    Conversation,
    Document,
    DocumentChunk,
    Message,
    ProcessingJob,
    UsageStatistic,
    User,
    Workspace,
)

ModelT = TypeVar("ModelT")


class BaseRepository:
    model = None

    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs):
        obj = self.model(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, id):
        return self.db.query(self.model).filter(self.model.id == id).first()

    def list(self, **filters) -> List:
        query = self.db.query(self.model)
        for k, v in filters.items():
            if v is not None:
                query = query.filter(getattr(self.model, k) == v)
        return query.all()


class UserRepository(BaseRepository):
    model = User

    def get_by_email(self, email: str):
        return self.db.query(self.model).filter(self.model.email == email).first()


class WorkspaceRepository(BaseRepository):
    model = Workspace

    def count_documents(self, workspace_id) -> int:
        return (
            self.db.query(func.count())
            .select_from(Document)
            .filter(Document.workspace_id == workspace_id)
            .scalar()
            or 0
        )


class DocumentRepository(BaseRepository):
    model = Document

    def get_many(self, workspace_id: Optional[str] = None):
        query = self.db.query(self.model)
        if workspace_id:
            query = query.filter(self.model.workspace_id == workspace_id)
        return query.all()


class ConversationRepository(BaseRepository):
    model = Conversation


class MessageRepository(BaseRepository):
    model = Message

    def get_by_conversation(self, conversation_id):
        return (
            self.db.query(self.model)
            .filter(self.model.conversation_id == conversation_id)
            .order_by(self.model.created_at)
            .all()
        )


class ChunkRepository(BaseRepository):
    model = DocumentChunk


class JobRepository(BaseRepository):
    model = ProcessingJob


class UsageRepository(BaseRepository):
    model = UsageStatistic
