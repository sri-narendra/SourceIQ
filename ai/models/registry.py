from dataclasses import dataclass


@dataclass
class LLMModel:
    """A language-model provider, selectable by name."""

    provider: str
    model_id: str
    base_url: str | None = None


def resolve_llm(provider: str | None = None, model: str | None = None) -> LLMModel:
    from config.settings import settings

    p = (provider or settings.ai_provider).lower()
    if p == "gemini":
        return LLMModel("gemini", model or "gemini-1.5-pro")
    if p == "groq":
        return LLMModel("groq", model or "llama-3.1-8b-instant")
    if p == "openai":
        return LLMModel("openai", model or "gpt-4o-mini")
    if p == "vllm":
        return LLMModel("vllm", model or "meta-llama/Meta-Llama-3-8B-Instruct", settings.vllm_base_url)
    if p == "ollama":
        return LLMModel("ollama", model or "llama3", settings.ollama_base_url)
    raise ValueError(f"Unsupported AI provider: {p}")


def build_embeddings(docs_metadata: None = None):
    """Prepare the embedding config (dimension 1536) used across the pipeline."""
    from config.settings import settings

    return {"model": settings.embedding_model, "dim": 1536}