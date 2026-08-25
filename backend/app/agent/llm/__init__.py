"""LLM Provider Abstraction for Phase 3 Agent.

Provides abstraction over different LLM providers (Gemini, Groq, OpenAI, Mock)
to enable seamless switching and deterministic testing without code changes.
"""

from app.agent.llm.base import LLMProvider, LLMMessage, LLMResponse
from app.agent.llm.provider import GroqProvider, OpenAIProvider
from app.agent.llm.gemini import GeminiProvider
from app.agent.llm.mock import MockLLMProvider
from app.core.config import settings as default_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_llm_provider(settings=None) -> LLMProvider:
    """Factory to initialize the configured LLM provider."""
    cfg = settings or default_settings
    provider_name = (cfg.llm_provider or "mock").lower()

    if provider_name == "gemini":
        api_key = cfg.gemini_api_key or cfg.llm_api_key
        if not api_key:
            logger.warning("Gemini API key not configured; falling back to MockLLMProvider")
            return MockLLMProvider(model=cfg.llm_model, timeout_seconds=cfg.llm_timeout_seconds)
        return GeminiProvider(
            api_key=api_key,
            model=cfg.llm_model or "gemini-1.5-flash",
            timeout_seconds=cfg.llm_timeout_seconds,
        )

    elif provider_name == "groq":
        api_key = cfg.groq_api_key or cfg.llm_api_key
        if not api_key:
            logger.warning("Groq API key not configured; falling back to MockLLMProvider")
            return MockLLMProvider(model=cfg.llm_model, timeout_seconds=cfg.llm_timeout_seconds)
        return GroqProvider(
            api_key=api_key,
            model=cfg.llm_model or "llama3-70b-8192",
            timeout_seconds=cfg.llm_timeout_seconds,
        )

    elif provider_name == "openai":
        api_key = cfg.openai_api_key or cfg.llm_api_key
        if not api_key:
            logger.warning("OpenAI API key not configured; falling back to MockLLMProvider")
            return MockLLMProvider(model=cfg.llm_model, timeout_seconds=cfg.llm_timeout_seconds)
        return OpenAIProvider(
            api_key=api_key,
            model=cfg.llm_model or "gpt-4o-mini",
            timeout_seconds=cfg.llm_timeout_seconds,
        )

    elif provider_name == "mock":
        return MockLLMProvider(
            model=cfg.llm_model or "mock-model",
            timeout_seconds=cfg.llm_timeout_seconds,
        )

    else:
        logger.warning(f"Unknown LLM provider '{provider_name}'; falling back to MockLLMProvider")
        return MockLLMProvider(model=cfg.llm_model, timeout_seconds=cfg.llm_timeout_seconds)


__all__ = [
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    "GeminiProvider",
    "GroqProvider",
    "OpenAIProvider",
    "MockLLMProvider",
    "get_llm_provider",
]
