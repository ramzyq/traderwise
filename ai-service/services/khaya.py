import os

import requests

BASE_URL = "https://translation.ghananlp.org"
TRANSLATE_URL = BASE_URL + "/v1/translate"
ASR_URL = BASE_URL + "/asr/v1/transcribe"


def _headers(with_json: bool = True) -> dict[str, str]:
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("KHAYA_API_KEY", ""),
    }
    if with_json:
        headers["Content-Type"] = "application/json"
    return headers


def khaya_translate(text: str, lang_pair: str) -> str:
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


def khaya_asr(audio_bytes: bytes, language: str) -> str:
    if not os.getenv("KHAYA_API_KEY", ""):
        return ""
    headers = _headers(with_json=False)
    headers["Content-Type"] = "audio/ogg"
    resp = requests.post(
        ASR_URL,
        headers=headers,
        params={"language": language},
        data=audio_bytes,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.text