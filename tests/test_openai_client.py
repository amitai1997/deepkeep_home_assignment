import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.openai_client import OpenAIClient, get_openai_client


def test_get_openai_client_cached():
    c1 = get_openai_client()
    c2 = get_openai_client()
    assert c1 is c2


@pytest.mark.asyncio
async def test_chat_completion_success(monkeypatch):
    client = OpenAIClient()
    fake_response = MagicMock()
    fake_response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    fake_response.raise_for_status.return_value = None
    post_mock = AsyncMock(return_value=fake_response)
    client._client = MagicMock()
    client._client.post = post_mock

    result = await client.chat_completion("hi")
    assert result == "ok"
