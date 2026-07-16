from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Akshat Royal Stay"
    app_env: str = "development"
    app_url: str = "https://online.akshatroyalstay.in"
    contact_email: str = "ars.familystay@gmail.com"
    contact_phone: str = "+919092977055"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
