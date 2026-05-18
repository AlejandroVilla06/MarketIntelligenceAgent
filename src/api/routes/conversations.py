"""Conversation CRUD endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from src.api.auth.jwt_validator import get_current_user
from src.api.deps import get_conversations
from src.api.state import SupabaseConversationStore
from src.utils import get_logger

router = APIRouter(tags=["conversations"])
log = get_logger("api.routes.conversations")


class RenameRequest(BaseModel):
    title: str


@router.post("/conversations")
async def create_conversation(
    user: dict = Depends(get_current_user),
    store: SupabaseConversationStore = Depends(get_conversations),
):
    try:
        conv = await store.create()
        return {"id": conv["id"], "messages": []}
    except Exception as e:
        log.error(f"Create conversation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation.")


@router.get("/conversations")
async def list_conversations(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    store: SupabaseConversationStore = Depends(get_conversations),
):
    """List conversations for the authenticated user."""
    try:
        return await store.list(offset=offset, limit=limit)
    except Exception as e:
        log.error(f"List conversations failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to load conversations.")


@router.get("/conversations/{cid}")
async def get_conversation(
    cid: str,
    user: dict = Depends(get_current_user),
    store: SupabaseConversationStore = Depends(get_conversations),
):
    try:
        conv = await store.get(cid)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conv
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Get conversation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to load conversation.")


@router.put("/conversations/{cid}")
async def rename_conversation(
    cid: str,
    body: RenameRequest,
    user: dict = Depends(get_current_user),
    store: SupabaseConversationStore = Depends(get_conversations),
):
    """Rename a conversation."""
    try:
        if not await store.rename(cid, body.title):
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"renamed": True, "title": body.title}
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Rename conversation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to rename conversation.")


@router.delete("/conversations/{cid}")
async def delete_conversation(
    cid: str,
    user: dict = Depends(get_current_user),
    store: SupabaseConversationStore = Depends(get_conversations),
):
    try:
        if not await store.delete(cid):
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Delete conversation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation.")
