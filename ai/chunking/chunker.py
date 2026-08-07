def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """Split text into overlapping chunks by token-ish length.

    ponytail: char-based approximation of tokens; swap for a real tokenizer (tiktoken/test) when needed.
    """
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        if not chunks and start > 0:
            break
        piece = words[start : start + chunk_size]
        if piece:
            chunks.append(" ".join(piece))
    return chunks