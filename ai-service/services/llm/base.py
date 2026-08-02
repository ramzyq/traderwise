from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Return the model's reply to user_message with the given system prompt."""
        raise NotImplementedError