"""Planner-related exceptions."""

from __future__ import annotations

from loopengine.core.domain.exceptions.base import LoopEngineError


class PlanError(LoopEngineError):
    """Raised when planning fails."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message, code="PLAN_ERROR")


class PlanValidationError(PlanError):
    """Raised when a plan fails validation."""

    def __init__(self, message: str = "", *, issues: list[str] | None = None) -> None:
        super().__init__(message)
        self.code = "PLAN_VALIDATION_ERROR"
        self.issues = issues or []


class PlanCyclicDependencyError(PlanError):
    """Raised when a plan contains cyclic dependencies."""

    def __init__(self, cycle: list[str] | None = None) -> None:
        cycle_str = " -> ".join(cycle) if cycle else "unknown"
        super().__init__(f"Cyclic dependency detected: {cycle_str}")
        self.code = "PLAN_CYCLIC_DEPENDENCY"
        self.cycle = cycle or []
