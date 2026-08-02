import requests

GRAPH_BASE = "https://graph.facebook.com/v19.0/"


def send_message(phone_number_id: str, access_token: str, to: str, text: str) -> None:
    url = f"{GRAPH_BASE}{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )
        resp.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"WhatsApp send failed: {exc}") from exc


def resolve_media_url(access_token: str, media_id: str) -> str:
    url = f"{GRAPH_BASE}{media_id}"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("url", "")