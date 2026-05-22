"""
JWT Validation — Validates tokens against Supabase Auth API.

Two methods:
1. Fast path: local JWT decoding with PyJWT using SUPABASE_JWT_SECRET (HS256).
2. Fallback: call supabase.auth.get_user() API (handles RS256 tokens too).

The fast path is used when SUPABASE_JWT_SECRET is configured in .env.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.api.auth.supabase_client import get_supabase_client
from src.config import settings
from src.utils import get_logger

security = HTTPBearer()
log = get_logger("api.auth.jwt_validator")


def _decode_local(token: str) -> dict | None:
    """Try to decode JWT locally using SUPABASE_JWT_SECRET (fast, no network).

    Returns user claims dict or None if:
    - SUPABASE_JWT_SECRET is not configured
    - Token is expired
    - Signature is invalid
    """
    secret = settings.supabase_jwt_secret
    if not secret:
        return None

    try:
        import jwt as pyjwt

        payload = pyjwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["exp", "sub"]},
        )
        log.debug("JWT validated locally (fast path)")
        return {
            "sub": payload.get("sub", ""),
            "email": payload.get("email", ""),
            "aud": payload.get("aud", "authenticated"),
            "_token": token,
        }
    except pyjwt.ExpiredSignatureError:
        log.warning("Local JWT validation failed: token expired")
        return None
    except pyjwt.InvalidAudienceError:
        log.warning("Local JWT validation failed: invalid audience")
        return None
    except Exception as e:
        log.debug("Local JWT validation failed, falling back to API: {}", e)
        return None


def _decode_via_api(token: str) -> dict:
    """Validate JWT by calling Supabase Auth API (network call)."""
    supabase = get_supabase_client()
    user_response = supabase.auth.get_user(token)
    user = user_response.user
    if not user:
        raise ValueError("No user data returned")
    return {
        "sub": user.id,
        "email": user.email,
        "aud": "authenticated",
        "_token": token,
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate JWT and return user claims.

    Uses local decoding (fast, no network) when SUPABASE_JWT_SECRET is set.
    Falls back to Supabase Auth API call (slower, but supports RS256).

    Returns:
        dict with user claims (sub=user_id, email, aud) + _token

    Raises:
        HTTPException 401 if token is invalid, expired, or missing
    """
    token = credentials.credentials
    try:
        # Fast path: decode locally using JWT secret
        claims = _decode_local(token)
        if claims:
            return claims

        # Fallback: validate via Supabase Auth API
        return _decode_via_api(token)
    except Exception as e:
        log.warning("Token validation failed: {}", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
