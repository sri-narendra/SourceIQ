RAG_SYSTEM = (
    "You are a helpful assistant answering questions strictly from the provided "
    "documents. Use the context only. Never invent facts. Cite the source document "
    "and page for each claim. If the context does not contain the answer, say so."
)


def build_prompt(question: str, context: str) -> str:
    return f"{RAG_SYSTEM}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"