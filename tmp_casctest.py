import sys, os
sys.path.insert(0, "backend")
os.environ["SQS_QUEUE_URL"] = ""
from database.session import SessionLocal
from models.entities import (
    Document, DocumentChunk, Embedding, ProcessingJob,
    DocumentStatus, JobType, JobStatus, Workspace, User,
)
import uuid
db = SessionLocal()
ws_id = db.query(Workspace).first().id
usr_id = db.query(User).first().id
doc_id = uuid.uuid4()
d = Document(id=doc_id, workspace_id=ws_id, uploaded_by=usr_id,
             filename="t.pdf", original_name="t.pdf", file_type="pdf",
             file_size=1, status=DocumentStatus.completed)
db.add(d); db.flush()
c = DocumentChunk(document_id=doc_id, chunk_number=0, content="x",
                  token_count=1, page_number=1)
db.add(c); db.flush()
db.add(Embedding(chunk_id=c.id, embedding=[0.0]*1536, model="test"))
db.add(ProcessingJob(document_id=doc_id, job_type=JobType.embed,
                     status=JobStatus.completed))
db.commit()

db.query(ProcessingJob).filter_by(document_id=doc_id).delete()
db.delete(d)
db.commit()
left = dict(
    chunks=db.query(DocumentChunk).filter_by(document_id=doc_id).count(),
    embeds=db.query(Embedding).join(DocumentChunk,
        DocumentChunk.id == Embedding.chunk_id).filter(
        DocumentChunk.document_id == doc_id).count(),
    jobs=db.query(ProcessingJob).filter_by(document_id=doc_id).count(),
    doc=db.query(Document).filter_by(id=doc_id).count(),
)
print("after delete:", left)
assert left == {"chunks": 0, "embeds": 0, "jobs": 0, "doc": 0}, left
print("CASCADE TEST PASS")
db.close()