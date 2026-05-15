"""
JWT Validation — Validates tokens against Supabase Auth API.
Uses Supabase client for robust validation (handles both HS256 and RS256).
"""
from __future__ import annotations
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.api.auth.supabase_client import get_supabase_client
from src.utils import get_logger

security = HTTPBearer()
log = get_logger("api.auth.jwt_validator")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate JWT using Supabase Auth API and return user claims.

    Calls supabase.auth.get_user() to validate the token.
    This is more reliable than local JWT decoding since it handles
    both HS256 and RS256 signed tokens automatically.

    Returns:
        dict with user claims (sub=user_id, email, aud, exp)

    Raises:
        HTTPException 401 if token is invalid, expired, or missing
    """
    token = credentials.credentials
    try:
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        if not user:
            raise ValueError("No user data returned")
        return {
            "sub": user.id,
            "email": user.email,
            "aud": "authenticated",
        }
    except Exception as e:
        log.warning(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
