"""
Integration tests for API with mocked orchestrator.

The orchestrator is mocked globally via conftest.py — see that file
for the rationale.
Auth is provided via TEST_TOKEN from conftest.py.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from src.api.app import create_app
from tests.conftest import TEST_TOKEN

client = TestClient(create_app())

_AUTH = {"Authorization": f"Bearer {TEST_TOKEN}"}


def test_concurrent_conversations():
    """Multiple conversations should have independent IDs."""
    c1 = client.post("/api/conversations", headers=_AUTH).json()
    c2 = client.post("/api/conversations", headers=_AUTH).json()
    assert c1["id"] != c2["id"]


def test_conversation_persists_messages():
    """Messages added to a conversation should be retrievable."""
    # Create conversation
    conv = client.post("/api/conversations", headers=_AUTH).json()
    cid = conv["id"]

    # Send chat message
    chat_resp = client.post("/api/chat", json={
        "query": "test",
        "conversation_id": cid,
    }, headers=_AUTH)
    assert chat_resp.status_code == 200

    # Get conversation and verify messages
    get_resp = client.get(f"/api/conversations/{cid}", headers=_AUTH)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert len(data["messages"]) == 2  # user + assistant
