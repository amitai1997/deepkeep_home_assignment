"""Tests for chat API endpoints."""

from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import httpx

from src.main import create_app


class TestChatAPI:
    """Test cases for chat API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_chat_endpoint_success(self):
        """Test successful chat endpoint call."""
        user_id = "test_user"
        message = "Hello world"
        expected_response = "Hello! How can I help you?"

        # Mock the moderation service and OpenAI client
        with (
            patch("src.api.chat.get_moderation_service") as mock_moderation,
            patch("src.api.chat.get_openai_client") as mock_openai,
        ):

            # Setup mocks
            mock_moderation_instance = Mock()
            mock_moderation_instance.process_message.return_value = (
                False,
                False,
            )  # No violation, not blocked
            mock_moderation.return_value = mock_moderation_instance

            mock_openai_instance = Mock()
            mock_openai_instance.chat_completion = AsyncMock(
                return_value=expected_response
            )
            mock_openai.return_value = mock_openai_instance

            # Make request
            response = self.client.post(f"/chat/{user_id}", json={"message": message})

            # Assertions
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["response"] == expected_response
            assert response_data["user_id"] == user_id

            # Verify mocks were called
            mock_moderation_instance.process_message.assert_called_once_with(
                message, user_id
            )
            mock_openai_instance.chat_completion.assert_called_once_with(message)

    def test_chat_endpoint_user_blocked(self):
        """Test chat endpoint when user is blocked."""
        user_id = "blocked_user"
        message = "Hello world"

        # Mock the moderation service to return blocked status
        with patch("src.api.chat.get_moderation_service") as mock_moderation:
            mock_moderation_instance = Mock()
            mock_moderation_instance.process_message.return_value = (
                False,
                True,
            )  # Not violation this time, but blocked
            mock_moderation.return_value = mock_moderation_instance

            # Make request
            response = self.client.post(f"/chat/{user_id}", json={"message": message})

            # Assertions
            assert response.status_code == 403
            response_data = response.json()
            assert "User is blocked" in response_data["detail"]["error"]
            assert response_data["detail"]["code"] == "USER_BLOCKED"

    def test_chat_endpoint_with_violation_but_not_blocked(self):
        """Test chat endpoint with violation detected but user not blocked yet."""
        user_id = "test_user"
        message = "Hello user2"
        expected_response = "Hello! How can I help you?"

        # Mock the moderation service and OpenAI client
        with (
            patch("src.api.chat.get_moderation_service") as mock_moderation,
            patch("src.api.chat.get_openai_client") as mock_openai,
        ):

            # Setup mocks
            mock_moderation_instance = Mock()
            mock_moderation_instance.process_message.return_value = (
                True,
                False,
            )  # Violation but not blocked
            mock_moderation.return_value = mock_moderation_instance

            mock_openai_instance = Mock()
            mock_openai_instance.chat_completion = AsyncMock(
                return_value=expected_response
            )
            mock_openai.return_value = mock_openai_instance

            # Make request
            response = self.client.post(f"/chat/{user_id}", json={"message": message})

            # Assertions - should still succeed even with violation
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["response"] == expected_response
            assert response_data["user_id"] == user_id

    def test_chat_endpoint_openai_error(self):
        """Test chat endpoint when OpenAI API fails."""
        user_id = "test_user"
        message = "Hello world"

        # Mock the moderation service and OpenAI client
        with (
            patch("src.api.chat.get_moderation_service") as mock_moderation,
            patch("src.api.chat.get_openai_client") as mock_openai,
        ):

            # Setup mocks
            mock_moderation_instance = Mock()
            mock_moderation_instance.process_message.return_value = (False, False)
            mock_moderation.return_value = mock_moderation_instance

            mock_openai_instance = Mock()
            mock_openai_instance.chat_completion = AsyncMock(
                side_effect=httpx.HTTPError("API Error")
            )
            mock_openai.return_value = mock_openai_instance

            # Make request
            response = self.client.post(f"/chat/{user_id}", json={"message": message})

            # Assertions
            assert response.status_code == 502
            response_data = response.json()
            assert "OpenAI service unavailable" in response_data["detail"]["error"]
            assert response_data["detail"]["code"] == "OPENAI_ERROR"

    def test_chat_endpoint_openai_invalid_response(self):
        """Test chat endpoint when OpenAI returns invalid response."""
        user_id = "test_user"
        message = "Hello world"

        # Mock the moderation service and OpenAI client
        with (
            patch("src.api.chat.get_moderation_service") as mock_moderation,
            patch("src.api.chat.get_openai_client") as mock_openai,
        ):

            # Setup mocks
            mock_moderation_instance = Mock()
            mock_moderation_instance.process_message.return_value = (False, False)
            mock_moderation.return_value = mock_moderation_instance

            mock_openai_instance = Mock()
            mock_openai_instance.chat_completion = AsyncMock(
                side_effect=ValueError("Invalid response")
            )
            mock_openai.return_value = mock_openai_instance

            # Make request
            response = self.client.post(f"/chat/{user_id}", json={"message": message})

            # Assertions
            assert response.status_code == 502
            response_data = response.json()
            assert "Invalid response from OpenAI" in response_data["detail"]["error"]
            assert response_data["detail"]["code"] == "OPENAI_RESPONSE_ERROR"

    def test_chat_endpoint_invalid_request(self):
        """Test chat endpoint with invalid request data."""
        user_id = "test_user"

        # Make request with missing message field
        response = self.client.post(f"/chat/{user_id}", json={})

        # Assertions
        assert response.status_code == 422  # Unprocessable Entity

    def test_chat_endpoint_empty_message(self):
        """Test chat endpoint with empty message."""
        user_id = "test_user"
        
        # Make request with empty message
        response = self.client.post(f"/chat/{user_id}", json={"message": ""})
        
        # Should still process (empty messages are technically valid)
        with (
            patch("src.api.chat.get_moderation_service") as mock_moderation,
            patch("src.api.chat.get_openai_client") as mock_openai,
        ):
            mock_moderation_instance = Mock()
            mock_moderation_instance.process_message.return_value = (False, False)
            mock_moderation.return_value = mock_moderation_instance
            
            mock_openai_instance = Mock()
            mock_openai_instance.chat_completion = AsyncMock(return_value="Response")
            mock_openai.return_value = mock_openai_instance
            
            response = self.client.post(f"/chat/{user_id}", json={"message": ""})
            assert response.status_code == 200

    def test_chat_endpoint_special_characters_in_user_id(self):
        """Test chat endpoint with special characters in user ID."""
        user_id = "user@example.com"
        message = "Hello world"
        
        with (
            patch("src.api.chat.get_moderation_service") as mock_moderation,
            patch("src.api.chat.get_openai_client") as mock_openai,
        ):
            mock_moderation_instance = Mock()
            mock_moderation_instance.process_message.return_value = (False, False)
            mock_moderation.return_value = mock_moderation_instance
            
            mock_openai_instance = Mock()
            mock_openai_instance.chat_completion = AsyncMock(return_value="Response")
            mock_openai.return_value = mock_openai_instance
            
            response = self.client.post(f"/chat/{user_id}", json={"message": message})
            assert response.status_code == 200

    def test_chat_endpoint_very_long_message(self):
        """Test chat endpoint with very long message."""
        user_id = "test_user"
        message = "x" * 10000  # 10k character message
        
        with (
            patch("src.api.chat.get_moderation_service") as mock_moderation,
            patch("src.api.chat.get_openai_client") as mock_openai,
        ):
            mock_moderation_instance = Mock()
            mock_moderation_instance.process_message.return_value = (False, False)
            mock_moderation.return_value = mock_moderation_instance
            
            mock_openai_instance = Mock()
            mock_openai_instance.chat_completion = AsyncMock(return_value="Response")
            mock_openai.return_value = mock_openai_instance
            
            response = self.client.post(f"/chat/{user_id}", json={"message": message})
            assert response.status_code == 200

    def test_chat_endpoint_concurrent_violations(self):
        """Test handling of concurrent violations from same user."""
        user_id = "concurrent_violator"
        message = "Hello user2"
        
        with (
            patch("src.api.chat.get_moderation_service") as mock_moderation,
            patch("src.api.chat.get_openai_client") as mock_openai,
        ):
            # Setup mocks to simulate concurrent violations
            mock_moderation_instance = Mock()
            # First two calls return violation but not blocked
            # Third call returns violation and blocked
            mock_moderation_instance.process_message.side_effect = [
                (True, False),  # First violation
                (True, False),  # Second violation
                (True, True),   # Third violation - blocked
            ]
            mock_moderation.return_value = mock_moderation_instance
            
            mock_openai_instance = Mock()
            mock_openai_instance.chat_completion = AsyncMock(return_value="Response")
            mock_openai.return_value = mock_openai_instance
            
            # Make three requests
            for i in range(2):
                response = self.client.post(f"/chat/{user_id}", json={"message": message})
                assert response.status_code == 200
            
            # Third request should be allowed but user becomes blocked
            response = self.client.post(f"/chat/{user_id}", json={"message": message})
            assert response.status_code == 200
