from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from planner.schemas import utc_now


class DatasourceIngestionJob(BaseModel):
    job_id: str = Field(..., min_length=1)
    datasource_id: str = Field(..., min_length=1)
    environment_id: str = Field(..., min_length=1)
    status: Literal["scheduled", "running", "completed", "failed", "disabled"] = "scheduled"
    trigger_mode: Literal["manual", "interval"] = "manual"
    interval_seconds: int | None = Field(default=None, ge=30)
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    last_status_message: str | None = None
    records_ingested: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
