from settings import Settings


def test_settings_defaults(monkeypatch):
    monkeypatch.delenv("WHATSAPP_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)
    monkeypatch.delenv("WHATSAPP_VERIFY_TOKEN", raising=False)
    s = Settings()
    assert s.whatsapp_access_token == ""
    assert s.whatsapp_phone_number_id == ""
    assert s.whatsapp_verify_token == ""
    assert s.graph_base == "https://graph.facebook.com/v19.0/"


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "tok_abc")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "12345")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "veriftok")
    s = Settings()
    assert s.whatsapp_access_token == "tok_abc"
    assert s.whatsapp_phone_number_id == "12345"
    assert s.whatsapp_verify_token == "veriftok"


def test_settings_multilingual_defaults(monkeypatch):
    monkeypatch.delenv("ASR_PROVIDER", raising=False)
    monkeypatch.delenv("ASR_LANGUAGE", raising=False)
    monkeypatch.delenv("TRANSLATION_PROVIDER", raising=False)
    s = Settings()
    assert s.asr_provider == "groq"
    assert s.asr_language == "tw"
    assert s.translation_provider == "khaya"


def test_settings_multilingual_reads_env(monkeypatch):
    monkeypatch.setenv("ASR_PROVIDER", "khaya")
    monkeypatch.setenv("ASR_LANGUAGE", "gaa")
    monkeypatch.setenv("TRANSLATION_PROVIDER", "google")
    s = Settings()
    assert s.asr_provider == "khaya"
    assert s.asr_language == "gaa"
    assert s.translation_provider == "google"