"""Integration tests for the complete blocking flow."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from src.main import create_app
from src.store.user_store import get_user_store


class TestBlockingFlowIntegration:
    """Integration tests for the complete user blocking and unblocking flow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.client = TestClient(self.app)
        # Reset user store for each test
        user_store = get_user_store()
        user_store._users.clear()

    def test_three_strikes_blocking_flow(self):
        """Test complete flow of user getting blocked after 3 violations."""
        user_id = "violator"
        other_user_id = "victim"

        # First create the victim user by making a chat request
        with patch("src.api.chat.get_openai_client") as mock_openai:
            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat_completion = AsyncMock(return_value="Response")
            mock_openai.return_value = mock_openai_instance

            # Victim sends a normal message
            response = self.client.post(
                f"/chat/{other_user_id}", json={"message": "Hello world"}
            )
            assert response.status_code == 200

        # Now test violations
        with patch("src.api.chat.get_openai_client") as mock_openai:
            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat_completion = AsyncMock(return_value="Response")
            mock_openai.return_value = mock_openai_instance

            # First violation - should succeed
            response = self.client.post(
                f"/chat/{user_id}",
                json={"message": f"Hey {other_user_id}, how are you?"},
            )
            assert response.status_code == 200

            # Second violation - should succeed
            response = self.client.post(
                f"/chat/{user_id}", json={"message": f"I know {other_user_id} is here"}
            )
            assert response.status_code == 200

            # Third violation - should succeed but user is now blocked
            response = self.client.post(
                f"/chat/{user_id}", json={"message": f"Last message to {other_user_id}"}
            )
            assert response.status_code == 200

            # Fourth attempt - should be blocked
            response = self.client.post(
                f"/chat/{user_id}", json={"message": "I'm blocked now"}
            )
            assert response.status_code == 403
            response_data = response.json()
            assert response_data["detail"]["code"] == "USER_BLOCKED"

    def test_automatic_unblocking_after_timeout(self):
        """Test that users are automatically unblocked after the timeout period."""
        user_id = "temp_blocked_user"
        other_user_id = "other_user"

        # Create users
        user_store = get_user_store()
        user_store.get_user(other_user_id)

        # Block the user manually
        for _ in range(3):
            user_store.add_violation(user_id)

        # User should be blocked
        with patch("src.api.chat.get_openai_client") as mock_openai:
            response = self.client.post(
                f"/chat/{user_id}", json={"message": "I should be blocked"}
            )
            assert response.status_code == 403

        # Simulate time passing by modifying blocked_until
        user = user_store.get_user(user_id)
        user.blocked_until = datetime.now(timezone.utc) - timedelta(minutes=1)

        # User should be automatically unblocked
        with patch("src.api.chat.get_openai_client") as mock_openai:
            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat_completion = AsyncMock(return_value="Response")
            mock_openai.return_value = mock_openai_instance

            response = self.client.post(
                f"/chat/{user_id}", json={"message": "I should be unblocked now"}
            )
            assert response.status_code == 200

        # Verify user state was reset
        user = user_store.get_user(user_id)
        assert user.is_blocked is False
        assert user.violation_count == 0
        assert user.blocked_until is None

    def test_manual_unblock_resets_user_state(self):
        """Test that manual unblocking properly resets user state."""
        user_id = "manually_unblocked"
        other_user_id = "other"

        # Create users and block one
        user_store = get_user_store()
        user_store.get_user(other_user_id)
        for _ in range(3):
            user_store.add_violation(user_id)

        # Verify user is blocked
        response = self.client.post(f"/chat/{user_id}", json={"message": "I'm blocked"})
        assert response.status_code == 403

        # Manually unblock
        response = self.client.put(f"/admin/unblock/{user_id}")
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["violation_count"] == 0
        assert response_data["is_blocked"] is False

        # User should be able to chat again
        with patch("src.api.chat.get_openai_client") as mock_openai:
            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat_completion = AsyncMock(return_value="Response")
            mock_openai.return_value = mock_openai_instance

            response = self.client.post(
                f"/chat/{user_id}", json={"message": "I can chat again"}
            )
            assert response.status_code == 200

    def test_blocked_user_with_new_violation_after_unblock(self):
        """Test that a user can be blocked again after being unblocked."""
        user_id = "repeat_offender"
        other_user_id = "victim"

        # Create users
        user_store = get_user_store()
        user_store.get_user(other_user_id)

        # First blocking cycle
        for _ in range(3):
            user_store.add_violation(user_id)

        # Unblock manually
        response = self.client.put(f"/admin/unblock/{user_id}")
        assert response.status_code == 200

        # User can violate again and get blocked after 3 strikes
        with patch("src.api.chat.get_openai_client") as mock_openai:
            mock_openai_instance = AsyncMock()
            mock_openai_instance.chat_completion = AsyncMock(return_value="Response")
            mock_openai.return_value = mock_openai_instance

            # Three more violations
            for i in range(3):
                response = self.client.post(
                    f"/chat/{user_id}",
                    json={"message": f"Violation {i+1} mentioning {other_user_id}"},
                )
                assert response.status_code == 200

            # Should be blocked again
            response = self.client.post(
                f"/chat/{user_id}", json={"message": "Blocked again"}
            )
            assert response.status_code == 403

    def test_unblock_nonexistent_user(self):
        """Test unblocking a user that doesn't exist."""
        response = self.client.put("/admin/unblock/nonexistent_user")
        assert response.status_code == 404
        response_data = response.json()
        assert response_data["detail"]["code"] == "USER_NOT_FOUND"

    def test_blocking_persists_across_requests(self):
        """Test that blocking state persists across multiple requests."""
        user_id = "persistent_block"
        other_user_id = "other"

        # Create users and block one
        user_store = get_user_store()
        user_store.get_user(other_user_id)
        for _ in range(3):
            user_store.add_violation(user_id)

        # Multiple requests should all be blocked
        for _ in range(5):
            response = self.client.post(
                f"/chat/{user_id}", json={"message": "Still blocked"}
            )
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "USER_BLOCKED"
