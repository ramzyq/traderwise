import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings:
    @property
    def whatsapp_access_token(self) -> str:
        return os.getenv("WHATSAPP_ACCESS_TOKEN", "")

    @property
    def whatsapp_phone_number_id(self) -> str:
        return os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

    @property
    def whatsapp_verify_token(self) -> str:
        return os.getenv("WHATSAPP_VERIFY_TOKEN", "")

    @property
    def whatsapp_app_secret(self) -> str:
        return os.getenv("WHATSAPP_APP_SECRET", "")

    @property
    def graph_base(self) -> str:
        return "https://graph.facebook.com/v19.0/"

    @property
    def asr_provider(self) -> str:
        return os.getenv("ASR_PROVIDER", "groq")

    @property
    def asr_language(self) -> str:
        return os.getenv("ASR_LANGUAGE", "tw")

    @property
    def translation_provider(self) -> str:
        return os.getenv("TRANSLATION_PROVIDER", "khaya")


settings = Settings()


class StartupSettings(BaseSettings):
    """Validated env schema. Enforced at process startup (production only)."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "development"
    port: int = 8000
    groq_api_key: str = ""
    khaya_api_key: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_app_secret: str = ""
    database_url: str = ""
    broker_url: str = ""
    result_backend: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False


def validate_startup_settings() -> list[str]:
    """Fail fast on missing required env vars in production.

    Returns a list of missing-var messages (empty when all required vars set
    or when not running in production). Safe to call on every startup.
    """
    cfg = StartupSettings()
    if cfg.app_env != "production":
        return []

    required = {
        "GROQ_API_KEY": cfg.groq_api_key,
        "WHATSAPP_ACCESS_TOKEN": cfg.whatsapp_access_token,
        "WHATSAPP_PHONE_NUMBER_ID": cfg.whatsapp_phone_number_id,
        "WHATSAPP_VERIFY_TOKEN": cfg.whatsapp_verify_token,
        "DATABASE_URL": cfg.database_url,
        "BROKER_URL": cfg.broker_url,
    }
    missing = [name for name, value in required.items() if not value]
    return [
        f"missing required env var: {name}" for name in missing
    ]