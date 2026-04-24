from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

WebhookType = Literal["slack", "teams", "generic"]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class WebhookConfig(BaseModel):
    webhook_id: str = Field(default_factory=lambda: f"webhook-{uuid4().hex[:12]}")
    name: str
    type: WebhookType = "generic"
    url: str
    enabled: bool = True
    events: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)


class WebhookConfigCreate(BaseModel):
    name: str
    type: WebhookType = "generic"
    url: str
    enabled: bool = True
    events: list[str] = Field(default_factory=list)


class WebhookEvent(BaseModel):
    event_type: str
    environment_id: str
    severity: str = "info"
    title: str
    body: str
    metadata: dict[str, object] = Field(default_factory=dict)
