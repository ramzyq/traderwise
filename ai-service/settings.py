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
    def graph_base(self) -> str:
        return "https://graph.facebook.com/v19.0/"


settings = Settings()