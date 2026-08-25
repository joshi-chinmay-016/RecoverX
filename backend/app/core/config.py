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

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
