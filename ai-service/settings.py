import os


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