"""OpenAI API client service."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol, Any
import asyncio
import httpx

from ..core.config import get_settings


# Public protocol for both real and mock clients – keeps static type checkers
# happy without forcing inheritance.


class OpenAIClientProtocol(Protocol):
    """Minimal contract shared by real and mock OpenAI clients."""

    async def chat_completion(self, message: str) -> str:  # noqa: D401
        """Return the assistant response as plain text."""
        ...


class OpenAIClient(OpenAIClientProtocol):
    """Async client for OpenAI API calls."""

    def __init__(self) -> None:
        """Initialize the OpenAI client."""
        self._settings = get_settings()
        self._base_url = "https://api.openai.com/v1"
        self._timeout = self._settings.openai_timeout
        self._retries = self._settings.openai_retries
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

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
            "Content-Type": "application/json",
        }

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 150,
            "temperature": 0.7,
        }

        for attempt in range(1, self._retries + 1):
            try:
                response = await self._client.post(
                    "/chat/completions", headers=headers, json=payload
                )
                response.raise_for_status()

                data: dict[str, Any] = response.json()
                return str(data["choices"][0]["message"]["content"]).strip()

            except httpx.HTTPError as e:
                if attempt == self._retries:
                    raise httpx.HTTPError(f"OpenAI API request failed: {e}") from e
                await asyncio.sleep(2 ** (attempt - 1))
            except (KeyError, IndexError) as e:
                raise ValueError(f"Unexpected OpenAI response format: {e}") from e

        raise httpx.HTTPError("OpenAI API request failed")


# ---------------------------------------------------------------------------
# Mock implementation — used during development/testing to avoid real API calls
# ---------------------------------------------------------------------------


class MockOpenAIClient:
    """Lightweight mock that mimics :class:`OpenAIClient` without network I/O.

    Echoes back the caller's message so that the rest of the system can
    continue to function during local development or testing sessions where
    making real OpenAI requests would be expensive.
    """

    async def chat_completion(self, message: str) -> str:  # noqa: D401
        """Return a deterministic mock response without external calls."""

        return f"[MOCK] Echo: {message}"


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAIClientProtocol:  # noqa: D401
    """Get OpenAI client instance.

    If the ``USE_MOCK_OPENAI`` environment variable (or corresponding
    configuration flag) is truthy, a :class:`MockOpenAIClient` is returned
    instead of the real networked client. This makes it trivial to run the
    service locally without an API key while still exercising the surrounding
    business logic.

    # type: ignore[override] – runtime returns an implementation compatible with
    # ``OpenAIClientProtocol`` (either real or mock). Annotated below for static
    # analyzers.
    """

    settings = get_settings()

    # The attribute is added to ``Settings`` in ``core.config``.
    if getattr(settings, "use_mock_openai", False):  # pragma: no cover
        return MockOpenAIClient()

    return OpenAIClient()
