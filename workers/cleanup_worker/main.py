"""Cleanup worker: expire temporary uploads and failed documents (runs daily).

Run standalone:  python -m workers.cleanup_worker.main
"""


def run():
    from database.session import SessionLocal
    from models.entities import Document, DocumentStatus
    from storage.s3.client import s3_client

    db = SessionLocal()
    try:
        failed = db.query(Document).filter(Document.status == DocumentStatus.failed).all()
        for doc in failed:
            if doc.s3_key:
                try:
                    s3_client.delete(doc.s3_key)
                except Exception:
                    pass  # already gone
            db.delete(doc)
        db.commit()
        print(f"Cleaned {len(failed)} failed documents")
    finally:
        db.close()


if __name__ == "__main__":
    run()