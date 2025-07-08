from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock, patch

from src.main import create_app


class TestChatAPI:
    def setup_method(self):
        self.client = TestClient(create_app())

    def test_chat_success(self):
        with (
            patch("src.api.chat.get_moderation_service") as mod,
            patch("src.api.chat.get_openai_client") as openai,
        ):
            mod_inst = Mock()
            mod_inst.process_message = AsyncMock(return_value=(False, False))
            mod.return_value = mod_inst
            openai_inst = Mock()
            openai_inst.chat_completion = AsyncMock(return_value="ok")
            openai.return_value = openai_inst

            resp = self.client.post("/chat/u1", json={"message": "hi"})
            assert resp.status_code == 200
            assert resp.json()["response"] == "ok"

    def test_chat_blocked(self):
        with patch("src.api.chat.get_moderation_service") as mod:
            mod_inst = Mock()
            mod_inst.process_message = AsyncMock(return_value=(False, True))
            mod.return_value = mod_inst
            resp = self.client.post("/chat/u1", json={"message": "hi"})
            assert resp.status_code == 403

    def test_chat_openai_failure(self):
        with (
            patch("src.api.chat.get_moderation_service") as mod,
            patch("src.api.chat.get_openai_client") as openai,
        ):
            mod_inst = Mock()
            mod_inst.process_message = AsyncMock(return_value=(False, False))
            mod.return_value = mod_inst
            openai_inst = Mock()
            import httpx

            openai_inst.chat_completion = AsyncMock(side_effect=httpx.HTTPError("boom"))
            openai.return_value = openai_inst
            resp = self.client.post("/chat/u1", json={"message": "hi"})
            assert resp.status_code == 502
