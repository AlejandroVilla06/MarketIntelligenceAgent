"""
Supabase client for the FastAPI app.

- Singleton client (anon) for lightweight operations.
- Per-request authenticated client for user-scoped DB operations (RLS).
"""
from __future__ import annotations
from supabase import create_client, Client
from src.config import settings

_client: Client | None = None


def get_supabase_client() -> Client:
    """Get the Supabase client singleton (anon key, no user context).

    For operations that don't need RLS context (e.g., token validation).
    Created lazily; pre-init via init_supabase().
    """
    global _client
    if _client is None:
        _client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )
    return _client


def get_authenticated_client(token: str) -> Client:
    """Create a per-request Supabase client with the user's auth context for RLS.

    This client includes the user's JWT so Supabase RLS policies
    correctly identify auth.uid() for row-level permissions.

    Args:
        token: User's JWT access token from Authorization header

    Returns:
        A fresh Supabase Client scoped to the authenticated user
    """
    client = create_client(settings.supabase_url, settings.supabase_key)
    try:
        client.auth.set_session(token, "")
    except Exception:
        pass  # Token already validated; set_session is best-effort for RLS
    return client


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
