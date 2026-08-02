import os

import requests

from services import khaya

GOOGLE_TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"


def _google_translate(text: str, target_language: str, source_language: str | None = None) -> str:
    api_key = os.getenv("GOOGLE_TRANSLATE_KEY", "")
    if not api_key:
        return text
    params: dict = {"q": text, "target": target_language, "key": api_key, "format": "text"}
    if source_language:
        params["source"] = source_language
    response = requests.post(GOOGLE_TRANSLATE_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()["data"]["translations"][0]["translatedText"]


def _provider() -> str:
    return os.getenv("TRANSLATION_PROVIDER", "khaya").lower()


def translate(text: str, target_language: str, source_language: str | None = None) -> str:
    if _provider() == "google":
        return _google_translate(text, target_language, source_language)

    # Khaya provider (default). English logical target -> Khaya pair.
    source = source_language or "en"
    pair = f"{source}-{target_language}"
    try:
        translated = khaya.khaya_translate(text, pair)
    except Exception:
        translated = ""
    if translated:
        return translated
    return _google_translate(text, target_language, source_language)


def to_english(text: str, source_language: str | None = None) -> str:
    return translate(text, "en", source_language)
    return translate(text, "en", source_language)


def to_twi(text: str) -> str:
    return translate(text, "tw", "en")


def to_ga(text: str) -> str:
    return translate(text, "gaa", "en")