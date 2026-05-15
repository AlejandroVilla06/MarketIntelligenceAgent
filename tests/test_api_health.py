"""Tests for GET /api/health endpoint."""
from __future__ import annotations

from fastapi.testclient import TestClient
from src.api.app import create_app

client = TestClient(create_app())


def test_health_returns_ok():
    """Health endpoint returns 200 with status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
