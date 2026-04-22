from abc import ABC, abstractmethod

from executor.models import ExecutionResult
from planner import ValidationResult, validate_exercise_plan
from planner.schemas import ExercisePlan


class BaseExecutor(ABC):
    """Base contract for future Atomic, Caldera, and custom executors."""

    def validate(self, plan: ExercisePlan) -> ValidationResult:
        """Validate an exercise plan before any executor-specific handling."""

        return validate_exercise_plan(plan)

    @abstractmethod
    def execute(self, plan: ExercisePlan) -> ExecutionResult:
        """Return a safe execution stub without running commands."""

        return ExecutionResult(
            status="stub",
            executor=self.__class__.__name__,
            message="Execution is not implemented in the base executor.",
            plan_id=plan.id,
            executed=False,
        )
