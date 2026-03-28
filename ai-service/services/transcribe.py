import os
import tempfile
from urllib.parse import urlparse

import requests

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


def transcribe_from_audio_url(audio_url: str, access_token: str | None = None) -> tuple[str, str]:
    """
    Downloads audio to a temporary file, transcribes via Whisper, then deletes immediately.
    Audio is never persisted beyond the duration of this call.
    """
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        return "Voice note received. Please set GROQ_API_KEY to enable transcription.", "unknown"

    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    audio_response = requests.get(audio_url, headers=headers, timeout=60)
    audio_response.raise_for_status()

    suffix, mime_type = _audio_mime(audio_url)
    tmp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp_file.write(audio_response.content)
        tmp_file.flush()
        tmp_file.close()

        with open(tmp_file.name, "rb") as audio_file:
            whisper_response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {groq_key}"},
                files={"file": (f"audio{suffix}", audio_file, mime_type)},
                data={"model": "whisper-large-v3-turbo", "response_format": "verbose_json"},
                timeout=30,
            )
        whisper_response.raise_for_status()
    finally:
        os.unlink(tmp_file.name)

    payload = whisper_response.json()
    text = payload.get("text", "").strip()
    language = payload.get("language", "unknown")
    return text, language
