from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user, require_admin
from auth.models import Token, UserCreate, UserPublic, UserUpdate
from auth.service import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, verify_password
from auth.store import create_user, delete_user, get_user_by_username, list_users, update_user
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login", response_model=Token)
def login(payload: LoginRequest) -> Token:
    user = get_user_by_username(payload.username)
    if user is None or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user)
    return Token(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


@router.get("/me", response_model=UserPublic)
def me(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return current_user


@router.get("/users", response_model=list[UserPublic])
def get_users(_: UserPublic = Depends(require_admin)) -> list[UserPublic]:
    return [
        UserPublic(user_id=u.user_id, username=u.username, email=u.email, role=u.role, is_active=u.is_active, created_at=u.created_at)
        for u in list_users()
    ]


@router.post("/users", response_model=UserPublic, status_code=201)
def create_new_user(payload: UserCreate, _: UserPublic = Depends(require_admin)) -> UserPublic:
    try:
        user = create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserPublic(user_id=user.user_id, username=user.username, email=user.email, role=user.role, is_active=user.is_active, created_at=user.created_at)


@router.patch("/users/{user_id}", response_model=UserPublic)
def update_user_endpoint(user_id: str, payload: UserUpdate, _: UserPublic = Depends(require_admin)) -> UserPublic:
    user = update_user(user_id, payload)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic(user_id=user.user_id, username=user.username, email=user.email, role=user.role, is_active=user.is_active, created_at=user.created_at)


@router.delete("/users/{user_id}", status_code=204, response_model=None)
def delete_user_endpoint(user_id: str, current_user: UserPublic = Depends(require_admin)) -> None:
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    if not delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
