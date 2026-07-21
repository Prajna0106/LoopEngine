"""Execution engine — drives sequential task execution from plans.

Receives a PlanResult, executes tasks in dependency order, tracks status,
persists history, and generates execution reports.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from loopengine.core.domain.exceptions.execution_exceptions import (
    ExecutionError,
    PlanNotProvidedError,
)

if TYPE_CHECKING:
    from loopengine.core.ports.outbound.executor_port import ExecutionResult, Executor
    from loopengine.core.ports.outbound.planner_port import PlanResult, PlanStep


class TaskStatus(StrEnum):
    """Status of a single task execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class ExecutionPhase(StrEnum):
    """Overall execution phase."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskRecord:
    """Record of a single task's execution."""

    task_id: str
    step_id: str
    phase_name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: ExecutionResult | None = None
    error: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0
    duration_ms: float = 0.0

    @property
    def is_terminal(self) -> bool:
        """Return True if the task is in a terminal state."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.SKIPPED,
        )

    def mark_running(self) -> None:
        """Transition to RUNNING state."""
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()

    def mark_completed(self, result: ExecutionResult) -> None:
        """Transition to COMPLETED state."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.finished_at = time.time()
        self.duration_ms = (self.finished_at - self.started_at) * 1000

    def mark_failed(self, error: str) -> None:
        """Transition to FAILED state."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.finished_at = time.time()
        self.duration_ms = (self.finished_at - self.started_at) * 1000

    def mark_skipped(self, reason: str = "") -> None:
        """Transition to SKIPPED state."""
        self.status = TaskStatus.SKIPPED
        self.error = reason
        self.finished_at = time.time()

    def mark_blocked(self, reason: str = "") -> None:
        """Transition to BLOCKED state."""
        self.status = TaskStatus.BLOCKED
        self.error = reason


@dataclass
class PhaseRecord:
    """Record of a phase's execution."""

    phase_name: str
    description: str
    tasks: list[TaskRecord] = field(default_factory=list)

    @property
    def status(self) -> ExecutionPhase:
        """Derive phase status from task statuses."""
        if not self.tasks:
            return ExecutionPhase.IDLE
        if any(t.status == TaskStatus.RUNNING for t in self.tasks):
            return ExecutionPhase.RUNNING
        if all(t.status == TaskStatus.COMPLETED for t in self.tasks):
            return ExecutionPhase.COMPLETED
        if any(t.status == TaskStatus.FAILED for t in self.tasks):
            return ExecutionPhase.FAILED
        return ExecutionPhase.RUNNING

    @property
    def completed_count(self) -> int:
        """Count of completed tasks."""
        return sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)

    @property
    def failed_count(self) -> int:
        """Count of failed tasks."""
        return sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)

    @property
    def total_count(self) -> int:
        """Total number of tasks."""
        return len(self.tasks)


