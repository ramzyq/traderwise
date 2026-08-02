from services import translate


def test_twi_uses_khaya_pair(monkeypatch):
    monkeypatch.setenv("TRANSLATION_PROVIDER", "khaya")
    monkeypatch.setenv("KHAYA_API_KEY", "key")
    monkeypatch.setenv("GOOGLE_TRANSLATE_KEY", "")
    monkeypatch.setattr(
        "services.translate.khaya.khaya_translate",
        lambda text, pair: "Mepa wo kyew",
    )
    assert translate.to_twi("Please") == "Mepa wo kyew"


def test_ga_uses_khaya_pair(monkeypatch):
    monkeypatch.setenv("TRANSLATION_PROVIDER", "khaya")
    monkeypatch.setenv("KHAYA_API_KEY", "key")
    monkeypatch.setenv("GOOGLE_TRANSLATE_KEY", "")
    monkeypatch.setattr(
        "services.translate.khaya.khaya_translate",
        lambda text, pair: "Heeno",
    )
    assert translate.to_ga("Hello") == "Heeno"


def test_to_english_khaya(monkeypatch):
    monkeypatch.setenv("TRANSLATION_PROVIDER", "khaya")
    monkeypatch.setenv("KHAYA_API_KEY", "key")
    monkeypatch.setenv("GOOGLE_TRANSLATE_KEY", "")
    monkeypatch.setattr(
        "services.translate.khaya.khaya_translate",
        lambda text, pair: "I need to buy",
    )
    assert translate.to_english("Mepɛ sɛ metɔ", "tw") == "I need to buy"


def test_google_provider_uses_google(monkeypatch):
    monkeypatch.setenv("TRANSLATION_PROVIDER", "google")
    monkeypatch.setenv("KHAYA_API_KEY", "")
    monkeypatch.setenv("GOOGLE_TRANSLATE_KEY", "gkey")
    monkeypatch.setattr(
        "services.translate._google_translate",
        lambda text, target, source=None: "Me ho yɛ",
    )
    assert translate.to_twi("I am fine") == "Me ho yɛ"


def test_khaya_fallback_to_google_when_empty(monkeypatch):
    monkeypatch.setenv("TRANSLATION_PROVIDER", "khaya")
    monkeypatch.setenv("KHAYA_API_KEY", "key")
    monkeypatch.setenv("GOOGLE_TRANSLATE_KEY", "gkey")
    monkeypatch.setattr(
        "services.translate.khaya.khaya_translate",
        lambda text, pair: "",
    )
    monkeypatch.setattr(
        "services.translate._google_translate",
        lambda text, target, source=None: "Google text",
    )
    assert translate.to_twi("Please") == "Google text"