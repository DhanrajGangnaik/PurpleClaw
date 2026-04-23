from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from planner.schemas import utc_now


class ScanPolicy(BaseModel):
    policy_id: str = Field(..., min_length=1)
    environment_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    allowed_targets: list[str] = Field(default_factory=list)
    allowed_network_ranges: list[str] = Field(default_factory=list)
    allowed_scan_types: list[str] = Field(default_factory=list)
    max_depth: Literal["light", "standard"] = "light"
    enabled: bool = True


class ScanPolicyCreate(BaseModel):
    environment_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    allowed_targets: list[str] = Field(default_factory=list)
    allowed_network_ranges: list[str] = Field(default_factory=list)
    allowed_scan_types: list[str] = Field(default_factory=list)
    max_depth: Literal["light", "standard"] = "light"
    enabled: bool = True


class ScanRequest(BaseModel):
    scan_id: str = Field(..., min_length=1)
    environment_id: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    target_type: Literal["asset", "hostname", "ip", "service"]
    scan_types: list[str] = Field(default_factory=list)
    depth: Literal["light", "standard"] = "light"
    requested_at: datetime = Field(default_factory=utc_now)
    status: Literal["queued", "running", "completed", "failed", "blocked"] = "queued"
    requested_by: str | None = None
    notes: str | None = None


class ScanRunRequest(BaseModel):
    environment_id: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    target_type: Literal["asset", "hostname", "ip", "service"]
    scan_types: list[str] = Field(default_factory=list)
    depth: Literal["light", "standard"] = "light"
    requested_by: str | None = None
    notes: str | None = None


class ScanResult(BaseModel):
    scan_id: str = Field(..., min_length=1)
    environment_id: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    findings_created: int = 0
    summary: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    status: str = Field(..., min_length=1)


class ScanDetail(BaseModel):
    request: ScanRequest
    result: ScanResult | None = None
    related_findings: list[dict[str, Any]] = Field(default_factory=list)
