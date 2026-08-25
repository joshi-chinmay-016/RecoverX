"""Groq LLM Provider Implementation."""

import httpx
import json
from typing import Dict, Any, List, Optional
from app.agent.llm.base import LLMProvider, LLMMessage, LLMResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class GroqProvider(LLMProvider):
    """Groq LLM provider implementation."""
    
    BASE_URL = "https://api.groq.com/openai/v1"
    
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a response from Groq."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": temperature,
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                
                data = response.json()
                choice = data["choices"][0]
                
                return LLMResponse(
                    content=choice["message"]["content"],
                    finish_reason=choice.get("finish_reason"),
                    usage=data.get("usage"),
                )
                
        except httpx.HTTPError as e:
            logger.error(f"Groq API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Groq provider: {e}")
            raise
    
    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate a structured response from Groq using JSON mode."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            # Add schema instruction to system message
            schema_instruction = (
                "You must respond with valid JSON only. "
                f"Use this schema: {json.dumps(response_schema)}"
            )
            
            enhanced_messages = [
                LLMMessage(role="system", content=schema_instruction),
                *messages,
            ]
            
            payload = {
                "model": self.model,
                "messages": [{"role": m.role, "content": m.content} for m in enhanced_messages],
                "temperature": temperature,
                "response_format": {"type": "json_object"},
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Parse JSON response
                try:
                    structured_data = json.loads(content)
                    return structured_data
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse structured response: {content}")
                    raise ValueError(f"Invalid JSON response: {e}")
                
        except httpx.HTTPError as e:
            logger.error(f"Groq API error in structured generation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Groq structured generation: {e}")
            raise
    
    def validate_connection(self) -> bool:
        """Validate Groq connection (synchronous check)."""
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
            }
            
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Groq connection validation failed: {e}")
            return False


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""

    BASE_URL = "https://api.openai.com/v1"

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a response from OpenAI."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": temperature,
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                choice = data["choices"][0]

                return LLMResponse(
                    content=choice["message"]["content"],
                    finish_reason=choice.get("finish_reason"),
                    usage=data.get("usage"),
                )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate structured response from OpenAI."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            schema_instruction = (
                "You must respond with valid JSON only matching this schema: "
                f"{json.dumps(response_schema)}"
            )

            enhanced_messages = [
                LLMMessage(role="system", content=schema_instruction),
                *messages,
            ]

            payload = {
                "model": self.model,
                "messages": [{"role": m.role, "content": m.content} for m in enhanced_messages],
                "temperature": temperature,
                "response_format": {"type": "json_object"},
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)

        except Exception as e:
            logger.error(f"OpenAI structured generation error: {e}")
            raise

    def validate_connection(self) -> bool:
        """Validate connection to OpenAI."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            with httpx.Client(timeout=10) as client:
                response = client.get(f"{self.BASE_URL}/models", headers=headers)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenAI connection validation failed: {e}")
            return False

