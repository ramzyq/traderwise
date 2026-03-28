import os

import requests


class ClaudeClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = "claude-sonnet-4-6"

    def generate(self, system_prompt: str, user_message: str) -> str:
        if not self.api_key:
            return (
                "Cash Flow: What cash must remain safe this week? "
                "Risk: What could go wrong if this choice delays payment? "
                "Relationships: How can trust stay strong while protecting your business? "
                "Learning: What did last week teach you about this kind of decision"
            )

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": self.model,
                "max_tokens": 300,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}]
            },
            timeout=20
        )
        response.raise_for_status()

        payload = response.json()
        content = payload.get("content", [])
        if content and isinstance(content, list):
            first = content[0]
            if isinstance(first, dict):
                return first.get("text", "").strip()

        return ""
