"""Reflection engine — analyzes execution results and decides next action.

Reads execution results, detects failures, categorizes errors,
generates improvement suggestions and fix prompts for iterative execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from loopengine.core.domain.exceptions.reflection_exceptions import (
    MaxIterationsExceededError,
)

if TYPE_CHECKING:
    from loopengine.core.ports.outbound.reflection_port import ReflectionResult
    from loopengine.core.services.execution_engine import ExecutionReport, TaskRecord


class ErrorCategory(StrEnum):
    """Category of error detected during reflection."""

    SYNTAX = "syntax"
    LOGIC = "logic"
    DEPENDENCY = "dependency"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class ErrorSeverity(StrEnum):
    """Severity of an identified issue."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReflectionAction(StrEnum):
    """Recommended action after reflection."""

    CONVERGED = "converged"
    RETRY = "retry"
    FIX_AND_RETRY = "fix_and_retry"
    SKIP_AND_CONTINUE = "skip_and_continue"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class IdentifiedIssue:
    """A specific issue identified during reflection."""

    task_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    raw_error: str = ""
    phase_name: str = ""


@dataclass(frozen=True)
class ImprovementSuggestion:
    """A suggestion for improving the next iteration."""

    priority: int
    description: str
    fix_prompt: str
    affected_tasks: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass
class ReflectionReport:
    """Structured report from the reflection engine."""

    goal: str
    iteration: int = 0
    max_iterations: int = 5
    action: ReflectionAction = ReflectionAction.CONVERGED
    issues: list[IdentifiedIssue] = field(default_factory=list)
    suggestions: list[ImprovementSuggestion] = field(default_factory=list)
    fix_prompts: list[str] = field(default_factory=list)
    reasoning: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_critical_issues(self) -> bool:
        """Return True if any critical issues exist."""
        return any(i.severity == ErrorSeverity.CRITICAL for i in self.issues)

    @property
    def issue_count_by_category(self) -> dict[str, int]:
        """Count issues per category."""
        counts: dict[str, int] = {}
        for issue in self.issues:
            cat = issue.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    @property
    def total_issues(self) -> int:
        """Total number of identified issues."""
        return len(self.issues)

    @property
    def can_iterate(self) -> bool:
        """Return True if more iterations are allowed."""
        return self.iteration < self.max_iterations


