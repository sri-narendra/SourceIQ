from sqlalchemy.orm import Session

from ai.embeddings.provider import embed_query
from models.entities import DocumentChunk, Embedding


def _cosine(a: list[float], b: list[float]) -> float:
    dots = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dots / ((na * nb) or 1.0)


def retrieve_chunks(db: Session, workspace_id: str, query: str, top_k: int = 5) -> list:
    """Brute-force cosine over the workspace's embeddings.

    ponytail: linear scan; swap for a pgvector HNSW index when document counts grow.
    """
    q = embed_query(query)

    rows = (
        db.query(Embedding, DocumentChunk)
        .join(DocumentChunk, Embedding.chunk_id == DocumentChunk.id)
        .join(DocumentChunk.document)
        .filter(DocumentChunk.document.has(workspace_id=workspace_id))
        .all()
    )

    scored = []
    for emb, chunk in rows:
        if emb.embedding is None:
            continue
        score = _cosine(q, list(emb.embedding))
        # np.float32 is not JSON-serializable for the sources column.
        chunk._score = float(score)  # noqa: SLF001
        scored.append((score, chunk))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [c for _, c in scored[:top_k]]