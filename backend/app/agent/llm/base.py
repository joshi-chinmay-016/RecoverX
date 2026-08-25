"""Base LLM Provider Abstraction."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Message for LLM interaction."""
    role: str  # system, user, assistant
    content: str


class LLMResponse(BaseModel):
    """Response from LLM."""
    content: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, model: str, timeout_seconds: int = 30):
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
    
    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate a structured response from the LLM."""
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate that the provider connection works."""
        pass
