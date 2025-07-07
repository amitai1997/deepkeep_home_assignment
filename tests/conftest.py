"""Test configuration and fixtures."""

import os
import pytest
from unittest.mock import patch

# Set dummy environment variables for testing
os.environ.setdefault("OPENAI_API_KEY", "test-key-dummy")


@pytest.fixture
def mock_settings():
    """Mock settings for testing without requiring real environment variables."""
    from src.core.config import Settings
    
    with patch('src.core.config.get_settings') as mock_get_settings:
        mock_settings = Settings(
            openai_api_key="test-key-dummy",
            block_minutes=60 * 24
        )
        mock_get_settings.return_value = mock_settings
        yield mock_settings


@pytest.fixture
def fresh_user_store():
    """Provide a fresh UserStore instance for each test."""
    from src.store.user_store import UserStore
    return UserStore()


@pytest.fixture
def mock_openai_key():
    """Set mock OpenAI API key for tests.""" 
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-dummy"}):
        yield
