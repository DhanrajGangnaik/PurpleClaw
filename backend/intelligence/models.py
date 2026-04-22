from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from planner.schemas import utc_now
from posture.models import FindingSeverity


class ThreatAdvisory(BaseModel):
    """Curated advisory from a trusted, source-controlled intelligence feed."""

    advisory_id: str = Field(..., min_length=1)
    source_name: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    severity: FindingSeverity
    published_at: datetime = Field(default_factory=utc_now)
    summary: str = Field(..., min_length=1)
    affected_products: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class IntelIndicator(BaseModel):
    """Curated product, service, or technology indicator."""

    indicator_id: str = Field(..., min_length=1)
    source_name: str = Field(..., min_length=1)
    indicator_type: Literal["ip", "domain", "service", "technology", "product"]
    value: str = Field(..., min_length=1)
    confidence: Literal["low", "medium", "high"]
    first_seen: datetime = Field(default_factory=utc_now)
    last_seen: datetime = Field(default_factory=utc_now)
    notes: str = Field(..., min_length=1)


class IntelTrend(BaseModel):
    """Curated security trend relevant to posture prioritization."""

    trend_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    severity: FindingSeverity
    summary: str = Field(..., min_length=1)
    affected_technologies: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)


class IntelligenceUpdateRun(BaseModel):
    """Reviewable record of a deterministic intelligence refresh."""

    run_id: str = Field(..., min_length=1)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    status: str = Field(..., min_length=1)
    advisories_loaded: int = Field(..., ge=0)
    indicators_loaded: int = Field(..., ge=0)
    trends_loaded: int = Field(..., ge=0)
    findings_reprioritized: int = Field(..., ge=0)
