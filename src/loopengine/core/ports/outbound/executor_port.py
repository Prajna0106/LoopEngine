"""Outbound port — executor interface.

Defines the contract for step/phase execution. An executor takes a
task description and produces an artifact or execution result.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExecutionResult:
    """Result of executing a single step or phase."""

    output: str
    success: bool = True
    artifacts: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class Executor(ABC):
    """Contract for step/phase executors.

    Follows ISP: only execution. An executor runs a single unit of work
    (a step or phase) and produces a result.
    """

    @abstractmethod
    def execute(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        """Execute a task and return the result.

        Parameters
        ----------
        task:
            Description of the work to perform.
        context:
            Optional state from prior steps (artifacts, intermediate results).
        timeout:
            Override the default timeout in seconds.

        Raises
        ------
        ExecutionError
            If execution fails due to an infrastructure or agent error.
        """

    @abstractmethod
    def can_execute(self, task_type: str) -> bool:
        """Return True if this executor handles *task_type*."""
