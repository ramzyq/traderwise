from services.llm.groq import GroqProvider


def test_groq_returns_fallback_without_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    provider = GroqProvider(api_key="")
    reply = provider.generate("sys", "msg")
    assert "Cash Flow" in reply


def test_groq_model_default():
    assert GroqProvider(api_key="k").model == "llama-3.3-70b-versatile"