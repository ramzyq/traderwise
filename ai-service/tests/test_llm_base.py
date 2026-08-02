import pytest

from services.llm.base import LLMProvider


def test_llm_provider_is_abstract():
    with pytest.raises(TypeError):
        LLMProvider()


def test_subclass_implements_generate():
    class FakeProvider(LLMProvider):
        def generate(self, system_prompt, user_message):
            return "reply"

    assert FakeProvider().generate("sys", "msg") == "reply"