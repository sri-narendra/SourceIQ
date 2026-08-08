"""Embedding provider implementations. Each implements embed_batch() and embed()."""


class GeminiEmbedder:
    def __init__(self):
        from config.settings import settings

        self.model = settings.embedding_model

    def _client(self):
        import google.generativeai as genai

        from config.settings import settings

        genai.configure(api_key=settings.gemini_api_key)
        return genai

    def embed(self, texts: list[str]) -> list[list[float]]:
        genai = self._client()
        if self.model == "text-embedding-004":
            # text-embedding-004 defaults to 768 dims; the embeddings table is Vector(1536).
            # gemini accepts output_dimensionality for this model, so pin it to match the schema.
            result = genai.embed_content(
                model=self.model, content=texts, output_dimensionality=1536
            )
        else:
            result = genai.embed_content(model=self.model, content=texts)
        return [list(v) for v in result["embedding"]]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self.embed(texts)


class OpenAIEmbedder:
    def __init__(self):
        from config.settings import settings

        # settings.embedding_model defaults to gemini's text-embedding-004, which is not
        # an OpenAI model; fall back to an OpenAI-native 1536-dim model so dims match.
        self.model = (
            "text-embedding-3-small"
            if settings.embedding_model == "text-embedding-004" or not settings.embedding_model
            else settings.embedding_model
        )

    def _client(self):
        import openai

        from config.settings import settings

        return openai.OpenAI(api_key=settings.openai_api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        client = self._client()
        resp = client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self.embed(texts)


class LocalEmbedder:
    """Fallback deterministic vectorizer so dev works without an API key."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_vec(t) for t in texts]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self.embed(texts)


def _hash_vec(text: str, dim: int = 1536) -> list[float]:
    import hashlib

    vec = [0.0] * dim
    for token in text.lower().split():
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = (sum(v * v for v in vec) ** 0.5) or 1.0
    return [v / norm for v in vec]