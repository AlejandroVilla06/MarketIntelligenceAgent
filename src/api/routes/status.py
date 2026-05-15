"""Orchestrator status endpoint."""
from __future__ import annotations
import asyncio
from fastapi import APIRouter, Depends
from src.agents.orchestrator import MarketOrchestrator
from src.api.auth.jwt_validator import get_current_user
from src.api.deps import get_orchestrator
from src.api.schemas.status import StatusResponse

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def get_status(
    user: dict = Depends(get_current_user),
    orch: MarketOrchestrator = Depends(get_orchestrator),
):
    """Get orchestrator initialization status and document counts."""
    status = await asyncio.to_thread(orch.get_status)
    return StatusResponse(**status)
