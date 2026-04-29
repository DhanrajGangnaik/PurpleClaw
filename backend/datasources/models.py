from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from planner.schemas import utc_now


class DataSource(BaseModel):
    datasource_id: str = Field(..., min_length=1)
    environment_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    type: Literal["prometheus", "loki", "file", "api", "inventory", "scanner_results", "kubernetes", "grafana", "ollama", "mlflow"]
    status: Literal["enabled", "disabled", "error"] = "enabled"
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_tested_at: datetime | None = None
    ingestion_enabled: bool = False
    ingestion_interval_seconds: int | None = Field(default=None, ge=30)


class DataSourceCreate(BaseModel):
    environment_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    type: Literal["prometheus", "loki", "file", "api", "inventory", "scanner_results", "kubernetes", "grafana", "ollama", "mlflow"]
    status: Literal["enabled", "disabled", "error"] = "enabled"
    config: dict[str, Any] = Field(default_factory=dict)
    ingestion_enabled: bool = False
    ingestion_interval_seconds: int | None = Field(default=None, ge=30)


class DataSourceScheduleRequest(BaseModel):
    trigger_mode: Literal["manual", "interval"] = "manual"
    interval_seconds: int | None = Field(default=None, ge=30)
    enabled: bool = True


class DataSourceTestRequest(BaseModel):
    environment_id: str = Field(..., min_length=1)
    type: Literal["prometheus", "loki", "file", "api", "inventory", "scanner_results", "kubernetes", "grafana", "ollama", "mlflow"]
    config: dict[str, Any] = Field(default_factory=dict)


class DataSourceTestResult(BaseModel):
    ok: bool
    status: Literal["enabled", "disabled", "error"]
    message: str
    checked_at: datetime = Field(default_factory=utc_now)
