import os

import requests

GOOGLE_TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"


def translate(text: str, target_language: str, source_language: str | None = None) -> str:
    api_key = os.getenv("GOOGLE_TRANSLATE_KEY", "")
    if not api_key:
        return text

    params: dict = {"q": text, "target": target_language, "key": api_key, "format": "text"}
    if source_language:
        params["source"] = source_language

    response = requests.post(GOOGLE_TRANSLATE_URL, params=params, timeout=10)
    response.raise_for_status()

    payload = response.json()
    return payload["data"]["translations"][0]["translatedText"]


def to_english(text: str, source_language: str | None = None) -> str:
    return translate(text, target_language="en", source_language=source_language)


def to_twi(text: str) -> str:
    return translate(text, target_language="tw", source_language="en")