class ReflectionService:
    """Domain service that analyzes execution and decides next action.

    Reads an ExecutionReport, identifies and categorizes issues,
    generates improvement suggestions and fix prompts, and decides
    whether to converge, iterate, or escalate.
    """

    def __init__(self, *, max_iterations: int = 5) -> None:
        self._max_iterations = max_iterations

    def reflect(
        self,
        report: ExecutionReport,
        *,
        iteration: int = 0,
        context: dict[str, Any] | None = None,
    ) -> ReflectionReport:
        """Analyze execution report and produce a reflection report.

        Parameters
        ----------
        report:
            The execution report to analyze.
        iteration:
            Current iteration number (0-based).
        context:
            Optional additional context for reflection.

        Returns
        -------
        ReflectionReport
            Structured reflection with issues, suggestions, and next action.

        Raises
        ------
        MaxIterationsExceededError
            If iteration exceeds max_iterations and there are still issues.
        """
        context = context or {}
        failed_tasks = self._get_failed_tasks(report)
        blocked_tasks = self._get_blocked_tasks(report)

        issues = self._identify_issues(failed_tasks, blocked_tasks)
        suggestions = self._generate_suggestions(issues, report, context)
        fix_prompts = self._generate_fix_prompts(suggestions, issues, context)
        action = self._decide_action(issues, report, iteration, self._max_iterations)
        reasoning = self._build_reasoning(action, issues, report, iteration, self._max_iterations)

        if action == ReflectionAction.ESCALATE and iteration >= self._max_iterations and issues:
            raise MaxIterationsExceededError(
                self._max_iterations,
                [i.message for i in issues],
            )

        reflection = ReflectionReport(
            goal=report.goal,
            iteration=iteration,
            max_iterations=self._max_iterations,
            action=action,
            issues=issues,
            suggestions=suggestions,
            fix_prompts=fix_prompts,
            reasoning=reasoning,
            metadata={
                "total_tasks": report.total_tasks,
                "completed_tasks": report.completed_tasks,
                "failed_tasks": report.failed_tasks,
                "success_rate": report.success_rate,
                "context_keys": list(context.keys()),
            },
        )

        return reflection

    def reflect_on_results(
        self,
        *,
        _goal: str,
        results: list[dict[str, Any]],
        iteration: int = 0,
    ) -> ReflectionResult:
        """Simplified reflection interface matching the port contract.

        Parameters
        ----------
        goal:
            The original workflow goal.
        results:
            Collected results from executed phases/steps.
        iteration:
            Current iteration number (0-based).

        Returns
        -------
        ReflectionResult
            Simple reflection result with decision and reasoning.
        """
        issues = self._analyze_raw_results(results)
        has_failures = any(not r.get("success", True) for r in results)

        if not has_failures and not issues:
            decision = "converged"
            reasoning = "All results indicate success"
        elif iteration >= self._max_iterations:
            decision = "escalate"
            reasoning = f"Max iterations ({self._max_iterations}) reached"
        else:
            decision = "iterate"
            reasoning = f"Found {len(issues)} issue(s) to address"

        from loopengine.core.ports.outbound.reflection_port import (
            ReflectionDecision,
            ReflectionResult,
        )

        return ReflectionResult(
            decision=ReflectionDecision(decision),
            reasoning=reasoning,
            issues=issues,
            suggestions=[f"Address issue: {i}" for i in issues],
        )

    # ── Task Analysis ──────────────────────────────────────────────

    def _get_failed_tasks(self, report: ExecutionReport) -> list[TaskRecord]:
        """Extract failed tasks from the report."""
        from loopengine.core.services.execution_engine import TaskStatus

        return [t for t in report.all_task_records if t.status == TaskStatus.FAILED]

    def _get_blocked_tasks(self, report: ExecutionReport) -> list[TaskRecord]:
        """Extract blocked tasks from the report."""
        from loopengine.core.services.execution_engine import TaskStatus

        return [t for t in report.all_task_records if t.status == TaskStatus.BLOCKED]

    # ── Issue Identification ───────────────────────────────────────

    def _identify_issues(
        self,
        failed_tasks: list[TaskRecord],
        blocked_tasks: list[TaskRecord],
    ) -> list[IdentifiedIssue]:
        """Identify and categorize issues from failed/blocked tasks."""
        issues: list[IdentifiedIssue] = []

        for task in failed_tasks:
            category = self._categorize_error(task.error)
            severity = self._assess_severity(task, category)
            issues.append(
                IdentifiedIssue(
                    task_id=task.task_id,
                    category=category,
                    severity=severity,
                    message=self._build_issue_message(task, category),
                    raw_error=task.error,
                    phase_name=task.phase_name,
                )
            )

        for task in blocked_tasks:
            issues.append(
                IdentifiedIssue(
                    task_id=task.task_id,
                    category=ErrorCategory.DEPENDENCY,
                    severity=ErrorSeverity.HIGH,
                    message=f"Task blocked: {task.error}",
                    raw_error=task.error,
                    phase_name=task.phase_name,
                )
            )

        return issues

    def _categorize_error(self, error_msg: str) -> ErrorCategory:
        """Categorize an error message into an ErrorCategory."""
        lower = error_msg.lower()

        if any(kw in lower for kw in ("syntax", "parse", "indentation", "unexpected token")):
            return ErrorCategory.SYNTAX
        if any(kw in lower for kw in ("config", "configuration", "setting", "env", "key")):
            return ErrorCategory.CONFIGURATION
        if any(kw in lower for kw in ("timeout", "timed out", "deadline")):
            return ErrorCategory.TIMEOUT
        if any(kw in lower for kw in ("import", "module", "not found")):
            return ErrorCategory.DEPENDENCY
        if any(kw in lower for kw in ("validation", "invalid", "schema", "type error")):
            return ErrorCategory.VALIDATION
        if any(kw in lower for kw in ("logic", "wrong", "incorrect", "expected", "assertion")):
            return ErrorCategory.LOGIC
        if any(kw in lower for kw in ("memory", "disk", "space", "resource", "quota")):
            return ErrorCategory.RESOURCE
        return ErrorCategory.UNKNOWN

    def _assess_severity(self, _task: TaskRecord, category: ErrorCategory) -> ErrorSeverity:
        """Assess severity based on category and context."""
        if category == ErrorCategory.SYNTAX:
            return ErrorSeverity.CRITICAL
        if category == ErrorCategory.DEPENDENCY:
            return ErrorSeverity.HIGH
        if category == ErrorCategory.TIMEOUT:
            return ErrorSeverity.HIGH
        if category == ErrorCategory.LOGIC:
            return ErrorSeverity.MEDIUM
        if category == ErrorCategory.VALIDATION:
            return ErrorSeverity.MEDIUM
        if category == ErrorCategory.CONFIGURATION:
            return ErrorSeverity.MEDIUM
        if category == ErrorCategory.RESOURCE:
            return ErrorSeverity.HIGH
        return ErrorSeverity.LOW

    def _build_issue_message(self, task: TaskRecord, category: ErrorCategory) -> str:
        """Build a human-readable issue message."""
        return (
            f"Task '{task.step_id}' in phase '{task.phase_name}' "
            f"failed with {category.value} error: {task.error}"
        )

    # ── Suggestion Generation ──────────────────────────────────────

    def _generate_suggestions(
        self,
        issues: list[IdentifiedIssue],
        report: ExecutionReport,
        context: dict[str, Any],
    ) -> list[ImprovementSuggestion]:
        """Generate improvement suggestions based on identified issues."""
        suggestions: list[ImprovementSuggestion] = []

        for idx, issue in enumerate(issues):
            suggestion = self._suggest_for_issue(issue, idx + 1, context)
            if suggestion:
                suggestions.append(suggestion)

        if report.success_rate < 50 and not suggestions:
            suggestions.append(
                ImprovementSuggestion(
                    priority=1,
                    description="Low success rate — consider simplifying the plan",
                    fix_prompt="Break down complex tasks into smaller steps",
                    rationale=f"Success rate is {report.success_rate:.0f}%",
                )
            )

        return sorted(suggestions, key=lambda s: s.priority)

    def _suggest_for_issue(
        self,
        issue: IdentifiedIssue,
        priority: int,
        _context: dict[str, Any],
    ) -> ImprovementSuggestion | None:
        """Generate a suggestion for a specific issue."""
        if issue.category == ErrorCategory.SYNTAX:
            return ImprovementSuggestion(
                priority=priority,
                description=f"Fix syntax error in task '{issue.task_id}'",
                fix_prompt=(f"Fix the following syntax error and retry:\n{issue.raw_error}"),
                affected_tasks=[issue.task_id],
                rationale="Syntax errors prevent code from running",
            )
        if issue.category == ErrorCategory.DEPENDENCY:
            return ImprovementSuggestion(
                priority=priority,
                description=f"Resolve dependency issue for task '{issue.task_id}'",
                fix_prompt=(f"Install or fix the missing dependency:\n{issue.raw_error}"),
                affected_tasks=[issue.task_id],
                rationale="Missing dependencies block execution",
            )
        if issue.category == ErrorCategory.TIMEOUT:
            return ImprovementSuggestion(
                priority=priority,
                description=f"Increase timeout or optimize task '{issue.task_id}'",
                fix_prompt=(
                    f"Optimize the task to complete faster, or increase timeout:\n"
                    f"{issue.raw_error}"
                ),
                affected_tasks=[issue.task_id],
                rationale="Timeout indicates the task takes too long",
            )
        if issue.category == ErrorCategory.LOGIC:
            return ImprovementSuggestion(
                priority=priority,
                description=f"Review logic in task '{issue.task_id}'",
                fix_prompt=(f"Review and fix the logic error:\n{issue.raw_error}"),
                affected_tasks=[issue.task_id],
                rationale="Logic errors produce incorrect results",
            )
        if issue.category == ErrorCategory.VALIDATION:
            return ImprovementSuggestion(
                priority=priority,
                description=f"Fix validation errors in task '{issue.task_id}'",
                fix_prompt=(f"Fix the validation/type errors:\n{issue.raw_error}"),
                affected_tasks=[issue.task_id],
                rationale="Validation errors indicate type or schema mismatches",
            )
        if issue.category == ErrorCategory.CONFIGURATION:
            return ImprovementSuggestion(
                priority=priority,
                description=f"Fix configuration for task '{issue.task_id}'",
                fix_prompt=(f"Update configuration to fix the error:\n{issue.raw_error}"),
                affected_tasks=[issue.task_id],
                rationale="Configuration errors prevent proper setup",
            )
        if issue.category == ErrorCategory.RESOURCE:
            return ImprovementSuggestion(
                priority=priority,
                description=f"Resolve resource issue for task '{issue.task_id}'",
                fix_prompt=(f"Free up resources or adjust limits:\n{issue.raw_error}"),
                affected_tasks=[issue.task_id],
                rationale="Resource exhaustion blocks execution",
            )
        return ImprovementSuggestion(
            priority=priority,
            description=f"Investigate failure in task '{issue.task_id}'",
            fix_prompt=f"Investigate and fix:\n{issue.raw_error}",
            affected_tasks=[issue.task_id],
            rationale="Unknown error requires investigation",
        )

    # ── Fix Prompt Generation ──────────────────────────────────────

    def _generate_fix_prompts(
        self,
        suggestions: list[ImprovementSuggestion],
        issues: list[IdentifiedIssue],
        _context: dict[str, Any],
    ) -> list[str]:
        """Generate concrete fix prompts for the next iteration."""
        prompts: list[str] = []

        for suggestion in suggestions:
            if suggestion.fix_prompt:
                prompts.append(suggestion.fix_prompt)

        if not prompts and issues:
            prompts.append(
                "Review and fix the following issues:\n"
                + "\n".join(f"- {i.message}" for i in issues)
            )

        return prompts

    # ── Decision Making ────────────────────────────────────────────

    def _decide_action(
        self,
        issues: list[IdentifiedIssue],
        _report: ExecutionReport,
        iteration: int,
        max_iterations: int,
    ) -> ReflectionAction:
        """Decide the next action based on issues and iteration count."""
        if not issues:
            return ReflectionAction.CONVERGED

        has_critical = any(i.severity == ErrorSeverity.CRITICAL for i in issues)

        if has_critical and iteration >= max_iterations:
            return ReflectionAction.ESCALATE

        if iteration >= max_iterations:
            return ReflectionAction.ESCALATE

        only_blocked = all(i.category == ErrorCategory.DEPENDENCY for i in issues)
        if only_blocked:
            return ReflectionAction.SKIP_AND_CONTINUE

        has_fixable = any(
            i.category
            in (
                ErrorCategory.SYNTAX,
                ErrorCategory.LOGIC,
                ErrorCategory.VALIDATION,
                ErrorCategory.CONFIGURATION,
            )
            for i in issues
        )
        if has_fixable:
            return ReflectionAction.FIX_AND_RETRY

        return ReflectionAction.RETRY

    # ── Reasoning ──────────────────────────────────────────────────

    def _build_reasoning(
        self,
        action: ReflectionAction,
        issues: list[IdentifiedIssue],
        report: ExecutionReport,
        iteration: int,
        max_iterations: int,
    ) -> str:
        """Build human-readable reasoning for the decision."""
        if action == ReflectionAction.CONVERGED:
            return (
                f"All {report.total_tasks} task(s) completed successfully. "
                f"Goal '{report.goal}' achieved."
            )

        cats = [i.category.value for i in issues]
        cat_summary = ", ".join(sorted(set(cats)))

        if action == ReflectionAction.ESCALATE:
            return (
                f"Escalating after {iteration} iteration(s). "
                f"{len(issues)} unresolved issue(s) [{cat_summary}]. "
                f"Max iterations ({max_iterations}) reached."
            )
        if action == ReflectionAction.FIX_AND_RETRY:
            return (
                f"Found {len(issues)} fixable issue(s) [{cat_summary}] "
                f"after iteration {iteration}. Generating fix prompts "
                f"for next iteration."
            )
        if action == ReflectionAction.RETRY:
            return (
                f"Found {len(issues)} issue(s) [{cat_summary}] "
                f"after iteration {iteration}. Retrying execution."
            )
        if action == ReflectionAction.SKIP_AND_CONTINUE:
            return (
                f"All {len(issues)} issue(s) are dependency-related. "
                f"Skipping blocked tasks and continuing."
            )
        return "Unknown action"

    # ── Raw Result Analysis ────────────────────────────────────────

    def _analyze_raw_results(self, results: list[dict[str, Any]]) -> list[str]:
        """Analyze raw result dicts for issues."""
        issues: list[str] = []
        for idx, result in enumerate(results):
            if not result.get("success", True):
                error = result.get("error", result.get("message", "Unknown error"))
                issues.append(f"Result {idx}: {error}")
            output = result.get("output", "")
            if output and "error" in output.lower():
                issues.append(f"Result {idx} output contains error indicators")
        return issues
