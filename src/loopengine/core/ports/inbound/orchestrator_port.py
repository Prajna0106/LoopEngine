"""Inbound port — orchestrator interface.

Commands that drive workflow lifecycle.  The CLI calls these; implementations
live in the application layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class InitResult:
    """Result of project initialisation."""

    project_path: str
    config_path: str


@dataclass(frozen=True)
class DoctorResult:
    """Result of a health check."""

    checks: list[CheckItem]


@dataclass(frozen=True)
class CheckItem:
    """A single health-check entry."""

    name: str
    ok: bool
    detail: str = ""


@dataclass(frozen=True)
class PlanResult:
    """Result of planning a workflow."""

    workflow_id: str
    phases: list[str]
    summary: str


@dataclass(frozen=True)
class RunResult:
    """Result of running a workflow."""

    workflow_id: str
    status: str
    iterations: int
    summary: str


@dataclass(frozen=True)
class ReviewResult:
    """Result of reviewing a completed workflow."""

    workflow_id: str
    verdict: str  # "converged" | "needs_improvement"
    issues: list[str]
    summary: str


@dataclass(frozen=True)
class ImproveResult:
    """Result of triggering an improvement iteration."""

    workflow_id: str
    iteration: int
    changes: list[str]
    summary: str


class OrchestratorPort(ABC):
    """Public API for the CLI layer."""

    @abstractmethod
    def init(self, project_path: str) -> InitResult:
        """Initialise a LoopEngine project at *project_path*."""

    @abstractmethod
    def doctor(self) -> DoctorResult:
        """Run health checks and return results."""

    @abstractmethod
    def plan(self, config_path: str | None = None, *, goal: str | None = None) -> PlanResult:
        """Plan a workflow from configuration or goal."""

    @abstractmethod
    def run(
        self,
        config_path: str | None = None,
        *,
        dry_run: bool = False,
        goal: str | None = None,
    ) -> RunResult:
        """Execute a workflow."""

    @abstractmethod
    def review(self, workflow_id: str) -> ReviewResult:
        """Review results of a completed workflow."""

    @abstractmethod
    def improve(self, workflow_id: str) -> ImproveResult:
        """Trigger an improvement iteration on an existing workflow."""
