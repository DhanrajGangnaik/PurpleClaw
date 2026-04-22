from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return the current UTC timestamp for audit fields."""

    return datetime.now(timezone.utc)


def new_execution_id() -> str:
    """Return a unique execution result identifier."""

    return str(uuid4())


class ExecutionResult(BaseModel):
    """Typed response returned by safe executor stubs."""

    execution_id: str = Field(default_factory=new_execution_id)
    environment_id: str = Field(default="homelab", min_length=1)
    created_at: datetime = Field(default_factory=utc_now)
    executed_at: datetime = Field(default_factory=utc_now)
    status: str
    executor: str
    message: str
    plan_id: str
    executed: bool
