from __future__ import annotations
from pydantic import BaseModel


class StatusResponse(BaseModel):
    is_setup: bool
    retriever_initialized: bool
    agent_initialized: bool
    counts: dict | None = None
