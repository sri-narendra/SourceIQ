"""Re-embed verification worker: regenerate embeddings for failed/missing chunks.

Run standalone:  python -m workers.embedding_worker.main
"""


def run():
    from database.session import SessionLocal
    from models.entities import DocumentChunk, DocumentStatus, Embedding
    from ai.embeddings.provider import embed_texts
    from config.settings import settings

    db = SessionLocal()
    try:
        # Chunks created by a failed job have no embedding row yet.
        missing = (
            db.query(DocumentChunk)
            .outerjoin(Embedding, Embedding.chunk_id == DocumentChunk.id)
            .filter(Embedding.id.is_(None))
            .all()
        )
        for chunk in missing:
            [vec] = embed_texts([chunk.content])
            db.add(
                Embedding(
                    chunk_id=chunk.id,
                    embedding=vec,
                    model=settings.embedding_model,
                )
            )
            doc = chunk.document
            if doc and doc.status == DocumentStatus.failed:
                doc.status = DocumentStatus.completed
        db.commit()
        print(f"Re-embedded {len(missing)} chunks")
    finally:
        db.close()


if __name__ == "__main__":
    run()