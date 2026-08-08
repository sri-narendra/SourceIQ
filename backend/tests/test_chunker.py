from ai.chunking.chunker import chunk_text


def test_single_chunk_short_text():
    chunks = chunk_text("hello world", chunk_size=800, overlap=120)
    assert chunks == ["hello world"]


def test_multiple_chunks_overlap():
    text = " ".join(str(i) for i in range(100))
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert len(chunks) >= 5
    # step = chunk_size - overlap = 15
    assert all(len(c.split()) <= 20 for c in chunks)


def test_chunks_reconstruct_all_words():
    text = " ".join(str(i) for i in range(100))
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    all_words = [w for c in chunks for w in c.split()]
    # union preserves every word (may have dupes from overlap)
    assert len(set(all_words)) == 100


def test_zero_overlap():
    text = " ".join(str(i) for i in range(30))
    chunks = chunk_text(text, chunk_size=10, overlap=0)
    assert len(chunks) == 3


def test_empty_text():
    assert chunk_text("") == []
