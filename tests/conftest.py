"""
Shared pytest configuration — patches heavy orchestrator dependency and
Supabase auth client. Also creates a valid JWT test token.

Without these patches:
- Importing create_app triggers src.api.routes.chat → src.api.deps.get_orchestrator
  → init_orchestrator() → MarketOrchestrator.setup() → sentence_transformers
  import (not available in test env).
- Auth endpoints would try to call real Supabase API.

The patch is applied at module level (BEFORE any test files import create_app)
so that the route modules capture the mocked version in their local namespace.

autospec=True preserves the original function signature, preventing FastAPI
from misinterpreting the MagicMock/AysncMock's flexible *args/**kwargs as
query parameters.
"""
from __future__ import annotations
import time
from unittest.mock import MagicMock, patch

import jwt as pyjwt

from src.config import settings

# =============================================================================
# Orchestrator mock — avoids importing sentence_transformers / heavy setup()
# =============================================================================
_patcher = patch("src.api.deps.get_orchestrator", autospec=True)
_mock_get_orch = _patcher.start()
_mock_orch = MagicMock()
_mock_orch.ask.return_value = "Mock assistant response"
_mock_get_orch.return_value = _mock_orch

# =============================================================================
# Supabase client mock — avoids calling real Supabase API
# =============================================================================

# ---------------------------------------------------------------------------
# Profiles table mock (used by auth/profile endpoints)
# ---------------------------------------------------------------------------
mock_profiles_table = MagicMock()
mock_profiles_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
    data=[{
        "id": "test-user-id",
        "email": "test@example.com",
        "full_name": None,
        "avatar_url": None,
        "preferred_language": "es",
        "preferred_theme": "dark",
    }],
)

# ---------------------------------------------------------------------------
# Conversations table mock (used by SupabaseConversationStore)
# ---------------------------------------------------------------------------
mock_conversations_table = MagicMock()

# Track conversation id for conditional get()/delete() behavior
_get_cid_tracker: dict[str, str | None] = {"id": None}

# chain: insert({...}).execute -> returns new conversation data (infinite generator)
_conv_ins_counter: list[int] = [0]


def _insert_execute_side_effect() -> MagicMock:
    _conv_ins_counter[0] += 1
    cid = f"conv-{_conv_ins_counter[0]:04d}"
    return MagicMock(data=[{
        "id": cid, "user_id": "test-user-id", "title": "Nueva conversación",
        "messages": [], "created_at": "2025-01-01T00:00:00", "updated_at": "2025-01-01T00:00:00",
    }])


mock_conversations_table.insert.return_value.execute.side_effect = _insert_execute_side_effect

# -- store.get() chain: select(...).eq("id", cid).eq("user_id", uid).execute --
# Track the first .eq() arg so execute can decide return data
_first_eq_return = mock_conversations_table.select.return_value.eq.return_value
mock_conversations_table.select.return_value.eq.side_effect = lambda col, val: (
    _get_cid_tracker.__setitem__("id", val) if col == "id" else None,
    _first_eq_return,
)[1]

# execute returns empty data for "nonexistent", real data otherwise
mock_conversations_table.select.return_value.eq.return_value.eq.return_value.execute.side_effect = lambda: (
    MagicMock(data=[])
    if _get_cid_tracker.get("id") == "nonexistent"
    else MagicMock(data=[{
        "id": _get_cid_tracker.get("id", "conv-0001"),
        "user_id": "test-user-id", "title": "Nueva conversación",
        "created_at": "2025-01-01T00:00:00", "updated_at": "2025-01-01T00:00:00",
    }])
)

# -- store.list() chain: select(...).eq("user_id", uid).order(...).range(0,19).execute --
# (range added for pagination support)
mock_conversations_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = MagicMock(
    data=[{
        "id": "conv-0001", "user_id": "test-user-id", "title": "Test",
        "created_at": "2025-01-01T00:00:00", "updated_at": "2025-01-01T00:00:00",
    }],
)

# -- get_recent_history() chain: select(...).eq(...).order(...).limit(...).execute --
mock_conversations_table.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
    data=[{
        "id": "conv-0001", "user_id": "test-user-id", "title": "Test",
        "created_at": "2025-01-01T00:00:00", "updated_at": "2025-01-01T00:00:00",
    }],
)

# -- store.delete() chain: delete().eq("id", cid).eq("user_id", uid).execute --
_del_first_eq_return = mock_conversations_table.delete.return_value.eq.return_value
mock_conversations_table.delete.return_value.eq.side_effect = lambda col, val: (
    _get_cid_tracker.__setitem__("id", val) if col == "id" else None,
    _del_first_eq_return,
)[1]

