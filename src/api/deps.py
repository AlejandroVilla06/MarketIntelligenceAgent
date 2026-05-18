"""
Dependency Injection for FastAPI
- Orchestrator singleton: initialized in lifespan, shared across requests
- Conversation store: per-user Supabase-backed store with DI
"""
from __future__ import annotations
import asyncio

from fastapi import Depends

from src.market_orchestrator.orchestrator import MarketOrchestrator
from src.api.auth.supabase_client import get_authenticated_client
from src.api.auth.jwt_validator import get_current_user
from src.api.state import SupabaseConversationStore
from src.utils import get_logger

log = get_logger("api.deps")

_orchestrator: MarketOrchestrator | None = None
_orchestrator_lock = asyncio.Lock()


async def init_orchestrator() -> None:
    global _orchestrator
    async with _orchestrator_lock:
        if _orchestrator is None:
            log.info("Initializing orchestrator (lifespan)...")
            orch = MarketOrchestrator()
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(orch.setup),
                    timeout=30.0,
                )
                _orchestrator = orch
                log.info("Orchestrator initialized successfully")
            except Exception as e:
                log.warning("Orchestrator init failed (will retry on first request): {}", e)
                # Don't set _orchestrator — next get_orchestrator() will retry


async def shutdown_orchestrator() -> None:
    global _orchestrator
    log.info("Shutting down orchestrator...")
    _orchestrator = None


async def get_orchestrator() -> MarketOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        await init_orchestrator()
    if _orchestrator is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Orchestrator not initialized. Check server dependencies.")
    return _orchestrator


async def get_conversations(
    user: dict = Depends(get_current_user),
) -> SupabaseConversationStore:
    """Dependency: creates a Supabase-backed conversation store scoped to the current user."""
    token = user.get("_token", "")
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Missing authentication token.")
    try:
        supabase = get_authenticated_client(token)
    except Exception as e:
        log.error("Failed to create Supabase client: {}", e)
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database unavailable. Check Supabase credentials.")
    user_id = user.get("sub", "")
    return SupabaseConversationStore(supabase, user_id)
