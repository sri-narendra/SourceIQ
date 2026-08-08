"""Service-level tests for chat, search, retrieval with a real DB.

These exercise the actual business flow (embed -> store -> retrieve -> answer)
against Postgres + pgvector.
"""
import pytest

from config.settings import settings


@pytest.fixture()
def clean_db(db):
    return db


def _seed_workspace_doc(db):
    from models.entities import Document, User, Workspace
    from services.auth_service import hash_password

    user = User(name="u", email="svc@u.com", password_hash=hash_password("x"))
    db.add(user)
    db.commit()
    ws = Workspace(owner_id=user.id, name="ws", description="")
    db.add(ws)
    db.commit()

    doc = Document(
        workspace_id=ws.id,
        uploaded_by=user.id,
        filename="docs/1.txt",
        original_name="1.txt",
        file_type="txt",
        file_size=100,
        status="completed",
    )
    db.add(doc)
    db.commit()
    return user, ws, doc


def seed_chunk(db, doc, text):
    from ai.embeddings.provider import embed_texts

    from models.entities import DocumentChunk, Embedding

    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_number=1,
        page_number=1,
        content=text,
        token_count=len(text.split()),
    )
    db.add(chunk)
    db.commit()
    vec = embed_texts([text])[0]
    emb = Embedding(chunk_id=chunk.id, embedding=vec, model=settings.embedding_model)
    db.add(emb)
    db.commit()
    return chunk


def test_retriever_returns_most_relevant(clean_db):
    from ai.retrieval.retriever import retrieve_chunks

    _, ws, doc = _seed_workspace_doc(clean_db)
    seed_chunk(clean_db, doc, "The cat sat on the warm mat.")
    seed_chunk(clean_db, doc, "Quantum chromodynamics explains quarks and gluons.")

    results = retrieve_chunks(clean_db, str(ws.id), "what is quantum chromodynamics?", top_k=2)
    assert len(results) == 2
    assert results[0].content == "Quantum chromodynamics explains quarks and gluons."


def test_search_service_payload(clean_db):
    _, ws, doc = _seed_workspace_doc(clean_db)
    seed_chunk(clean_db, doc, "The sky is blue.")
    from services.search_service import SearchService

    out = SearchService(clean_db).semantic_search(str(ws.id), "color of sky", top_k=1)
    assert out[0]["text"] == "The sky is blue."
    assert "score" in out[0]
    assert out[0]["document"] == "1.txt"


def test_embedder_model_resolution(monkeypatch):
    from ai.embeddings.provider import get_embedder
    from ai.embeddings.providers import GeminiEmbedder, LocalEmbedder, OpenAIEmbedder

    # openai with key + default gemini model name -> OpenAI-native model
    monkeypatch.setattr("config.settings.settings.ai_provider", "openai")
    monkeypatch.setattr("config.settings.settings.openai_api_key", "k")
    monkeypatch.setattr("config.settings.settings.embedding_model", "text-embedding-004")
    ed = OpenAIEmbedder()
    assert ed.model != "text-embedding-004"  # never send a gemini model id to openai
    assert ed.model == "text-embedding-3-small"  # 1536-dim

    # no key -> local fallback still 1536
    monkeypatch.setattr("config.settings.settings.openai_api_key", "")
    assert isinstance(get_embedder(), LocalEmbedder)
    assert isinstance(GeminiEmbedder(), GeminiEmbedder)


def test_chat_service_persists_conversation_and_messages(clean_db, monkeypatch):
    user, ws, doc = _seed_workspace_doc(clean_db)
    seed_chunk(clean_db, doc, "RAG pipelines answer from retrieved documents.")

    monkeypatch.setattr("config.settings.settings.ai_provider", "openai")
    monkeypatch.setattr("config.settings.settings.openai_api_key", "")

    from services.chat_service import ChatService

    out = ChatService(clean_db).answer(str(ws.id), str(user.id), "how do rag pipelines work?")
    assert out["conversation_id"]
    assert out["answer"]
    assert "conversation_id" in out

    from models.entities import Message
    msgs = clean_db.query(Message).filter(Message.conversation_id == out["conversation_id"]).all()
    assert len(msgs) == 2  # user + assistant
    assert msgs[0].role.value == "user"
    assert msgs[1].role.value == "assistant"


def test_chat_service_reuses_conversation_when_id_passed(clean_db, monkeypatch):
    user, ws, doc = _seed_workspace_doc(clean_db)
    seed_chunk(clean_db, doc, "RAG pipelines answer from retrieved documents.")

    monkeypatch.setattr("config.settings.settings.ai_provider", "openai")
    monkeypatch.setattr("config.settings.settings.openai_api_key", "")

    from services.chat_service import ChatService

    svc = ChatService(clean_db)
    first = svc.answer(str(ws.id), str(user.id), "what is rag?")
    second = svc.answer(
        str(ws.id), str(user.id), "elaborate", conversation_id=first["conversation_id"] or None
    )

    assert second["conversation_id"] == first["conversation_id"]

    from models.entities import Message

    msgs = (
        clean_db.query(Message)
        .filter(Message.conversation_id == first["conversation_id"])
        .order_by(Message.created_at)
        .all()
    )
    assert len(msgs) == 4  # both turns persist into the same conversation
