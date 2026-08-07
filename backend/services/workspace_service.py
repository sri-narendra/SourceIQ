from sqlalchemy.orm import Session

from repositories.base import WorkspaceRepository


class WorkspaceService:
    def __init__(self, db: Session):
        self.repo = WorkspaceRepository(db)

    def create(self, owner_id: str, name: str, description: str | None = None):
        return self.repo.create(owner_id=owner_id, name=name, description=description)

    def list_for_user(self, user_id: str):
        return self.repo.list(owner_id=user_id)

    def with_doc_counts(self, workspaces):
        return [
            {"id": w.id, "name": w.name, "documents": self.repo.count_documents(w.id)}
            for w in workspaces
        ]
