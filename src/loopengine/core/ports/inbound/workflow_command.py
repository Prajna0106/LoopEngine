"""Inbound port — workflow command (write side)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CreateWorkflowCommand:
    """Command to create a new workflow."""

    config_path: str
    project_path: str


@dataclass(frozen=True)
class StartWorkflowCommand:
    """Command to start executing a workflow."""

    workflow_id: str


@dataclass(frozen=True)
class CancelWorkflowCommand:
    """Command to cancel a running workflow."""

    workflow_id: str
    reason: str = ""


class WorkflowCommandPort(ABC):
    """Write-side commands for workflow state."""

    @abstractmethod
    def create(self, command: CreateWorkflowCommand) -> str:
        """Create a workflow and return its ID."""

    @abstractmethod
    def start(self, command: StartWorkflowCommand) -> None:
        """Start executing a workflow."""

    @abstractmethod
    def cancel(self, command: CancelWorkflowCommand) -> None:
        """Cancel a running workflow."""
