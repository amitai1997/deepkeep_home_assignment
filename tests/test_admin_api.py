"""Tests for admin API endpoints."""

from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from src.main import create_app
from src.models.schemas import UserStatus


class TestAdminAPI:
    """Test cases for admin API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_unblock_user_success(self):
        """Test successful user unblocking."""
        user_id = "test_user"

        # Create mock user status
        now = datetime.now(timezone.utc)
        mock_user_status = UserStatus(
            user_id=user_id,
            violation_count=0,
            is_blocked=False,
            blocked_until=None,
            last_violation=None,
            created_at=now,
            updated_at=now,
        )

        # Mock the user store
        with patch("src.api.admin.get_user_store") as mock_get_store:
            mock_store = Mock()
            mock_store._users = {user_id: mock_user_status}  # User exists
            mock_store.unblock_user.return_value = mock_user_status
            mock_get_store.return_value = mock_store

            # Make request
            response = self.client.put(f"/admin/unblock/{user_id}")

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["user_id"] == user_id
            assert response_data["violation_count"] == 0
            assert response_data["is_blocked"] is False
            assert response_data["blocked_until"] is None

            # Verify mock was called
            mock_store.unblock_user.assert_called_once_with(user_id)

    def test_unblock_user_not_found(self):
        """Test unblocking non-existent user."""
        user_id = "nonexistent_user"

        # Mock the user store with empty users dict
        with patch("src.api.admin.get_user_store") as mock_get_store:
            mock_store = Mock()
            mock_store._users = {}  # User doesn't exist
            mock_get_store.return_value = mock_store

            # Make request
            response = self.client.put(f"/admin/unblock/{user_id}")

            # Assertions
            assert response.status_code == 404
            response_data = response.json()
            assert "User not found" in response_data["detail"]["error"]
            assert response_data["detail"]["code"] == "USER_NOT_FOUND"
            assert user_id in response_data["detail"]["details"]

    def test_unblock_user_blocked_user(self):
        """Test unblocking a user who was previously blocked."""
        user_id = "blocked_user"

        # Create mock blocked user status
        now = datetime.now(timezone.utc)
        blocked_user_status = UserStatus(
            user_id=user_id,
            violation_count=3,
            is_blocked=True,
            blocked_until=now,
            last_violation=now,
            created_at=now,
            updated_at=now,
        )

        # Create mock unblocked user status (after unblocking)
        unblocked_user_status = UserStatus(
            user_id=user_id,
            violation_count=0,
            is_blocked=False,
            blocked_until=None,
            last_violation=now,
            created_at=now,
            updated_at=now,
        )

        # Mock the user store
        with patch("src.api.admin.get_user_store") as mock_get_store:
            mock_store = Mock()
            mock_store._users = {
                user_id: blocked_user_status
            }  # User exists and is blocked
            mock_store.unblock_user.return_value = unblocked_user_status
            mock_get_store.return_value = mock_store

            # Make request
            response = self.client.put(f"/admin/unblock/{user_id}")

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["user_id"] == user_id
            assert response_data["violation_count"] == 0
            assert response_data["is_blocked"] is False
            assert response_data["blocked_until"] is None

            # Verify mock was called
            mock_store.unblock_user.assert_called_once_with(user_id)
