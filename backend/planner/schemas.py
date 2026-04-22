from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


def utc_now() -> datetime:
    """Return the current UTC timestamp for audit fields."""

    return datetime.now(timezone.utc)


class Environment(StrEnum):
    """Supported exercise environment categories."""

    ENDPOINT = "endpoint"
    KUBERNETES = "kubernetes"
    CLOUD = "cloud"


class RiskLevel(StrEnum):
    """Exercise risk levels used for approval decisions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ExecutorType(StrEnum):
    """Supported executor integration types."""

    ATOMIC = "atomic"
    CALDERA = "caldera"
    CUSTOM = "custom"


class ScopePolicy(BaseModel):
    """Defines where and for how long an exercise may run."""

    allowed_targets: list[str] = Field(default_factory=list)
    blocked_targets: list[str] = Field(default_factory=list)
    max_execution_time: int = Field(..., gt=0, description="Maximum runtime in seconds.")


class Technique(BaseModel):
    """Maps an exercise to a documented ATT&CK technique."""

    id: str = Field(..., pattern=r"^T\d{4}(?:\.\d{3})?$")
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class ExecutionStep(BaseModel):
    """References an approved execution action without embedding raw commands."""

    step_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    executor: ExecutorType
    command_reference: str = Field(..., min_length=1)
    safe: bool


class ExpectedTelemetry(BaseModel):
    """Describes telemetry expected from a planned exercise."""

    source: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class DetectionExpectation(BaseModel):
    """Describes detections expected to trigger during an exercise."""

    detection_name: str = Field(..., min_length=1)
    data_source: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class RollbackStep(BaseModel):
    """Describes a cleanup or rollback action for an exercise."""

    step_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)


class ExercisePlan(BaseModel):
    """Complete purple-team exercise plan and safety metadata."""

    id: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    environment: Environment
    scope: ScopePolicy
    techniques: list[Technique] = Field(default_factory=list)
    execution_steps: list[ExecutionStep] = Field(default_factory=list)
    expected_telemetry: list[ExpectedTelemetry] = Field(default_factory=list)
    expected_detections: list[DetectionExpectation] = Field(default_factory=list)
    rollback_steps: list[RollbackStep] = Field(default_factory=list)
    risk_level: RiskLevel
    requires_approval: bool

    @model_validator(mode="after")
    def validate_safety_requirements(self) -> "ExercisePlan":
        """Enforce safety constraints that span multiple fields."""

        if self.execution_steps and not self.scope.allowed_targets:
            raise ValueError("execution_steps require at least one allowed target")

        if self.risk_level == RiskLevel.HIGH and not self.requires_approval:
            raise ValueError("high risk exercise plans require approval")

        return self
