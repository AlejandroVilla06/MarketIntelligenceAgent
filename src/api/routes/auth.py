"""Authentication endpoints — signup, login, OAuth, logout, profile."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from src.api.auth.supabase_client import get_supabase_client
from src.api.auth.jwt_validator import get_current_user
from src.api.auth.user_service import get_profile, update_profile
from src.api.schemas.auth import (
    SignupRequest, SignupResponse,
    LoginRequest, LoginResponse,
    OAuthResponse, OAuthProvider,
    TokenRefreshRequest, TokenRefreshResponse,
    UserProfile, UserProfileUpdate,
)
from src.utils import get_logger

router = APIRouter(tags=["auth"])
log = get_logger("api.routes.auth")


@router.post("/auth/signup", response_model=SignupResponse)
async def signup(request: SignupRequest, supabase: Client = Depends(get_supabase_client)):
    """Register with email and password."""
    try:
        result = supabase.auth.sign_up({"email": request.email, "password": request.password})
        user = result.user
        if not user:
            raise HTTPException(status_code=400, detail="Signup failed")
        return SignupResponse(
            user_id=user.id,
            access_token=result.session.access_token if result.session else "",
        )
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        log.error(f"Signup failed: {e}")
        raise HTTPException(status_code=400, detail="Registration failed. Check your input.")


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, supabase: Client = Depends(get_supabase_client)):
    """Login with email and password."""
    try:
        result = supabase.auth.sign_in_with_password({"email": request.email, "password": request.password})
        user = result.user
        session = result.session
        if not user or not session:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Get profile
        profile = get_profile(supabase, user.id)
        if not profile:
            profile = UserProfile(id=user.id, email=user.email)

        return LoginResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            user=profile,
        )
    except Exception as e:
        log.error(f"Login failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/auth/oauth/{provider}", response_model=OAuthResponse)
async def oauth_url(provider: str, supabase: Client = Depends(get_supabase_client)):
    """Get OAuth URL for social login (google, github)."""
    valid_providers = {"google", "github"}
    if provider.lower() not in valid_providers:
        raise HTTPException(status_code=400, detail=f"Unsupported provider. Use: {', '.join(valid_providers)}")

    try:
        result = supabase.auth.sign_in_with_oauth({
            "provider": provider.lower(),
        })
        return OAuthResponse(url=result.url, provider=provider.lower())
    except Exception as e:
        log.error(f"OAuth URL failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to get authentication URL.")


@router.get("/auth/callback")
async def oauth_callback(
    code: str = Query(...),
    supabase: Client = Depends(get_supabase_client),
):
    """Exchange OAuth code for session."""
    try:
        result = supabase.auth.exchange_code_for_session({"auth_code": code})
        user = result.user
        session = result.session
        if not user or not session:
            raise HTTPException(status_code=400, detail="Authentication failed")

        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "user_id": user.id,
        }
    except Exception as e:
        log.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed. Try again.")


@router.post("/auth/logout")
async def logout(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """Logout and invalidate session."""
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        log.error(f"Logout failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to logout. Try again.")


@router.get("/auth/me", response_model=UserProfile)
async def get_me(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """Get current user profile."""
    user_id = user.get("sub", "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: no user ID")

    profile = get_profile(supabase, user_id)
    if not profile:
        # Profile may not exist if trigger hasn't fired — create it
        profile = UserProfile(id=user_id, email=user.get("email"))

    return profile


@router.put("/auth/me", response_model=UserProfile)
async def update_me(
    update: UserProfileUpdate,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """Update current user profile."""
    user_id = user.get("sub", "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: no user ID")

    profile = update_profile(supabase, user_id, update)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


@router.post("/auth/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    supabase: Client = Depends(get_supabase_client),
):
    """Refresh access token."""
    try:
        result = supabase.auth.refresh_session(request.refresh_token)
        session = result.session
        if not session:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        return TokenRefreshResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
        )
    except Exception as e:
        log.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Session expired. Login again.")
