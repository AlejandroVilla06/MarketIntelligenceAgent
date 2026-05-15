"""Tests for Conversation CRUD endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient
from src.api.app import create_app
from tests.conftest import TEST_TOKEN

client = TestClient(create_app())

_AUTH = {"Authorization": f"Bearer {TEST_TOKEN}"}


def test_create_conversation():
    """POST /api/conversations returns a new conversation with id and messages."""
    response = client.post("/api/conversations", headers=_AUTH)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "messages" in data


def test_list_conversations():
    """GET /api/conversations returns a list of conversations."""
    # Create one first so the list is non-empty
    client.post("/api/conversations", headers=_AUTH)
    response = client.get("/api/conversations", headers=_AUTH)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_conversation_not_found():
    """GET /api/conversations/<invalid> returns 404."""
    response = client.get("/api/conversations/nonexistent", headers=_AUTH)
    assert response.status_code == 404


def test_delete_conversation_not_found():
    """DELETE /api/conversations/<invalid> returns 404."""
    response = client.delete("/api/conversations/nonexistent", headers=_AUTH)
    assert response.status_code == 404
