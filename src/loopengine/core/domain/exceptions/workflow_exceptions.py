"""Workflow-related exceptions."""

from __future__ import annotations

from loopengine.core.domain.exceptions.base import LoopEngineError


class WorkflowError(LoopEngineError):
    """Base for workflow errors."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message, code="WORKFLOW_ERROR")


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow ID does not exist."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow not found: {workflow_id}")
        self.code = "WORKFLOW_NOT_FOUND"
        self.workflow_id = workflow_id


class InvalidTransitionError(WorkflowError):
    """Raised on illegal state transition."""

    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"Cannot transition from {current!r} to {target!r}")
        self.code = "INVALID_TRANSITION"
        self.current = current
        self.target = target


class MaxIterationsReachedError(WorkflowError):
    """Raised when iteration limit is exceeded."""

    def __init__(self, limit: int) -> None:
        super().__init__(f"Max iterations ({limit}) reached without convergence")
        self.code = "MAX_ITERATIONS"
        self.limit = limit
