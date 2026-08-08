"""Document processing worker: download -> extract -> chunk -> embed -> store.

Run standalone:  python -m workers.document_worker.main
"""
import json
import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("document_worker")


def process_document(document_id: str, s3_key: str):
    """Ingest one document end-to-end: download -> extract -> chunk -> embed -> store.

    Called both by the SQS worker (process_message) and, when no queue is
    configured, directly from the upload path for local-dev RAG.
    """
    log.info("Processing document %s (%s)", document_id, s3_key)

    from database.session import SessionLocal
    from models.entities import (
        Document,
        DocumentChunk,
        DocumentStatus,
        Embedding,
        ProcessingJob,
        JobType,
        JobStatus,
    )
    from storage.s3.client import s3_client
    from ai.chunking.text_extractor import extract_pages
    from ai.chunking.chunker import chunk_text
    from ai.embeddings.provider import embed_texts
    from config.settings import settings

    db = SessionLocal()
    try:
        doc = db.query(Document).filter_by(id=document_id).first()
        if not doc:
            log.warning("Document %s not found", document_id)
            return

        data = s3_client.download(s3_key)
        page_blocks = extract_pages(doc.original_name, data)

        pieces = []
        chunk_pages = []
        for page_text, page_number in page_blocks:
            if not page_text.strip():
                continue
            for piece in chunk_text(page_text):
                pieces.append(piece)
                chunk_pages.append(page_number)

        vectors = embed_texts(pieces)

        job = db.query(ProcessingJob).filter_by(document_id=doc.id, job_type=JobType.embed).first()
        if not job:
            job = ProcessingJob(document_id=doc.id, job_type=JobType.embed)
            db.add(job)

        for i, (piece, vec) in enumerate(zip(pieces, vectors)):
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_number=i,
                content=piece,
                token_count=len(piece.split()),
                page_number=chunk_pages[i],
            )
            db.add(chunk)
            db.flush()
            db.add(
                Embedding(
                    chunk_id=chunk.id,
                    embedding=vec,
                    model=settings.embedding_model,
                )
            )

        doc.status = DocumentStatus.completed
        job.status = JobStatus.completed
        db.commit()
        log.info("Document %s done: %d chunks", document_id, len(pieces))
    except Exception as exc:
        db.rollback()
        doc = db.query(Document).filter_by(id=document_id).first()
        if doc:
            doc.status = DocumentStatus.failed
        job = db.query(ProcessingJob).filter_by(document_id=document_id, job_type=JobType.embed).first()
        if job:
            job.status = JobStatus.failed
            job.error_message = str(exc)
        db.commit()
        log.exception("Failed to process %s", document_id)
    finally:
        db.close()


def process_message(message):
    body = json.loads(message["Body"])
    process_document(body["document_id"], body.get("s3_key"))


def run(once: bool = False):
    from queueing.producer import delete_message, receive_document_jobs

    while True:
        messages = receive_document_jobs()
        for m in messages:
            process_message(m)
            delete_message(m["ReceiptHandle"])
        if once:
            break
        time.sleep(1)


if __name__ == "__main__":
    run(once="--once" in sys.argv)