@dataclass
class ExecutionReport:
    """Summary report of the entire execution."""

    goal: str
    status: ExecutionPhase = ExecutionPhase.IDLE
    phases: list[PhaseRecord] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0
    total_duration_ms: float = 0.0
    error: str = ""

    @property
    def total_tasks(self) -> int:
        """Total number of tasks across all phases."""
        return sum(p.total_count for p in self.phases)

    @property
    def completed_tasks(self) -> int:
        """Total completed tasks."""
        return sum(p.completed_count for p in self.phases)

    @property
    def failed_tasks(self) -> int:
        """Total failed tasks."""
        return sum(p.failed_count for p in self.phases)

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage (0-100)."""
        total = self.total_tasks
        if total == 0:
            return 0.0
        return (self.completed_tasks / total) * 100

    @property
    def all_task_records(self) -> list[TaskRecord]:
        """Flat list of all task records across phases."""
        records: list[TaskRecord] = []
        for phase in self.phases:
            records.extend(phase.tasks)
        return records


class ExecutionEngine:
    """Domain service that executes plans sequentially.

    Executes tasks in dependency order, respecting phase boundaries.
    Each task is run via an Executor adapter. Supports future parallel
    execution by tracking dependency graphs.
    """

    def __init__(self, executor: Executor) -> None:
        self._executor = executor

    def execute(
        self,
        plan: PlanResult,
        *,
        context: dict[str, Any] | None = None,
        max_failures: int = 0,
    ) -> ExecutionReport:
        """Execute all tasks in the plan sequentially.

        Parameters
        ----------
        plan:
            The structured plan to execute.
        context:
            Optional shared context passed to each task.
        max_failures:
            Stop after this many failures (0 = no limit).

        Returns
        -------
        ExecutionReport
            A report summarizing the execution.
        """
        if plan is None:
            raise PlanNotProvidedError()

        context = context or {}
        report = ExecutionReport(goal=plan.goal)
        report.started_at = time.time()
        report.status = ExecutionPhase.RUNNING

        completed_ids: set[str] = set()
        failure_count = 0

        for plan_phase in plan.phases:
            phase_record = PhaseRecord(
                phase_name=plan_phase.name,
                description=plan_phase.description,
            )

            for step in plan_phase.steps:
                task = TaskRecord(
                    task_id=f"{plan_phase.name}:{step.id}",
                    step_id=step.id,
                    phase_name=plan_phase.name,
                    description=step.description,
                )

                if max_failures > 0 and failure_count >= max_failures:
                    task.mark_blocked("Max failures reached")
                    phase_record.tasks.append(task)
                    continue

                missing = [dep for dep in step.dependencies if dep not in completed_ids]
                if missing:
                    task.mark_blocked(f"Dependencies not met: {', '.join(missing)}")
                    phase_record.tasks.append(task)
                    continue

                task.mark_running()

                try:
                    task_context = {
                        **context,
                        "step_id": step.id,
                        "phase": plan_phase.name,
                        "expected_output": step.expected_output,
                        "acceptance_criteria": step.acceptance_criteria,
                        "completed_steps": list(completed_ids),
                    }

                    result = self._executor.execute(
                        step.description,
                        context=task_context,
                    )

                    if result.success:
                        task.mark_completed(result)
                        completed_ids.add(step.id)
                    else:
                        task.mark_failed(
                            result.metadata.get("error", "Execution returned failure")
                        )
                        failure_count += 1

                except ExecutionError as exc:
                    task.mark_failed(str(exc))
                    failure_count += 1
                except Exception as exc:
                    task.mark_failed(f"Unexpected error: {exc}")
                    failure_count += 1

                phase_record.tasks.append(task)

            report.phases.append(phase_record)

        report.finished_at = time.time()
        report.total_duration_ms = (report.finished_at - report.started_at) * 1000

        if failure_count > 0 and report.completed_tasks == 0:
            report.status = ExecutionPhase.FAILED
            report.error = f"All tasks failed ({failure_count} failures)"
        elif failure_count > 0:
            report.status = ExecutionPhase.COMPLETED
            report.error = f"{failure_count} task(s) failed"
        else:
            report.status = ExecutionPhase.COMPLETED

        return report

    def execute_step(
        self,
        step: PlanStep,
        phase_name: str = "",
        *,
        context: dict[str, Any] | None = None,
        completed_ids: set[str] | None = None,
    ) -> TaskRecord:
        """Execute a single step and return its record.

        Parameters
        ----------
        step:
            The plan step to execute.
        phase_name:
            Optional phase name for context.
        context:
            Optional execution context.
        completed_ids:
            Set of already-completed step IDs (for dependency checking).

        Returns
        -------
        TaskRecord
            The record of the executed step.
        """
        completed_ids = completed_ids or set()
        task = TaskRecord(
            task_id=f"{phase_name}:{step.id}" if phase_name else step.id,
            step_id=step.id,
            phase_name=phase_name,
            description=step.description,
        )

        missing = [dep for dep in step.dependencies if dep not in completed_ids]
        if missing:
            task.mark_blocked(f"Dependencies not met: {', '.join(missing)}")
            return task

        task.mark_running()

        try:
            task_context = {
                **(context or {}),
                "step_id": step.id,
                "phase": phase_name,
                "expected_output": step.expected_output,
                "acceptance_criteria": step.acceptance_criteria,
            }

            result = self._executor.execute(
                step.description,
                context=task_context,
            )

            if result.success:
                task.mark_completed(result)
            else:
                task.mark_failed(result.metadata.get("error", "Execution returned failure"))

        except ExecutionError as exc:
            task.mark_failed(str(exc))
        except Exception as exc:
            task.mark_failed(f"Unexpected error: {exc}")

        return task
