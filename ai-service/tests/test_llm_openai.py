from services.llm.openai import OpenAIProvider


def test_openai_fallback_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    reply = OpenAIProvider(api_key="").generate("sys", "msg")
    assert "Cash Flow" in reply


def test_openai_model_default():
    assert OpenAIProvider(api_key="k").model == "gpt-4o-mini"