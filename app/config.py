from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Akshat Royal Stay"
    app_env: str = "development"
    app_url: str = "https://online.akshatroyalstay.in"
    contact_email: str = "ars.familystay@gmail.com"
    contact_phone: str = "+919092977055"
    database_url: str = "sqlite:///./online_ars.db"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    booking_gst_percent: float = 5.0
    booking_hold_minutes: int = 10
    extra_occupant_rate: float = 500.0
    smtp_host: str = "smtp.hostinger.com"
    smtp_port: int = 465
    smtp_username: str = "akshatroyalstay@ads-ai.in"
    smtp_password: str = ""
    smtp_use_ssl: bool = True
    smtp_use_starttls: bool = False
    smtp_from_email: str = "akshatroyalstay@ads-ai.in"
    smtp_from_name: str = "Akshat Royal Stay"
    smtp_reply_to: str = "ars.familystay@gmail.com"
    smtp_timeout_seconds: int = 15

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
