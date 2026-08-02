# Pluggable LLM Provider (Groq Default) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hard-coded `ClaudeClient` with a pluggable `LLMProvider` abstraction, defaulting to Groq (`llama-3.3-70b-versatile`) at zero cost, swappable to `claude` or `openai` via an environment variable.

**Architecture:** An abstract `LLMProvider` base class defines `generate(system_prompt, user_message) -> str`. Three concrete providers (`GroqProvider`, `ClaudeProvider`, `OpenAIProvider`) implement it. A factory `get_llm_provider()` reads `LLM_PROVIDER` and returns the right instance. The existing `ChatPipeline` is updated to use the factory instead of instantiating `ClaudeClient` directly.

**Tech Stack:** Python 3.11+, `requests`, `pytest`, Groq Cloud API.

## Global Constraints

- Provider selection is controlled by env var `LLM_PROVIDER`, values: `groq` (default), `claude`, `openai`.
- Groq model: `llama-3.3-70b-versatile`. Endpoint: `https://api.groq.com/openai/v1/chat/completions`.
- Claude model: `claude-sonnet-4-6`. Endpoint: `https://api.anthropic.com/v1/messages`.
- OpenAI model: `gpt-4o-mini`. Endpoint: `https://api.openai.com/v1/chat/completions`.
- No API key configured → provider returns a safe fallback string (no crash).
- `ChatPipeline` must not import provider subclasses directly; it consumes the abstract interface only.

---

### Task 1: Add pytest and project test configuration

**Files:**
- Modify: `ai-service/requirements.txt`
- Create: `ai-service/pytest.ini`
- Create: `ai-service/tests/__init__.py`

**Interfaces:**
- Consumes: nothing.
- Produces: a runnable `pytest` harness used by every later task.

- [ ] **Step 1: Add pytest to requirements**

Append to `ai-service/requirements.txt`:

```
pytest==8.3.5
```

- [ ] **Step 2: Create pytest.ini**

Create `ai-service/pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .
```

- [ ] **Step 3: Create tests package**

Create `ai-service/tests/__init__.py` as an empty file.

- [ ] **Step 4: Verify pytest runs**

Run: `cd ai-service && python -m pytest`
Expected: "no tests ran" and exit code 0 (or 5). Confirm the harness collects without errors.

- [ ] **Step 5: Commit**

```bash
git add ai-service/requirements.txt ai-service/pytest.ini ai-service/tests/__init__.py
git commit -m "test: add pytest harness to ai-service"
```

---

### Task 2: Implement the `LLMProvider` abstract base class

**Files:**
- Create: `ai-service/services/llm/base.py`
- Test: `ai-service/tests/test_llm_base.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `from services.llm.base import LLMProvider` — abstract class with method `generate(self, system_prompt: str, user_message: str) -> str`.

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_llm_base.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service && python -m pytest tests/test_llm_base.py -v`
Expected: FAIL — import error, `services.llm.base` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `ai-service/services/llm/base.py`:

```python
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Return the model's reply to user_message with the given system prompt."""
        raise NotImplementedError
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai-service && python -m pytest tests/test_llm_base.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add ai-service/services/llm/base.py ai-service/tests/test_llm_base.py
git commit -m "feat(llm): add abstract LLMProvider base class"
```

---

### Task 3: Implement GroqProvider

**Files:**
- Create: `ai-service/services/llm/groq.py`
- Test: `ai-service/tests/test_llm_groq.py`

**Interfaces:**
- Consumes: `LLMProvider` from `services.llm.base`.
- Produces: `class GroqProvider(LLMProvider)` with `__init__(self, api_key: str | None = None)` and `generate(self, system_prompt: str, user_message: str) -> str`. Reads `GROQ_API_KEY` from env when `api_key` is None.

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_llm_groq.py`:

```python
from services.llm.groq import GroqProvider


def test_groq_returns_fallback_without_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    provider = GroqProvider(api_key="")
    reply = provider.generate("sys", "msg")
    assert "Cash Flow" in reply


def test_groq_model_default():
    assert GroqProvider(api_key="k").model == "llama-3.3-70b-versatile"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service && python -m pytest tests/test_llm_groq.py -v`
Expected: FAIL — import error, module does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `ai-service/services/llm/groq.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai-service && python -m pytest tests/test_llm_groq.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add ai-service/services/llm/groq.py ai-service/tests/test_llm_groq.py
git commit -m "feat(llm): add Groq provider (default)"
```

---

### Task 4: Implement Claude provider

**Files:**
- Create: `ai-service/services/llm/claude.py`
- Test: `ai-service/tests/test_llm_claude.py`

**Interfaces:**
- Consumes: `LLMProvider` from `services.llm.base`.
- Produces: `class ClaudeProvider(LLMProvider)` with `__init__(self, api_key: str | None = None)` and the same `generate` signature. Preserves existing Anthropic wire format.

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_llm_claude.py`:

```python
from services.llm.claude import ClaudeProvider


def test_claude_fallback_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    reply = ClaudeProvider(api_key="").generate("sys", "msg")
    assert "Cash Flow" in reply


def test_claude_model_default():
    assert ClaudeProvider(api_key="k").model == "claude-sonnet-4-6"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service && python -m pytest tests/test_llm_claude.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `ai-service/services/llm/claude.py`:

```python
import os

