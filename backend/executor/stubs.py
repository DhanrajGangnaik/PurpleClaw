from executor.base import BaseExecutor
from executor.models import ExecutionResult
from executor.registry import register_executor
from planner.schemas import ExercisePlan


class AtomicExecutor(BaseExecutor):
    """Safe stub for future Atomic Red Team executor integration."""

    def execute(self, plan: ExercisePlan) -> ExecutionResult:
        """Return a structured response without running commands."""

        return ExecutionResult(
            status="stub",
            executor="atomic",
            message="Atomic executor stub did not run any commands.",
            plan_id=plan.id,
            executed=False,
        )


class CalderaExecutor(BaseExecutor):
    """Safe stub for future Caldera executor integration."""

    def execute(self, plan: ExercisePlan) -> ExecutionResult:
        """Return a structured response without running commands."""

        return ExecutionResult(
            status="stub",
            executor="caldera",
            message="Caldera executor stub did not run any commands.",
            plan_id=plan.id,
            executed=False,
        )


class CustomExecutor(BaseExecutor):
    """Safe stub for future custom executor integration."""

    def execute(self, plan: ExercisePlan) -> ExecutionResult:
        """Return a structured response without running commands."""

        return ExecutionResult(
            status="stub",
            executor="custom",
            message="Custom executor stub did not run any commands.",
            plan_id=plan.id,
            executed=False,
        )


register_executor("atomic", AtomicExecutor)
register_executor("caldera", CalderaExecutor)
register_executor("custom", CustomExecutor)
