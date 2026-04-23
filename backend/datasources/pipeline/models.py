from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from planner.schemas import utc_now


class DataRecord(BaseModel):
    record_id: str = Field(..., min_length=1)
    environment_id: str = Field(..., min_length=1)
    datasource_id: str = Field(..., min_length=1)
    record_type: str = Field(..., min_length=1)
    metric: str = Field(..., min_length=1)
    value: float | int | str | bool | None = None
    dimensions: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    observed_at: datetime = Field(default_factory=utc_now)


class QuerySpec(BaseModel):
    record_types: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    aggregate: str = "raw"
    start_at: datetime | None = None
    end_at: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)
