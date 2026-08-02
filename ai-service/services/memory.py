from threading import Lock

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class MemoryStore:
    def __init__(self) -> None:
        self._store: dict[str, list[Message]] = {}
        self._lock = Lock()

    def get(self, user_id: str) -> list[Message]:
        with self._lock:
            return list(self._store.get(user_id, []))

    def save(self, user_id: str, history: list[Message]) -> None:
        with self._lock:
            truncated = history[-20:] if len(history) > 20 else history
            self._store[user_id] = list(truncated)

    def clear(self, user_id: str) -> None:
        with self._lock:
            self._store.pop(user_id, None)


memory = MemoryStore()