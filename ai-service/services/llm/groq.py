import os

import requests

from services.llm.base import LLMProvider


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = "llama-3.3-70b-versatile"

    def generate(self, system_prompt: str, user_message: str) -> str:
        if not self.api_key:
            return (
                "Cash Flow: What cash must remain safe this week? "
                "Risk: What could go wrong if this choice delays payment? "
                "Relationships: How can trust stay strong while protecting your business? "
                "Learning: What did last week teach you about this kind of decision"
            )

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 300,
            },
            timeout=20,
        )
        response.raise_for_status()

        payload = response.json()
        choices = payload.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        return ""