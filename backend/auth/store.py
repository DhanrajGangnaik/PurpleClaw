from __future__ import annotations

from auth.models import User, UserCreate, UserUpdate
from auth.service import hash_password

_users: dict[str, User] = {}
_users_by_name: dict[str, str] = {}


def initialize_users(admin_username: str, admin_password: str) -> None:
    if not _users:
        admin = User(
            user_id="user-admin-bootstrap",
            username=admin_username,
            email="admin@purpleclaw.local",
            hashed_password=hash_password(admin_password),
            role="admin",
            is_active=True,
        )
        _users[admin.user_id] = admin
        _users_by_name[admin.username] = admin.user_id


def get_user_by_username(username: str) -> User | None:
    user_id = _users_by_name.get(username)
    return _users.get(user_id) if user_id else None


def get_user_by_id(user_id: str) -> User | None:
    return _users.get(user_id)


def list_users() -> list[User]:
    return sorted(_users.values(), key=lambda u: u.created_at)


def create_user(payload: UserCreate) -> User:
    if get_user_by_username(payload.username):
        raise ValueError(f"Username '{payload.username}' is already taken")
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    _users[user.user_id] = user
    _users_by_name[user.username] = user.user_id
    return user


def update_user(user_id: str, payload: UserUpdate) -> User | None:
    user = _users.get(user_id)
    if user is None:
        return None
    updates: dict[str, object] = {}
    if payload.email is not None:
        updates["email"] = payload.email
    if payload.role is not None:
        updates["role"] = payload.role
    if payload.is_active is not None:
        updates["is_active"] = payload.is_active
    if payload.password is not None:
        updates["hashed_password"] = hash_password(payload.password)
    updated = user.model_copy(update=updates)
    _users[user_id] = updated
    return updated


def delete_user(user_id: str) -> bool:
    user = _users.pop(user_id, None)
    if user:
        _users_by_name.pop(user.username, None)
        return True
    return False
