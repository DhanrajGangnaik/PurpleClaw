from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from planner.schemas import utc_now


class Dashboard(BaseModel):
    dashboard_id: str = Field(..., min_length=1)
    environment_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str | None = None
    layout: dict[str, Any] = Field(default_factory=dict)
    widgets: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DashboardCreate(BaseModel):
    environment_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str | None = None
    layout: dict[str, Any] = Field(default_factory=dict)
    widgets: list[dict[str, Any]] = Field(default_factory=list)


class DashboardUpdate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    layout: dict[str, Any] = Field(default_factory=dict)
    widgets: list[dict[str, Any]] = Field(default_factory=list)
