import hmac
import hashlib

from services.signature import is_valid_signature, compute_signature


def _sig(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature():
    secret = "my_app_secret"
    body = b'{"object": "whatsapp_business_account"}'
    header = _sig(secret, body)
    assert is_valid_signature(secret, header, body) is True


def test_invalid_signature_rejected():
    secret = "my_app_secret"
    body = b'{"object": "whatsapp_business_account"}'
    bad_header = _sig("wrong_secret", body)
    assert is_valid_signature(secret, bad_header, body) is False


def test_tampered_body_rejected():
    secret = "s"
    body = b'{"object":"x"}'
    header = _sig(secret, b'{"object":"y"}')
    assert is_valid_signature(secret, header, body) is False


def test_missing_header_false():
    assert is_valid_signature("s", "", b"body") is False
    assert is_valid_signature("s", None, b"body") is False


def test_malformed_header_false():
    assert is_valid_signature("s", "sha256:abc", b"body") is False


def test_compute_signature_roundtrip():
    assert compute_signature("s", b"x") == _sig("s", b"x")