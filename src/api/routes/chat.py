"""Chat endpoint — single Q&A and SSE streaming."""
from __future__ import annotations
import asyncio
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse
from src.agents.orchestrator import MarketOrchestrator
from src.api.auth.jwt_validator import get_current_user
from src.api.deps import get_orchestrator, get_conversations
from src.api.schemas.chat import ChatRequest, ChatResponse
from src.api.state import SupabaseConversationStore
from src.utils import get_logger

router = APIRouter(tags=["chat"])
log = get_logger("api.routes.chat")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
    orch: MarketOrchestrator = Depends(get_orchestrator),
    store: SupabaseConversationStore = Depends(get_conversations),
):
    """Single Q&A: send query, get response."""
    # Get or create conversation
    conv = await store.get(request.conversation_id) if request.conversation_id else None
    if request.conversation_id and not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not conv:
        conv = await store.create()

    # Add user message
    await store.add_message(conv["id"], "user", request.query)

    # Build history from previous messages (exclude current user message)
    history = [{"role": m["role"], "content": m["content"]} for m in conv["messages"][:-1]]

    # Get agent response
    try:
        response = await asyncio.to_thread(orch.ask, request.query, history)
    except Exception as e:
        log.error(f"Orchestrator ask failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Add assistant message
    await store.add_message(conv["id"], "assistant", response)

    return ChatResponse(response=response, conversation_id=conv["id"])


@router.get("/chat/stream")
async def chat_stream(
    query: str = Query(..., min_length=1),
    conversation_id: str | None = None,
    user: dict = Depends(get_current_user),
    orch: MarketOrchestrator = Depends(get_orchestrator),
    store: SupabaseConversationStore = Depends(get_conversations),
):
    """SSE streaming chat endpoint with REAL LLM streaming."""
    # Get or create conversation
    conv = await store.get(conversation_id) if conversation_id else None
    if conversation_id and not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not conv:
        conv = await store.create()

    await store.add_message(conv["id"], "user", query)

    # Build history from previous messages
    history = [{"role": m["role"], "content": m["content"]} for m in conv["messages"][:-1]]

    async def event_generator():
        full_response = ""
        try:
            async for token in orch.ask_stream(query, history):
                full_response += token
                yield {"data": json.dumps({"token": token})}

            await store.add_message(conv["id"], "assistant", full_response)
            yield {"data": json.dumps({"done": True})}

        except Exception as e:
            log.error(f"Stream failed: {e}")
            yield {"data": json.dumps({"error": str(e)})}
            yield {"data": json.dumps({"done": True})}

    return EventSourceResponse(event_generator())


@router.post("/reset")
async def reset_orchestrator(
    user: dict = Depends(get_current_user),
    orch: MarketOrchestrator = Depends(get_orchestrator),
):
    """Reset orchestrator (clear ChromaDB and re-index)."""
    try:
        await asyncio.to_thread(orch.reset)
        await asyncio.to_thread(orch.setup)
        return {"message": "Orchestrator reset successfully"}
    except Exception as e:
        log.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
