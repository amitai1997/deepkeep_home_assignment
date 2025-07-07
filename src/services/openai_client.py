"""OpenAI API client service."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

import httpx

from ..core.config import get_settings


class OpenAIClient:
    """Async client for OpenAI API calls."""
    
    def __init__(self) -> None:
        """Initialize the OpenAI client."""
        self._settings = get_settings()
        self._base_url = "https://api.openai.com/v1"
        self._timeout = 30.0
    
    async def chat_completion(self, message: str) -> str:
        """
        Send chat completion request to OpenAI.
        
        Args:
            message: User message to send to OpenAI
            
        Returns:
            OpenAI response content
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        headers = {
            "Authorization": f"Bearer {self._settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": message}
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
                
            except httpx.HTTPError as e:
                # Re-raise with more context
                raise httpx.HTTPError(f"OpenAI API request failed: {e}") from e
            except (KeyError, IndexError) as e:
                raise ValueError(f"Unexpected OpenAI response format: {e}") from e


def get_openai_client() -> OpenAIClient:
    """Get OpenAI client instance."""
    return OpenAIClient()