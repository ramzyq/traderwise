from services import transcribe


def test_groq_primary_selected(monkeypatch, tmp_path):
    monkeypatch.setenv("ASR_PROVIDER", "groq")
    audio_file = tmp_path / "note.ogg"
    audio_file.write_bytes(b"abc")
    called = {"providers": []}

    def fake_download(url, token=None):
        return str(audio_file)

    def fake_run_provider(provider, temp_path, suffix):
        called["providers"].append(provider)
        if provider == "groq":
            return "text from groq", "en"
        return "", "tw"

    monkeypatch.setattr(transcribe, "_download_audio", fake_download)
    monkeypatch.setattr(transcribe, "_run_provider", fake_run_provider)

    text, lang = transcribe.transcribe_from_audio_url("http://example.com/a.ogg")
    assert text == "text from groq"
    assert called["providers"] == ["groq"]


def test_khaya_selected_and_fallback_from_groq(monkeypatch, tmp_path):
    monkeypatch.setenv("ASR_PROVIDER", "khaya")
    audio_file = tmp_path / "note.ogg"
    audio_file.write_bytes(b"abc")
    called = {"providers": []}

    def fake_download(url, token=None):
        return str(audio_file)

    def fake_run_provider(provider, temp_path, suffix):
        called["providers"].append(provider)
        if provider == "khaya":
            return "", "unknown"
        return "groq fallback text", "en"

    monkeypatch.setattr(transcribe, "_download_audio", fake_download)
    monkeypatch.setattr(transcribe, "_run_provider", fake_run_provider)

    text, lang = transcribe.transcribe_from_audio_url("http://example.com/note.ogg")
    assert text == "groq fallback text"
    assert called["providers"] == ["khaya", "groq"]


def test_no_text_returns_graceful_message(monkeypatch, tmp_path):
    monkeypatch.setenv("ASR_PROVIDER", "khaya")
    audio_file = tmp_path / "note.ogg"
    audio_file.write_bytes(b"abc")

    def fake_download(url, token=None):
        return str(audio_file)

    def fake_run_provider(provider, temp_path, suffix):
        return "", "unknown"

    monkeypatch.setattr(transcribe, "_download_audio", fake_download)
    monkeypatch.setattr(transcribe, "_run_provider", fake_run_provider)

    text, lang = transcribe.transcribe_from_audio_url("http://x/x.ogg")
    assert "Could not transcribe" in text