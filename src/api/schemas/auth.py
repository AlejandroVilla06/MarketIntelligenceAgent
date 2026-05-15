"""
Auth Pydantic schemas for request/response models.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, EmailStr, Field

OAuthProvider = Literal["google", "github"]


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupResponse(BaseModel):
    user_id: str
    access_token: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserProfile


class OAuthResponse(BaseModel):
    url: str
    provider: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str


class UserProfile(BaseModel):
    """Matches the profiles table schema in PostgreSQL."""
    id: str
    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    preferred_language: str = "es"
    preferred_theme: str = "dark"


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    preferred_language: str | None = None
    preferred_theme: str | None = None


# Circular import workaround: define UserProfile before LoginResponse uses it
LoginResponse.model_rebuild()
