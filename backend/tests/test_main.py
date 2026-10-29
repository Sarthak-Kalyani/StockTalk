"""
Core smoke tests for the StockTalk backend.

Milestone 1 exit criteria:
- /health and / return 200
- App starts and is callable
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "stocktalk-backend"


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "StockTalk" in response.json()["message"]
    assert response.json()["version"] == "1.0.0"
