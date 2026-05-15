"""
Tests for chat endpoints with mocked orchestrator.

The orchestrator is mocked globally via conftest.py to avoid importing
sentence_transformers and triggering heavy setup().
Auth is provided via TEST_TOKEN from conftest.py.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from src.api.app import create_app
from tests.conftest import TEST_TOKEN

client = TestClient(create_app())

_AUTH = {"Authorization": f"Bearer {TEST_TOKEN}"}


def test_chat_requires_query():
    """POST /api/chat with empty body returns 422 (query is required)."""
    response = client.post("/api/chat", json={}, headers=_AUTH)
    assert response.status_code == 422


def test_chat_returns_response():
    """POST /api/chat with valid query returns response and conversation_id."""
    response = client.post("/api/chat", json={"query": "test query"}, headers=_AUTH)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "conversation_id" in data
