"""Execution-related exceptions."""

from __future__ import annotations

from loopengine.core.domain.exceptions.base import LoopEngineError


class ExecutionError(LoopEngineError):
    """Base for execution errors."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message, code="EXECUTION_ERROR")


class TaskFailedError(ExecutionError):
    """Raised when a task execution fails."""

    def __init__(self, task_id: str, reason: str = "") -> None:
        msg = f"Task '{task_id}' failed"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.code = "TASK_FAILED"
        self.task_id = task_id
        self.reason = reason


class DependencyNotMetError(ExecutionError):
    """Raised when a task's dependencies are not satisfied."""

    def __init__(self, task_id: str, missing: list[str] | None = None) -> None:
        missing_str = ", ".join(missing) if missing else "unknown"
        super().__init__(f"Task '{task_id}' has unsatisfied dependencies: {missing_str}")
        self.code = "DEPENDENCY_NOT_MET"
        self.task_id = task_id
        self.missing = missing or []


class PlanNotProvidedError(ExecutionError):
    """Raised when no plan is provided to the execution engine."""

    def __init__(self) -> None:
        super().__init__("No plan provided for execution")
        self.code = "PLAN_NOT_PROVIDED"
