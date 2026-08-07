import logging

from ai.retrieval.retriever import retrieve_chunks
from sqlalchemy.orm import Session

from models.entities import MessageRole
from repositories.base import ConversationRepository, DocumentRepository, MessageRepository

log = logging.getLogger(__name__)


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.convo_repo = ConversationRepository(db)
        self.msg_repo = MessageRepository(db)
        self.doc_repo = DocumentRepository(db)

    def answer(self, workspace_id: str, user_id: str, message: str) -> dict:
        conversation_id = None

        chunks = retrieve_chunks(self.db, workspace_id, message, top_k=4)
        answer, sources = self._generate(workspace_id, message, chunks)

        convo = self.convo_repo.get(conversation_id) if conversation_id else None
        if convo is None:
            convo = self.convo_repo.create(
                workspace_id=workspace_id, user_id=user_id, title=message[:255]
            )

        self.msg_repo.create(conversation_id=convo.id, role=MessageRole.user, content=message)
        self.msg_repo.create(
            conversation_id=convo.id,
            role=MessageRole.assistant,
            content=answer,
            sources=sources,
        )

        return {"answer": answer, "sources": sources, "conversation_id": str(convo.id)}

    def history(self, conversation_id: str) -> list:
        return self.msg_repo.get_by_conversation(conversation_id)

    def _generate(self, workspace_id, question, chunks):
        # Placeholder — wired to ai/generation.generator.generate().
        from ai.generation.generator import format_sources, generate_answer

        context = "\n\n".join(c.content for c in chunks)
        answer = generate_answer(question, context)
        sources = format_sources(chunks)
        return answer, sources
