"""
Supabase-backed conversation store.
Replaces the in-memory ConversationStore with persistent PostgreSQL storage.
All DB calls are wrapped in asyncio.to_thread() to prevent event loop blocking.

Supabase RLS ensures user isolation at the database level.

Previous implementation (in-memory) is preserved in git history at
  5901ff1375b587b4954b92103aaae26253f2f187^:src/api/state.py
"""
from __future__ import annotations

import asyncio
from collections import Counter
from typing import Any

from src.utils import get_logger

log = get_logger("api.state")


class SupabaseConversationStore:
    """Persistent conversation store backed by Supabase PostgreSQL.

    Each instance is scoped to a single user. Created per-request via DI.
    All database operations use asyncio.to_thread() for non-blocking execution.

    Usage:
        store = SupabaseConversationStore(supabase_client, user_id="uuid")
        conv = await store.create()
        await store.add_message(conv["id"], "user", "Hello")
        messages = await store.get(conv["id"])
    """

    def __init__(self, supabase: Any, user_id: str) -> None:
        self._supabase = supabase
        self._user_id = user_id

    async def create(self, title: str = "Nueva conversación") -> dict:
        """Create a new conversation for the authenticated user."""
        result = await asyncio.to_thread(
            self._supabase.table("conversations").insert({
                "user_id": self._user_id,
                "title": title,
            }).execute
        )
        conv = result.data[0]
        conv["messages"] = []
        return conv

    async def get(self, cid: str) -> dict | None:
        """Get a conversation with all messages (scoped to user)."""
        result = await asyncio.to_thread(
            self._supabase.table("conversations")
                .select("*")
                .eq("id", cid)
                .eq("user_id", self._user_id)
                .execute
        )
        if not result.data:
            return None

        conv = result.data[0]
        messages = await asyncio.to_thread(
            self._supabase.table("messages")
                .select("*")
                .eq("conversation_id", cid)
                .order("created_at")
                .execute
        )
        conv["messages"] = messages.data or []
        return conv

    async def delete(self, cid: str) -> bool:
        """Delete a conversation (cascades to messages)."""
        result = await asyncio.to_thread(
            self._supabase.table("conversations")
                .delete()
                .eq("id", cid)
                .eq("user_id", self._user_id)
                .execute
        )
        return len(result.data) > 0

    async def list(self, offset: int = 0, limit: int = 20) -> list[dict]:
        """List conversations for the authenticated user with message counts — single pass."""
        result = await asyncio.to_thread(
            self._supabase.table("conversations")
                .select("id, title, created_at, updated_at")
                .eq("user_id", self._user_id)
                .order("updated_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute
        )

        convs = result.data or []
        if not convs:
            return convs

        # Get ALL message counts in ONE additional query, not N queries
        conv_ids = [c["id"] for c in convs]
        msg_result = await asyncio.to_thread(
            self._supabase.table("messages")
                .select("conversation_id", count="exact")
                .in_("conversation_id", conv_ids)
                .execute
        )

        # PostgREST `count` returns total rows before filter, not grouped counts.
        # So we count locally from the returned data.
        counts: Counter[str] = Counter()
        for msg in msg_result.data or []:
            counts[msg["conversation_id"]] += 1

        for conv in convs:
            conv["message_count"] = counts.get(conv["id"], 0)

        return convs

    async def add_message(self, cid: str, role: str, content: str) -> bool:
        """Add a message to a conversation.

        If this is the first user message, auto-update the conversation title.
        """
        result = await asyncio.to_thread(
            self._supabase.table("messages").insert({
                "conversation_id": cid,
                "role": role,
                "content": content,
            }).execute
        )

        if not result.data:
            return False

        # Auto-title: first user message becomes conversation title
        if role == "user":
            conv = await self.get(cid)
            if conv and conv.get("title") in ("Nueva conversación", "Chat"):
                new_title = (content[:42] + "…") if len(content) > 42 else content
                await asyncio.to_thread(
                    self._supabase.table("conversations")
                        .update({"title": new_title})
                        .eq("id", cid)
                        .execute
                )

        return True

    @property
    def user_id(self) -> str:
        """The authenticated user this store is scoped to."""
        return self._user_id
