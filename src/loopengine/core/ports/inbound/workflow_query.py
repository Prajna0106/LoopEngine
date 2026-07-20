"""Inbound port — workflow query (read side)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorkflowSummary:
    """Read-only view of a workflow."""

    workflow_id: str
    status: str
    iteration: int
    phases: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class WorkflowQueryPort(ABC):
    """Read-side queries for workflow state."""

    @abstractmethod
    def get_status(self, workflow_id: str) -> WorkflowSummary:
        """Return the current state of a workflow."""

    @abstractmethod
    def list_workflows(self, *, limit: int = 20) -> list[WorkflowSummary]:
        """Return recent workflows."""
