"""Conversation CRUD endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.auth.jwt_validator import get_current_user
from src.api.deps import get_conversations
from src.api.schemas.chat import ConversationListItem
from src.api.state import SupabaseConversationStore

router = APIRouter(tags=["conversations"])


@router.post("/conversations")
async def create_conversation(
    user: dict = Depends(get_current_user),
    store: SupabaseConversationStore = Depends(get_conversations),
):
    conv = await store.create()
    return {"id": conv["id"], "messages": []}


@router.get("/conversations")
async def list_conversations(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    store: SupabaseConversationStore = Depends(get_conversations),
):
    """List conversations for the authenticated user."""
    return await store.list(offset=offset, limit=limit)


@router.get("/conversations/{cid}")
async def get_conversation(
    cid: str,
    user: dict = Depends(get_current_user),
    store: SupabaseConversationStore = Depends(get_conversations),
):
    conv = await store.get(cid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/conversations/{cid}")
async def delete_conversation(
    cid: str,
    user: dict = Depends(get_current_user),
    store: SupabaseConversationStore = Depends(get_conversations),
):
    if not await store.delete(cid):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True}
