from __future__ import annotations

import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from auth.models import UserPublic, UserRole
from auth.service import decode_token
from auth.store import get_user_by_id

AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"

_bearer = HTTPBearer(auto_error=False)

_ANONYMOUS_USER = UserPublic(
    user_id="anon",
    username="anonymous",
    email="",
    role="admin",
    is_active=True,
    created_at="",
)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> UserPublic:
    if not AUTH_ENABLED:
        return _ANONYMOUS_USER
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = get_user_by_id(payload.sub)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return UserPublic(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def require_role(*roles: UserRole):
    def _check(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' does not have permission for this action",
            )
        return current_user

    return _check


require_admin = require_role("admin")
require_analyst = require_role("admin", "analyst")
require_any = require_role("admin", "analyst", "viewer")
