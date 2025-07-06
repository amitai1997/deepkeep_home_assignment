import sys
from pathlib import Path

import os

os.environ.setdefault("OPENAI_API_KEY", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fastapi.testclient import TestClient
from src.main import app


def test_app_startup() -> None:
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200
