from ai.models.registry import resolve_llm
from ai.prompts.prompts import build_prompt


def generate_answer(question: str, context: str, provider: str | None = None) -> str:
    """Streaming-agnostic single-shot answer. Providers return complete text.

    ponytail: server-side generic call; true token streaming is wired at the API layer (<SSE>).
    """
    from config.settings import settings

    llm = resolve_llm(provider)
    prompt = build_prompt(question, context)

    key_ok = {
        "gemini": settings.gemini_api_key,
        "groq": settings.groq_api_key,
        "openai": settings.openai_api_key,
        "mistral": settings.mistral_api_key,
        "nvidia": settings.nvidia_api_key,
        "openrouter": settings.openrouter_api_key,
    }.get(llm.provider)
    if llm.provider in ("vllm", "ollama") and not llm.base_url:
        return _local(llm, prompt)
    if not key_ok:
        return _local(llm, prompt)

    if llm.provider == "gemini":
        return _gemini(llm, prompt)
    if llm.provider == "groq":
        return _groq(llm, prompt)
    if llm.provider in ("openai", "mistral", "nvidia", "openrouter"):
        return _openai_compatible(llm, prompt)
    return _local(llm, prompt)


def format_sources(chunks) -> list[dict]:
    from ai.retrieval.sources import format_sources as _fs

    return _fs(chunks)


def _gemini(llm, prompt):
    import google.generativeai as genai

    from config.settings import settings

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(llm.model_id)
    return model.generate_content(prompt).text


def _groq(llm, prompt):
    from config.settings import settings

    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    resp = client.chat.completions.create(
        model=llm.model_id,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _openai_compatible(llm, prompt):
    from config.settings import settings

    import openai

    key = {
        "openai": settings.openai_api_key,
        "mistral": settings.mistral_api_key,
        "nvidia": settings.nvidia_api_key,
        "openrouter": settings.openrouter_api_key,
    }[llm.provider]
    client = openai.OpenAI(api_key=key, base_url=llm.base_url)
    resp = client.chat.completions.create(
        model=llm.model_id,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _local(llm, prompt):
    # Deterministic fallback for local dev / tests without an API key.
    last_line = prompt.splitlines()[-1]
    return f"[{llm.provider}] Grounded response for: {last_line}"