from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from planner.schemas import utc_now


class ReportTemplate(BaseModel):
    template_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    sections: list[str] = Field(default_factory=list)


class GeneratedReport(BaseModel):
    report_id: str = Field(..., min_length=1)
    environment_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=utc_now)
    generated_from: Literal["dashboard", "findings", "scan", "environment_summary"]
    source_id: str | None = None
    status: Literal["ready", "failed"] = "ready"
    file_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GenerateReportRequest(BaseModel):
    environment_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    generated_from: Literal["dashboard", "findings", "scan", "environment_summary"]
    source_id: str | None = None
    template_id: str | None = None
