# Khaya AI Multilingual ASR & Translation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Khaya AI (Ghana NLP) for Ga and Twi speech-to-text and translation, paired with a Groq Whisper-large-v3-turbo fallback. Reverse the translation/ASR "tying" so the pipeline works for the three supported languages (Twi, Ga, English).

**Tech Stack:** Python 3.11+, `requests` (project already uses it), `KHAYA_API_KEY` env var.

## Khaya API Contract (verified from official SDK v0.1.1)

- Base URL: `https://translation.ghananlp.org`
- Auth header: `Ocp-Apim-Subscription-Key: <KHAYA_API_KEY>` (plus `Content-Type: application/json`)
- **Translation**: `POST /v1/translate`, JSON body `{ "in": "<text>", "lang": "<tw>|<gaa>" }`. Khaya pair codes are like `en-tw`, `tw-en`, `en-ga`, `ga-en` where Ga is `gaa` and Twi is `tw`. Response is the translated string.
- **ASR**: `POST /asr/v1/transcribe`, query param `language=<tw|gaa|...>` , raw audio bytes in the body. Response is the transcript string.
- Language codes: `en`, `tw`, `gaa`, plus many others.

## Required Env Variables (all optional; providers fall back to no-op)

- `KHAYA_API_KEY=` — Khaya API key
- `ASR_PROVIDER=groq` — default `groq`; set `khaya` to use Khaya ASR
- `ASR_LANGUAGE=tw` — Khaya ASR requires a language (default `tw` in Twi; set `gaa` for Ga)
- `TRANSLATION_PROVIDER=khaya` — default `khaya`, fallback `google`

## Files

- Modify: `ai-service/services/khaya.py` (new)
- Modify: `ai-service/services/transcribe.py`
- Modify: `ai-service/services/translate.py`
- Modify: `ai-service/settings.py`
- Modify: `ai-service/.env.example`
- Test: `ai-service/tests/test_khaya.py` (new)
- Test: `ai-service/tests/test_translate.py` (new or extend)
- Test: `ai-service/tests/test_transcribe.py` (extend)

---

### Task 1 — `services/khaya.py`

Create a small module wrapping the two Khaya endpoints with `requests`. Keep raw bytes for ASR. Use `SELECT`-like logic: if `KHAYA_API` not set, return empty / raise-friendly so callers fall back to Groq.

**File:** `ai-service/services/khaya.py`

```python
import os

import requests

BASE_URL = "https://translation.ghananlp.org"
TRANSLATE_URL = BASE_URL + "/v1/translate"
ASR_URL = BASE_URL + "/asr/v1/transcribe"


def _headers() -> dict[str, str]:
    key = os.getenv("KHAYA_API_KEY", "")
    return {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/json",
    }


def khaya_translate(text: str, lang_pair: str) -> str:
    """Translate using Khaya. Returns '' if key missing. Raises on request error."""
    if not os.getenv("KHAYA_API_KEY", ""):
        return ""
    resp = requests.post(
        TRANSLATE_URL,
        headers=_headers(),
        json={"in": text, "lang": lang_pair},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def khai_asr(audio_bytes: bytes, language: str) -> str:
    """Khaya ASR raw bytes → transcript. Empty string when no key."""
    if not os.getenv("KHAYA_API_KEY", ""):
        return ""
    headers = _headers()
    headers["Content-Type"] = "audio/ogg"  # Twilio voice notes
    resp = requests.post(
        ASR_URL,
        headers=headers,
        params={"language": language},
        data=audio_bytes,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.text
```

**Verified against Khaya SDK source** (endpoint paths, auth header, body shapes, params). The actual signature response (`resp.json()` for translate, `resp.text` for ASR) matches the SDK: `TranslationResult.text = response.json()`, `TranscriptionResult.text = response.json()`.

But style: keep `requests` since the repo already depends on it (transcribe.py, translate.py). **Two tests:**

`tests/test_khaya.py`:
- `test_translate_no_key_returns_empty` — monkeypatch `KHAYA_API_KEY=""`, call `khai_translate`, return empty, no network.
- `test_asr_no_key_returns_empty`.

Then implement. **Do not** mock the network here; instead test the "no-key" guard paths, which are the deterministic branches. (Optionally add a monkeypatched `requests.post` returning a fake response for the happy path — see Task 4.)

---

### Task 2 — Update `services/translate.py` with provider switching

Current: only `GOOGLE_TRANSLATE_KEY`, `to_twi` and `to_english` hard-coded to Google.

Refactor to:

