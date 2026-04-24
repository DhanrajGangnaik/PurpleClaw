from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

UserRole = Literal["admin", "analyst", "viewer"]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class User(BaseModel):
    user_id: str = Field(default_factory=lambda: f"user-{uuid4().hex[:12]}")
    username: str
    email: str = ""
    hashed_password: str
    role: UserRole = "viewer"
    is_active: bool = True
    force_password_change: bool = False
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)


class UserCreate(BaseModel):
    username: str
    email: str = ""
    password: str
    role: UserRole = "viewer"


class UserUpdate(BaseModel):
    email: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = None


class UserPublic(BaseModel):
    user_id: str
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class TokenPayload(BaseModel):
    sub: str
    username: str
    role: UserRole
    exp: int
