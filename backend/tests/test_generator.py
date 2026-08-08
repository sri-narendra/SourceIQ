from ai.generation.generator import generate_answer


def test_local_fallback_without_key(monkeypatch):
    monkeypatch.setattr("config.settings.settings.ai_provider", "openai")
    monkeypatch.setattr("config.settings.settings.openai_api_key", "")
    out = generate_answer("what is x?", "context here")
    assert out.startswith("[openai]")
