"""Tests for the main FastAPI application."""

from fastapi.testclient import TestClient

from src.main import create_app


class TestApp:
    """Test cases for the main FastAPI application."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_app_creation(self):
        """Test that the app is created successfully."""
        assert self.app is not None
        assert self.app.title == "Chat Gateway"
        assert (
            self.app.description
            == "An intelligent chat gateway with content moderation and blocking"
        )
        assert self.app.version == "0.1.0"

    def test_health_check_via_docs(self):
        """Test that the app serves OpenAPI docs."""
        response = self.client.get("/docs")
        assert response.status_code == 200

    def test_openapi_spec(self):
        """Test that OpenAPI spec is available."""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200

        spec = response.json()
        assert spec["info"]["title"] == "Chat Gateway"
        assert "/chat/{user_id}" in spec["paths"]
        assert "/admin/unblock/{user_id}" in spec["paths"]