```python
import os
import requests

from services.khaya import khai_translate

GOOGLE_TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"

def _google_translate(text, target_language, source_language=None):
    api_key = os.getenv("GOOGLE_TRANSLATE_KEY", "")
    if not api_key:
        return text
    params = {"q": text, "target": target_language, "key": api_key, "format": "text"}
    if source_language:
        params["source"] = source_language
    resp = requests.post(GOOGLE_TRANSLATE_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]["translations"][0]["translatedText"]

def _provider() -> str:
    # TRANSLATION_PROVIDER in env (default khaya)
    return os.getenv("TRANSLATION_PROVIDER", "khaya").lower()
```

Semantic functions (used by main pipeline) — map a logical "target lang" to Khaya pair:

```python
def translate(text, target_language, source_language=None):
    ...
```

Keep the existing export names so nothing external breaks: `to_english(text, source_language=None)` and `to_twi(text)`, add `to_ga (text)`.

Behavior (when TRANSLATION_PROVIDER=khaya):
- `to_english`: khaya pair `<src>-en`, fallback to Google if khaya key missing/empty.
- `to_twi`: khaya pair `en-tw`.
- `to_ga`: khaya pair `en-gaa`.

When TRANSLATION_PROVIDER=google (legacy), use Google only (as today). Note Google uses distinct codes (`tw` for Akan/Twi, `ga` for Irish Ga — NOT Khaya's `gaa`), so keep the two providers isolated.

Ensure no new heavy imports at import time.

---

### Task 3 — `services/transcribe.py`: ASEASY provider switch + Groq fallback

Current `transcribe_from_audio_url` is Groq-only. Refactor so provider is chosen by `ASR_PROVIDER`:
- `groq` (default): current Whisper path (downloads audio, POST to `https://api.groq.com/openai/v1/audio/transcriptions`, model `whisper-large-v3-turbo`, `verbose_json`).
- `khaya`: also download audio to temp file, read bytes, call `khai_asr(bytes, ASR_LANGUAGE)`. Return `(text, language)`.

Then a fallback: if the "primary" provider fails or returns empty, try the other (Groq ↔ Khaya). This satisfies "Groq Whisper-large-v3-turbo fallback".

Preserve "audio is never persisted" invariant (tempfile already handled).

Implement:
1. Split `transcribe_from_audio_url` to: download audio → temp file → read bytes → route to internal `_transcribe_groq(bytes_and_mime)` and `_transcribe_khaya(bytes)`, each returning `(text, language)`.
2. `_transcribe_any...` function that tries primary then fallback.

---

### Task 4 — settings + env + tests

**`settings.py`**: add readonly properties:
```python
@property
def asr_provider(self): return os.getenv("ASR_PROVIDER", "groq")
@property
def asr_language(self): return os.getenv("ASR_LANGUAGE", "tw")   # could be "ga"
@property
def translation_provider(self): return os.getenv("TRANSLATION_PROVIDER", "khaya")
```

**`.env.example`**: add
```
KHAYA_API_KEY=
ASR_PROVIDER=groq
ASR_LANGUAGE=tw
TRANSLATION_PROVIDER=khaya
```

**Tests:**
- `tests/test_khaya.py` happy-path monkeypatch of `requests.post` for `khai_translate` (fake Response with `.json()` and `.raise_for_status()`).
- `tests/test_translate.py`: `to_english`/`to_twi`/`to_ga` route through khay when key present, fallback to Google text when key absent.
- `tests/test_transcribe.py`: `transcribe_from_audio_url` uses `ASR_PROVIDER` value to pick provider.

---

### Task 5 — Compare & commit

Run `pytest -q` (expect ~2—6 warnings but all green). Commit each task; final `git status` clean plus auto-merge via PR (or push branch + PR per the finishing flow for repo).

## Self-Review

- **Cap**: Only the AI pipeline (transcribe + translate) modules change; no webhook/queue changes.
- **Provider dictionary**: `services/khaya.py` contains the two HTTP calls. `translate.py`/`transcribe.py` choose provider; `settings.py` exposes env. No secrets hard-coded.
- **No circular import**: `khaya.py` is a leaf module; `translate.py` imports `services.khaya`. `transcribe.py` may import `services.khaya` too.
- **Verify no Khaya SDK Pydantic dependency**: implemented with `requests` (already a repo dependency) plus minimal `dict`/str returns — no new deps besides what tests use (`requests`).
- **Language code**: Ga in Khaya is `gaa`; Twi is `tw`; English is `en`. Google uses `ga` for Irish and `tw` for Akan — do NOT send `gaa` to Google. The provider dispatches to the correct destination per provider.
- **Groq fallback**: if Khaya key absent or Khaya raise_for_status fails, transcribe falls back to Groq Whisper. If Groq has no key either, returns a graceful message.