"""Google Gemini LLM Provider Implementation for Phase 3."""

import json
from typing import Dict, Any, List, Optional
import httpx
from app.agent.llm.base import LLMProvider, LLMMessage, LLMResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider implementation."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", timeout_seconds: int = 30):
        # Normalize model name if needed
        model_clean = model.replace("models/", "") if model else "gemini-1.5-flash"
        model_name = model_clean if model_clean.startswith("gemini") else "gemini-1.5-flash"
        super().__init__(api_key=api_key, model=model_name, timeout_seconds=timeout_seconds)

    def _convert_messages_to_gemini(self, messages: List[LLMMessage]) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Convert standard messages to Gemini contents and system instruction."""
        system_instruction = None
        contents = []

        system_parts = []
        for msg in messages:
            if msg.role == "system":
                system_parts.append(msg.content)
            else:
                role = "user" if msg.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })

        if system_parts:
            system_instruction = {
                "parts": [{"text": "\n\n".join(system_parts)}]
            }

        # Gemini requires at least one user content
        if not contents:
            contents.append({
                "role": "user",
                "parts": [{"text": "Proceed with analysis."}]
            })

        return system_instruction, contents

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a text response from Gemini."""
        try:
            system_instruction, contents = self._convert_messages_to_gemini(messages)
            
            payload: Dict[str, Any] = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                }
            }
            if system_instruction:
                payload["systemInstruction"] = system_instruction
            if max_tokens:
                payload["generationConfig"]["maxOutputTokens"] = max_tokens

            url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"
            
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                
                candidate = data["candidates"][0]
                content_text = candidate["content"]["parts"][0]["text"]
                finish_reason = candidate.get("finishReason")
                usage = data.get("usageMetadata")

                return LLMResponse(
                    content=content_text,
                    finish_reason=finish_reason,
                    usage=usage,
                )

        except httpx.HTTPError as e:
            logger.error(f"Gemini API HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Gemini provider: {e}")
            raise

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON response from Gemini using responseMimeType."""
        try:
            system_instruction, contents = self._convert_messages_to_gemini(messages)
            
            # Enforce JSON output in system instruction and config
            schema_str = json.dumps(response_schema)
            schema_note = f"\nYou MUST respond with a valid JSON object strictly matching this schema:\n{schema_str}"
            
            if system_instruction:
                system_instruction["parts"][0]["text"] += schema_note
            else:
                system_instruction = {"parts": [{"text": schema_note}]}

            payload: Dict[str, Any] = {
                "contents": contents,
                "systemInstruction": system_instruction,
                "generationConfig": {
                    "temperature": temperature,
                    "responseMimeType": "application/json",
                }
            }
            if max_tokens:
                payload["generationConfig"]["maxOutputTokens"] = max_tokens

            url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()

                candidate = data["candidates"][0]
                content_text = candidate["content"]["parts"][0]["text"].strip()
                
                # If wrapped in markdown code fence, strip it
                if content_text.startswith("```json"):
                    content_text = content_text[7:]
                if content_text.startswith("```"):
                    content_text = content_text[3:]
                if content_text.endswith("```"):
                    content_text = content_text[:-3]
                content_text = content_text.strip()

                try:
                    structured_data = json.loads(content_text)
                    return structured_data
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Gemini structured JSON: {content_text}")
                    raise ValueError(f"Invalid JSON returned by Gemini: {e}")

        except httpx.HTTPError as e:
            logger.error(f"Gemini API error in structured generation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Gemini structured generation: {e}")
            raise

    def validate_connection(self) -> bool:
        """Validate connection to Gemini API."""
        try:
            url = f"{self.BASE_URL}/{self.model}?key={self.api_key}"
            with httpx.Client(timeout=10) as client:
                response = client.get(url)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Gemini connection validation failed: {e}")
            return False
