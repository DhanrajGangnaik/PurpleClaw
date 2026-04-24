from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from planner.schemas import utc_now


class Environment(BaseModel):
    """A managed PurpleClaw environment."""

    environment_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    type: Literal["homelab", "lab", "staging", "production"]
    description: str = Field(default="")
    status: Literal["active", "inactive"]
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DataSource(StrEnum):
    """Origin of posture data."""

    DEMO = "demo"
    TRACKING = "tracking"


class SystemModeName(StrEnum):
    """Runtime posture data mode."""

    DEMO = "demo"
    TRACKING = "tracking"


class FindingSeverity(StrEnum):
    """Defensive finding severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Asset(BaseModel):
    """A homelab asset tracked for security posture."""

    id: str = Field(..., min_length=1)
    environment_id: str = Field(default="homelab", min_length=1)
    name: str = Field(..., min_length=1)
    asset_type: str = Field(..., min_length=1)
    environment: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    exposure: str = Field(..., min_length=1)
    criticality: str = Field(..., min_length=1)
    risk_score: int = Field(..., ge=0, le=100)
    status: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    telemetry_sources: list[str] = Field(default_factory=list)
    source: DataSource = DataSource.DEMO
    last_seen: datetime = Field(default_factory=utc_now)


class Finding(BaseModel):
    """A defensive posture issue discovered on an asset."""

    id: str = Field(..., min_length=1)
    environment_id: str = Field(default="homelab", min_length=1)
    asset_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    severity: FindingSeverity
    category: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    exposure: str = Field(..., min_length=1)
    evidence_summary: str = Field(..., min_length=1)
    verification: str = Field(..., min_length=1)
    score: int = Field(default=0, ge=0, le=100)
    confidence: Literal["low", "medium", "high"] = "medium"
    affected_component: str | None = None
    source: DataSource = DataSource.DEMO
    opened_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class InventoryRecord(BaseModel):
    """Environment-scoped package, service, image, or binary inventory record."""

    inventory_id: str = Field(..., min_length=1)
    environment_id: str = Field(default="homelab", min_length=1)
    asset_id: str = Field(..., min_length=1)
    component_name: str = Field(..., min_length=1)
    component_type: Literal["package", "service", "container_image", "binary"]
    version: str = Field(..., min_length=1)
    source: DataSource = DataSource.DEMO
    detected_at: datetime = Field(default_factory=utc_now)


class RemediationTask(BaseModel):
    """A defensive task mapped to a posture finding."""

    id: str = Field(..., min_length=1)
    environment_id: str = Field(default="homelab", min_length=1)
    finding_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    due_date: datetime
    steps: list[str] = Field(default_factory=list)
    verification: str = Field(..., min_length=1)
    source: DataSource = DataSource.DEMO
    updated_at: datetime = Field(default_factory=utc_now)


class Policy(BaseModel):
    """A defensive control or posture policy."""

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    coverage: int = Field(..., ge=0, le=100)
    requirements: list[str] = Field(default_factory=list)
    source: DataSource = DataSource.DEMO
    last_reviewed: datetime = Field(default_factory=utc_now)


class Report(BaseModel):
    """A generated defensive posture report."""

    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    report_type: str = Field(..., min_length=1)
    period: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=utc_now)
    summary: str = Field(..., min_length=1)
    key_metrics: dict[str, int | str] = Field(default_factory=dict)
    source: DataSource = DataSource.DEMO


class TelemetrySummary(BaseModel):
    """Aggregated telemetry health for one posture domain."""

    id: str = Field(..., min_length=1)
    environment_id: str = Field(default="homelab", min_length=1)
    source_name: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1)
    source: DataSource
    asset_count: int = Field(..., ge=0)
    event_count: int = Field(..., ge=0)
    health_status: str = Field(..., min_length=1)
    updated_at: datetime = Field(default_factory=utc_now)
    notes: list[str] = Field(default_factory=list)


class Alert(BaseModel):
    """Read-only operational or security alert."""

    alert_id: str = Field(..., min_length=1)
    environment_id: str = Field(default="homelab", min_length=1)
    source: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    severity: FindingSeverity
    status: str = Field(..., min_length=1)
    started_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    asset_id: str | None = None


class SecuritySignal(BaseModel):
    """Correlation-ready security signal record."""

    signal_id: str = Field(..., min_length=1)
    environment_id: str = Field(default="homelab", min_length=1)
    source: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    severity: FindingSeverity
    confidence: Literal["low", "medium", "high"]
    asset_id: str | None = None
    evidence: str = Field(..., min_length=1)
    detected_at: datetime = Field(default_factory=utc_now)
    status: str = Field(..., min_length=1)


class IncidentSummary(BaseModel):
    """Investigation-friendly incident summary."""

    incident_id: str = Field(..., min_length=1)
    environment_id: str = Field(default="homelab", min_length=1)
    title: str = Field(..., min_length=1)
    severity: FindingSeverity
    status: str = Field(..., min_length=1)
    related_signal_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ServiceHealth(BaseModel):
    """NOC service health record."""

    service_id: str = Field(..., min_length=1)
    environment_id: str = Field(default="homelab", min_length=1)
    name: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    availability: int = Field(..., ge=0, le=100)
    latency_ms: int | None = Field(default=None, ge=0)
    error_rate: float | None = Field(default=None, ge=0)
    updated_at: datetime = Field(default_factory=utc_now)


class DependencyStatus(BaseModel):
    """Read-only dependency status record."""

    dependency_id: str = Field(..., min_length=1)
    environment_id: str = Field(default="homelab", min_length=1)
    name: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    notes: str = Field(..., min_length=1)
    updated_at: datetime = Field(default_factory=utc_now)


class TelemetrySourceHealth(BaseModel):
    """Health state for a telemetry source."""

    source_id: str = Field(..., min_length=1)
    environment_id: str = Field(default="homelab", min_length=1)
    source_name: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    last_success_at: datetime | None = None
    notes: str = Field(..., min_length=1)
    updated_at: datetime = Field(default_factory=utc_now)


class SystemMode(BaseModel):
    """Current data mode for posture tracking."""

    mode: SystemModeName
    last_tracking_run_at: datetime | None = None
    tracking_enabled: bool


class AutomationRun(BaseModel):
    """A safe defensive automation run record."""

    run_id: str
    environment_id: str = Field(default="homelab", min_length=1)
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    assets_discovered: int = Field(..., ge=0)
    findings_created: int = Field(..., ge=0)
    posture_score: int = Field(..., ge=0, le=100)


class RiskByAsset(BaseModel):
    """Risk helper output for one asset."""

    asset_id: str
    asset_name: str
    open_findings: int
    critical_count: int
    high_count: int
    aggregate_score: int


class FindingSeverityCount(BaseModel):
    """Finding count helper output by severity."""

    severity: FindingSeverity
    count: int
