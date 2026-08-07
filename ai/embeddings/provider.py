def get_embedder():
    from config.settings import settings

    provider = settings.ai_provider
    # Only use a remote embedder when a matching API key is configured; else fall back to local.
    if provider == "gemini" and settings.gemini_api_key:
        from ai.embeddings.providers import GeminiEmbedder

        return GeminiEmbedder()
    if provider == "openai" and settings.openai_api_key:
        from ai.embeddings.providers import OpenAIEmbedder

        return OpenAIEmbedder()
    from ai.embeddings.providers import LocalEmbedder

    return LocalEmbedder()


def embed_texts(texts: list[str]) -> list[list[float]]:
    return get_embedder().embed_batch(texts)


def embed_query(query: str) -> list[float]:
    return get_embedder().embed([query])[0]