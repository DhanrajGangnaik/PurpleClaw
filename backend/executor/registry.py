from executor.base import BaseExecutor


ExecutorName = str
ExecutorClass = type[BaseExecutor]

SUPPORTED_EXECUTORS: set[ExecutorName] = {"atomic", "caldera", "custom"}
_EXECUTOR_REGISTRY: dict[ExecutorName, ExecutorClass] = {}


def register_executor(name: str, executor_cls: ExecutorClass) -> None:
    """Register an executor class for a supported executor name."""

    if name not in SUPPORTED_EXECUTORS:
        supported = ", ".join(sorted(SUPPORTED_EXECUTORS))
        raise ValueError(f"Unknown executor '{name}'. Supported executors: {supported}")

    _EXECUTOR_REGISTRY[name] = executor_cls


def get_executor(name: str) -> ExecutorClass:
    """Return the executor class registered for a supported executor name."""

    if name not in SUPPORTED_EXECUTORS:
        supported = ", ".join(sorted(SUPPORTED_EXECUTORS))
        raise ValueError(f"Unknown executor '{name}'. Supported executors: {supported}")

    try:
        return _EXECUTOR_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"No executor registered for '{name}'") from exc