mock_conversations_table.delete.return_value.eq.return_value.eq.return_value.execute.side_effect = lambda: (
    MagicMock(data=[])
    if _get_cid_tracker.get("id") == "nonexistent"
    else MagicMock(data=[{"id": _get_cid_tracker.get("id", "conv-0001")}])
)

# -- auto-title chain: update({...}).eq("id", cid).execute --
mock_conversations_table.update.return_value.eq.return_value.execute.return_value = MagicMock(
    data=[{"id": "conv-0001"}],
)

# ---------------------------------------------------------------------------
# Messages table mock (used by SupabaseConversationStore)
# ---------------------------------------------------------------------------
mock_messages_table = MagicMock()

# chain: insert({...}).execute                                     (add_message)
mock_messages_table.insert.return_value.execute.return_value = MagicMock(
    data=[{"id": "msg-1", "conversation_id": "conv-0001", "role": "user", "content": "test"}],
)

# chain: select("*").eq("conversation_id", cid).order("created_at").execute  (get messages)
mock_messages_table.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
    data=[
        {"id": "msg-u1", "conversation_id": "conv-0001", "role": "user", "content": "test",
         "created_at": "2025-01-01T00:00:00"},
        {"id": "msg-a1", "conversation_id": "conv-0001", "role": "assistant",
         "content": "Mock assistant response", "created_at": "2025-01-01T00:00:01"},
    ],
)

# chain: select("id", count="exact").eq("conversation_id", cid).execute  (list count - O(N) path)
mock_messages_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
    data=[],
    count=2,
)

# chain: select("conversation_id", count="exact").in_("conversation_id", ids).execute  (list count - O(1) path)
mock_messages_table.select.return_value.in_.return_value.execute.return_value = MagicMock(
    data=[
        {"conversation_id": "conv-0001", "id": "msg-1"},
        {"conversation_id": "conv-0001", "id": "msg-2"},
    ],
)

# ---------------------------------------------------------------------------
# Main Supabase mock — routes table(name) to the correct mock
# ---------------------------------------------------------------------------
mock_supabase = MagicMock()
mock_supabase.auth.sign_up.return_value = MagicMock(
    user=MagicMock(id="test-user-id"),
    session=MagicMock(access_token="test-access-token"),
)
mock_supabase.auth.sign_in_with_password.return_value = MagicMock(
    user=MagicMock(id="test-user-id", email="test@example.com"),
    session=MagicMock(
        access_token="test-access-token",
        refresh_token="test-refresh-token",
    ),
)
mock_supabase.auth.sign_in_with_oauth.return_value = MagicMock(
    url="https://example.com/oauth/callback",
)
mock_supabase.auth.exchange_code_for_session.return_value = MagicMock(
    user=MagicMock(id="test-user-id"),
    session=MagicMock(
        access_token="test-access-token",
        refresh_token="test-refresh-token",
    ),
)
mock_supabase.auth.refresh_session.return_value = MagicMock(
    session=MagicMock(
        access_token="new-access-token",
        refresh_token="new-refresh-token",
    ),
)

# Route auth.get_user — used by jwt_validator.get_current_user
mock_supabase.auth.get_user.return_value = MagicMock(
    user=MagicMock(id="test-user-id", email="test@example.com"),
)

# Route .table(name) to correct table mock
mock_supabase.table.side_effect = lambda name: {
    "profiles": mock_profiles_table,
    "conversations": mock_conversations_table,
    "messages": mock_messages_table,
}.get(name, MagicMock())

# Patch get_supabase_client() to return our mock_supabase
_patch_supabase = patch(
    "src.api.auth.supabase_client.get_supabase_client",
    autospec=True,
)
_mock_get_supabase = _patch_supabase.start()
_mock_get_supabase.return_value = mock_supabase

# Force-patch at jwt_validator and deps levels too (handles import-order edge cases)
_patch_jwt = patch("src.api.auth.jwt_validator.get_supabase_client", return_value=mock_supabase)
_patch_jwt.start()
_patch_deps = patch("src.api.deps.get_supabase_client", return_value=mock_supabase)
_patch_deps.start()

# =============================================================================
# Valid JWT test token — signed with the real JWT secret
# Tests that need to authenticate can use this token.
# =============================================================================
TEST_USER_ID = "test-user-id"
TEST_EMAIL = "test@example.com"
TEST_TOKEN: str = pyjwt.encode(
    {
        "sub": TEST_USER_ID,
        "email": TEST_EMAIL,
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    },
    settings.supabase_jwt_secret,
    algorithm="HS256",
)
