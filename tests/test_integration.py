import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.main import create_app

pytestmark = pytest.mark.asyncio


async def test_blocking_flow(user_store):
    app = create_app()
    client = TestClient(app)

    with (
        patch("src.api.chat.get_openai_client") as openai,
        patch(
            "src.services.moderation.ModerationService.check_content_violation",
            return_value=True,
        ),
    ):
        openai_inst = AsyncMock()
        openai_inst.chat_completion = AsyncMock(return_value="ok")
        openai.return_value = openai_inst
        for _ in range(3):
            resp = client.post("/chat/a", json={"message": "hi b"})
            assert resp.status_code == 200
        resp = client.post("/chat/a", json={"message": "blocked"})
        assert resp.status_code == 403
