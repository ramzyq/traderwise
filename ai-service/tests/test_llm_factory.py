from services.llm.groq import GroqProvider
from services.llm.claude import ClaudeProvider
from services.llm.openai import OpenAIProvider
from services.llm import get_llm_provider


def test_default_is_groq(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert isinstance(get_llm_provider(), GroqProvider)


def test_explicit_groq():
    assert isinstance(get_llm_provider("groq"), GroqProvider)


def test_claude():
    assert isinstance(get_llm_provider("claude"), ClaudeProvider)


def test_openai():
    assert isinstance(get_llm_provider("openai"), OpenAIProvider)


def test_unknown_defaults_to_groq():
    assert isinstance(get_llm_provider("whatever"), GroqProvider)