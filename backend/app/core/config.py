from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # Database
    database_url: str = ""

    # Redis
    redis_url: str = ""

    # Application
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
