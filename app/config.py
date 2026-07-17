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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
