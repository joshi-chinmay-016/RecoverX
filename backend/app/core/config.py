from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache
from typing import Union, List


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

    # LLM Provider (Phase 3)
    llm_provider: str = "mock"  # gemini, groq, openai, mock
    llm_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "gemini-1.5-flash"  # Default model for Gemini
    llm_timeout_seconds: int = 30
    max_agent_steps: int = 6
    agent_version: str = "agent-v1"
    prompt_version: str = "recovery-prompt-v1"
    policy_version: str = "policy-v1"

    # Agent Policy Configuration
    max_retry_attempts: int = 3
    agent_confidence_threshold: float = 0.5

    # Phase 6 Security & Multi-Tenancy Configuration
    jwt_secret: str = "recoverx-production-jwt-secret-key-2026-secure"
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 8
    cors_origins: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:4173",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:4173",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ]
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:[0-9]+)?$"
    login_rate_limit_attempts: int = 15
    login_rate_limit_window_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
