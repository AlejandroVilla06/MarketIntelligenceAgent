"""
Supabase client singleton for the FastAPI app.
Initialized in lifespan, shared across requests.
"""
from __future__ import annotations
from supabase import create_client, Client
from src.config import settings

_client: Client | None = None


def get_supabase_client() -> Client:
    """Get the Supabase client singleton.

    The client is created on first call (lazy init).
    FastAPI lifespan calls init_supabase() to pre-init.
    """
    global _client
    if _client is None:
        _client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )
    return _client


def init_supabase() -> None:
    """Pre-initialize Supabase client (called from lifespan)."""
    global _client
    if _client is None:
        _client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )


def close_supabase() -> None:
    """Close Supabase client (called from lifespan shutdown)."""
    global _client
    if _client:
        _client = None
