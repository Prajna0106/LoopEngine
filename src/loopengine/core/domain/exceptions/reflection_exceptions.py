"""Reflection-related exceptions."""

from __future__ import annotations

from loopengine.core.domain.exceptions.base import LoopEngineError


class ReflectionError(LoopEngineError):
    """Base for reflection errors."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message, code="REFLECTION_ERROR")


class MaxIterationsExceededError(ReflectionError):
    """Raised when maximum iterations are exceeded."""

    def __init__(self, max_iterations: int, last_issues: list[str] | None = None) -> None:
        issues_str = "; ".join(last_issues) if last_issues else "none"
        super().__init__(f"Max iterations ({max_iterations}) exceeded. Last issues: {issues_str}")
        self.code = "MAX_ITERATIONS_EXCEEDED"
        self.max_iterations = max_iterations
        self.last_issues = last_issues or []
