from services.llm.claude import ClaudeProvider


def test_claude_fallback_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    reply = ClaudeProvider(api_key="").generate("sys", "msg")
    assert "Cash Flow" in reply


def test_claude_model_default():
    assert ClaudeProvider(api_key="k").model == "claude-sonnet-4-6"