import hashlib
import hmac
import secrets


def compute_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _expected_hex(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def is_valid_signature(secret: str, signature: str | None, body: bytes) -> bool:
    """Verify Meta's X-Hub-Signature-256 against the raw request body.

    Uses a constant-time comparison to avoid timing attacks.
    """
    if not signature or not secret:
        return False
    if not signature.startswith("sha256="):
        return False
    provided = signature.split("=", 1)[1]
    expected = _expected_hex(secret, body)
    return secrets.compare_digest(provided, expected)