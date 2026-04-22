from pydantic import BaseModel, Field

from planner.schemas import ExercisePlan, RiskLevel


class ValidationResult(BaseModel):
    """Result of validating an exercise plan against planner safety rules."""

    valid: bool
    errors: list[str] = Field(default_factory=list)


def validate_exercise_plan(plan: ExercisePlan) -> ValidationResult:
    """Validate an exercise plan and return every rule violation found."""

    errors: list[str] = []

    if not plan.scope.allowed_targets:
        errors.append("scope.allowed_targets must not be empty")

    overlapping_targets = set(plan.scope.allowed_targets) & set(plan.scope.blocked_targets)
    if overlapping_targets:
        targets = ", ".join(sorted(overlapping_targets))
        errors.append(f"allowed_targets and blocked_targets must not overlap: {targets}")

    unsafe_step_ids = [
        step.step_id for step in plan.execution_steps if not step.safe
    ]
    if unsafe_step_ids:
        step_ids = ", ".join(unsafe_step_ids)
        errors.append(f"all execution steps must be marked safe: {step_ids}")

    if plan.risk_level == RiskLevel.HIGH and not plan.requires_approval:
        errors.append("high risk exercise plans require approval")

    return ValidationResult(valid=not errors, errors=errors)

