from settings import Settings, validate_startup_settings


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
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "appsecret")
    s = Settings()
    assert s.whatsapp_access_token == "tok_abc"
    assert s.whatsapp_phone_number_id == "12345"
    assert s.whatsapp_verify_token == "veriftok"
    assert s.whatsapp_app_secret == "appsecret"


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


def test_validate_startup_skips_non_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    assert validate_startup_settings() == []


def test_validate_startup_reports_missing_required(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    for var in (
        "GROQ_API_KEY",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_PHONE_NUMBER_ID",
        "WHATSAPP_VERIFY_TOKEN",
        "DATABASE_URL",
    ):
        monkeypatch.delenv(var, raising=False)
    missing = validate_startup_settings()
    assert len(missing) == 5
    assert "missing required env var: GROQ_API_KEY" in missing


def test_validate_startup_ok_when_required_set(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("GROQ_API_KEY", "g")
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "t")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "p")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "v")
    monkeypatch.setenv("DATABASE_URL", "postgres://x")
    monkeypatch.setenv("BROKER_URL", "redis://localhost:6379/0")
    assert validate_startup_settings() == []