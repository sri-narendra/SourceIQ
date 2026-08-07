def test_health():
    from main import app

    assert any(getattr(r, "path", "") == "/api/v1/health" for r in app.routes)


def test_chunker_roundtrip():
    from ai.chunking.chunker import chunk_text

    text = "word " * 600
    chunks = chunk_text(text, chunk_size=200, overlap=20)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 200 for c in chunks)


def test_local_embedder_dims():
    from ai.embeddings.provider import get_embedder

    embedder = get_embedder()
    vec = embedder.embed("hello world")
    assert len(vec) > 0
