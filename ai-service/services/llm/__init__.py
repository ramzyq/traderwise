import os

from services.llm.base import LLMProvider
from services.llm.claude import ClaudeProvider
from services.llm.groq import GroqProvider
from services.llm.openai import OpenAIProvider

_PROVIDERS = {
    "groq": GroqProvider,
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
}


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    name = provider_name or os.getenv("LLM_PROVIDER", "groq")
    provider_cls = _PROVIDERS.get(name, GroqProvider)
    return provider_cls()


provider = get_llm_provider()