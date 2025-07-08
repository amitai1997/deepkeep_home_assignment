from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock, patch

from src.main import create_app


class TestAdminAPI:
    def setup_method(self):
        self.client = TestClient(create_app())

    def test_unblock_success(self):
        with patch("src.api.admin.get_user_store") as gst:
            store = Mock()
            store.user_exists = AsyncMock(return_value=True)
            from types import SimpleNamespace

            from datetime import datetime, timezone

            user = SimpleNamespace(
                user_id="u",
                violation_count=0,
                is_blocked=False,
                blocked_until=None,
                last_violation=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            store.unblock_user = AsyncMock(return_value=user)
            gst.return_value = store
            resp = self.client.put("/admin/unblock/u")
            assert resp.status_code == 200
            store.unblock_user.assert_awaited_once_with("u")

    def test_unblock_missing(self):
        with patch("src.api.admin.get_user_store") as gst:
            store = Mock()
            store.user_exists = AsyncMock(return_value=False)
            gst.return_value = store
            resp = self.client.put("/admin/unblock/x")
            assert resp.status_code == 404