import requests

from services.llm.base import LLMProvider


class ClaudeProvider(LLMProvider):
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
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 300,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            },
            timeout=20,
        )
        response.raise_for_status()

        content = response.json().get("content", [])
        if content and isinstance(content[0], dict):
            return content[0].get("text", "").strip()
        return ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai-service && python -m pytest tests/test_llm_claude.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add ai-service/services/llm/claude.py ai-service/tests/test_llm_claude.py
git commit -m "feat(llm): add Claude provider"
```

---

### Task 5: Add OpenAI provider

**Files:**
- Create: `ai-service/services/llm/openai.py`
- Test: `ai-service/tests/test_llm_openai.py`

**Interfaces:**
- Consumes: `LLMProvider` from `services.llm.base`.
- Produces: `class OpenAIProvider(LLMProvider)` with `__init__(self, api_key: str | None = None)` and the same `generate` signature.

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_llm_openai.py`:

```python
from services.llm.openai import OpenAIProvider


def test_openai_fallback_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    reply = OpenAIProvider(api_key="").generate("sys", "msg")
    assert "Cash Flow" in reply


def test_openai_model_default():
    assert OpenAIProvider(api_key="k").model == "gpt-4o-mini"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service && python -m pytest tests/test_llm_openai.py -v`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `ai-service/services/llm/openai.py`:

```python
import os

import requests

from services.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = "gpt-4o-mini"

    def generate(self, system_prompt: str, user_message: str) -> str:
        if not self.api_key:
            return (
                "Cash Flow: What cash must remain safe this week? "
                "Risk: What could go wrong if this choice delays payment? "
                "Relationships: How can trust stay strong while protecting your business? "
                "Learning: What did last week teach you about this kind of decision"
            )

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
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

        choices = response.json().get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        return ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ai-service && python -m pytest tests/test_llm_openai.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add ai-service/services/llm/openai.py ai-service/tests/test_llm_openai.py
git commit -m "feat(llm): add OpenAI provider"
```

---

### Task 6: Add factory and wire into ChatPipeline

**Files:**
- Create: `ai-service/services/llm/__init__.py`
- Modify: `ai-service/services/chat_pipeline.py:1-15`
- Test: `ai-service/tests/test_llm_factory.py`

**Interfaces:**
- Consumes: `GroqProvider`, `ClaudeProvider`, `OpenAIProvider` from their modules.
- Produces: `get_llm_provider(provider_name: str | None = None) -> LLMProvider` factory and a module-level `provider` instance exported from `services.llm`.

- [ ] **Step 1: Write the failing test**

Create `ai-service/tests/test_llm_factory.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ai-service && python -m pytest tests/test_llm_factory.py -v`
Expected: FAIL — `services.llm.get_llm_provider` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `ai-service/services/llm/__init__.py`:

```python
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
```

Import the factory in `ai-service/services/llm/__init__.py` is already done above. Now update the pipeline to consume the facade.

- [ ] **Step 4: Update ChatPipeline to use the LLM facade**

Edit `ai-service/services/chat_pipeline.py`. Replace the import on line 2 and the constructor body:

Before (line 2):
```python
from services.claude_client import ClaudeClient
```

After:
```python
from services.llm import provider
```

Before (lines 12-14):
```python
class ChatPipeline:
    def __init__(self) -> None:
        self.claude = ClaudeClient()
```

After:
```python
class ChatPipeline:
    def __init__(self) -> None:
        self.llm = provider

    def set_provider(self, llm_provider) -> None:
        self.llm_provider = llm_provider
```

- [ ] **Step 5: Update generate calls to use self.llm**

In `ai-service/services/chat_pipeline.py`, replace both calls `self.claude.generate(...)` with `self.llm.generate(...)` (lines 51 and 56).

- [ ] **Step 6: Run all tests**

Run: `cd ai-service && python -m pytest -v`
Expected: All tests pass, including the pre-existing pipeline behavior.

- [ ] **Step 7: Verify the pipeline still imports**

Run: `cd ai-service && python -c "from services.llm import get_llm_provider, provider; from services.chat_pipeline import ChatPipeline; ChatPipeline()"`
Expected: No exceptions; prints nothing.

- [ ] **Step 8: Commit**

```bash
git add ai-service/services/llm/__init__.py ai-service/services/chat_pipeline.py ai-service/tests/test_llm_factory.py
git commit -m "feat(llm): add provider factory and wire Groq into pipeline"
```

---

## Self-Review

**Spec coverage:**
- Issue #5 (pluggable LLM with Groq default): covered by Tasks 1-6.
- System prompt / 4-lens / persona: preserved unchanged; not in scope for this increment.

**Placeholder scan:** No TBD/TODO. Every step has concrete code and commands.

**Type consistency:** `generate(system_prompt, user_message) -> str` is identical across all three providers and the base class. `get_llm_provider(provider_name=None) -> LLMProvider` matches all factory tests. `ChatPipeline.llm` used consistently in Steps 5-6.

**Note on remaining subsystems:** The webhook consolidation (#2), Celery queue (#3), Khaya ASR (#4), Ga/Twi safety (#6), Supabase idempotency (#7), signature verification (#8), and Docker/CI (#9) are intentionally separate plans. Each will be written following this same template and executed in order.