import os
import tempfile
from urllib.parse import urlparse

import requests

from services import khaya

_MIME_MAP = {
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
    ".m4a": "audio/mp4",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".flac": "audio/flac",
    ".webm": "audio/webm",
}


def _audio_mime(url: str) -> tuple[str, str]:
    """Return (suffix, mime_type) inferred from the URL path."""
    path = urlparse(url).path.lower()
    for suffix, mime in _MIME_MAP.items():
        if path.endswith(suffix):
            return suffix, mime
    return ".ogg", "audio/ogg"  # default for Twilio voice notes


def _download_audio(audio_url: str, access_token: str | None) -> str:
    """Download audio to a temp file and return its path. Audio is not persisted beyond the call."""
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    audio_response = requests.get(audio_url, headers=headers, timeout=60)
    audio_response.raise_for_status()

    suffix, _mime = _audio_mime(audio_url)
    tmp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp_file.write(audio_response.content)
        tmp_file.flush()
    finally:
        tmp_file.close()
    return tmp_file.name


def _transcribe_groq(temp_path: str, suffix: str) -> tuple[str, str]:
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        return "", "unknown"
    with open(temp_path, "rb") as audio_file:
        whisper_response = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {groq_key}"},
            files={"file": (f"audio{suffix}", audio_file, _audio_mime(temp_path)[1])},
            data={"model": "whisper-large-v3-turbo", "response_format": "verbose_json"},
            timeout=30,
        )
    whisper_response.raise_for_status()
    payload = whisper_response.json()
    return payload.get("text", "").strip(), payload.get("language", "unknown")


def _transcribe_khaya(temp_path: str) -> tuple[str, str]:
    with open(temp_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    language = os.getenv("ASR_LANGUAGE", "tw")
    text = khaya.khaya_asr(audio_bytes, language).strip()
    return text, language if text else "unknown"


def _primary_provider() -> str:
    return os.getenv("ASR_PROVIDER", "groq").lower()


def _fallback_provider() -> str:
    return "khaya" if _primary_provider() == "groq" else "groq"


def _run_provider(provider: str, temp_path: str, suffix: str) -> tuple[str, str]:
    if provider == "khaya":
        return _transcribe_khaya(temp_path)
    return _transcribe_groq(temp_path, suffix)


def transcribe_from_audio_url(audio_url: str, access_token: str | None = None) -> tuple[str, str]:
    """Transcribe audio via the configured ASR provider (Groq or Khaya) with cross-fallback.

    Audio is downloaded to a temp file, transcribed, and immediately deleted.
    """
    temp_path = _download_audio(audio_url, access_token)
    suffix, _ = _audio_mime(audio_url)
    try:
        text, language = _run_provider(_primary_provider(), temp_path, suffix)
        if not text:
            text, language = _run_provider(_fallback_provider(), temp_path, suffix)
        if not text:
            return "Could not transcribe the voice note. Please try again.", language
        return text, language
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)