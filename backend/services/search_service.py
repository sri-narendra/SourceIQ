from ai.retrieval.retriever import retrieve_chunks
from sqlalchemy.orm import Session


class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def semantic_search(self, workspace_id: str, query: str, top_k: int = 5) -> list:
        chunks = retrieve_chunks(self.db, workspace_id, query, top_k=top_k)
        return [
            {
                "document": chunk.document.original_name,
                "page": chunk.page_number,
                "text": chunk.content,
                "score": getattr(chunk, "_score", 0.0),
            }
            for chunk in chunks
        ]
