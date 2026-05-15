"""
User profile service — CRUD operations on Supabase profiles table.
"""
from __future__ import annotations
from supabase import Client
from src.api.schemas.auth import UserProfile, UserProfileUpdate


def get_profile(supabase: Client, user_id: str) -> UserProfile | None:
    """Get user profile by ID from Supabase profiles table."""
    result = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if not result.data:
        return None
    return UserProfile(**result.data[0])


def update_profile(supabase: Client, user_id: str, update: UserProfileUpdate) -> UserProfile | None:
    """Update user profile fields."""
    data = update.model_dump(exclude_none=True)
    if not data:
        return get_profile(supabase, user_id)

    data["updated_at"] = "now()"
    result = supabase.table("profiles").update(data).eq("id", user_id).execute()
    if not result.data:
        return None
    return UserProfile(**result.data[0])
