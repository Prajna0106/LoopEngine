"""Unit tests for ReflectionService."""

from __future__ import annotations

import pytest

from loopengine.core.domain.exceptions.reflection_exceptions import (
    MaxIterationsExceededError,
    ReflectionError,
)
from loopengine.core.ports.outbound.executor_port import ExecutionResult
from loopengine.core.services.execution_engine import (
    ExecutionPhase,
    ExecutionReport,
    PhaseRecord,
    TaskRecord,
    TaskStatus,
)
from loopengine.core.services.reflection_service import (
    ErrorCategory,
    ErrorSeverity,
    IdentifiedIssue,
    ImprovementSuggestion,
    ReflectionAction,
    ReflectionReport,
    ReflectionService,
)

# ── Helpers ───────────────────────────────────────────────────────


def make_task(
    task_id: str,
    step_id: str,
    phase: str,
    status: TaskStatus,
    error: str = "",
    output: str = "ok",
) -> TaskRecord:
    """Create a TaskRecord with specified status."""
    task = TaskRecord(
        task_id=task_id,
        step_id=step_id,
        phase_name=phase,
        description=f"Task {step_id}",
    )
    if status == TaskStatus.COMPLETED:
        task.mark_running()
        task.mark_completed(ExecutionResult(output=output))
    elif status == TaskStatus.FAILED:
        task.mark_running()
        task.mark_failed(error)
    elif status == TaskStatus.BLOCKED:
        task.mark_blocked(error)
    elif status == TaskStatus.RUNNING:
        task.mark_running()
    return task


def make_report(
    goal: str = "test",
    tasks: list[TaskRecord] | None = None,
) -> ExecutionReport:
    """Create an ExecutionReport with specified tasks."""
    report = ExecutionReport(goal=goal)
    if tasks:
        phase = PhaseRecord(phase_name="Phase", description="Test phase")
        phase.tasks = tasks
        report.phases.append(phase)
    report.status = ExecutionPhase.COMPLETED
    return report


# ── Data Model Tests ──────────────────────────────────────────────


class TestErrorCategory:
    def test_values(self) -> None:
        assert ErrorCategory.SYNTAX.value == "syntax"
        assert ErrorCategory.LOGIC.value == "logic"
        assert ErrorCategory.DEPENDENCY.value == "dependency"
        assert ErrorCategory.TIMEOUT.value == "timeout"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.RESOURCE.value == "resource"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestErrorSeverity:
    def test_values(self) -> None:
        assert ErrorSeverity.CRITICAL.value == "critical"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.INFO.value == "info"


class TestReflectionAction:
    def test_values(self) -> None:
        assert ReflectionAction.CONVERGED.value == "converged"
        assert ReflectionAction.RETRY.value == "retry"
        assert ReflectionAction.FIX_AND_RETRY.value == "fix_and_retry"
        assert ReflectionAction.SKIP_AND_CONTINUE.value == "skip_and_continue"
        assert ReflectionAction.ESCALATE.value == "escalate"


class TestIdentifiedIssue:
    def test_construction(self) -> None:
        issue = IdentifiedIssue(
            task_id="t1",
            category=ErrorCategory.SYNTAX,
            severity=ErrorSeverity.CRITICAL,
            message="Syntax error",
            raw_error="IndentationError",
            phase_name="Execute",
        )
        assert issue.task_id == "t1"
        assert issue.category == ErrorCategory.SYNTAX
        assert issue.severity == ErrorSeverity.CRITICAL


class TestImprovementSuggestion:
    def test_construction(self) -> None:
        suggestion = ImprovementSuggestion(
            priority=1,
            description="Fix syntax",
            fix_prompt="Fix the indentation",
            affected_tasks=["t1"],
            rationale="Syntax errors block execution",
        )
        assert suggestion.priority == 1
        assert suggestion.affected_tasks == ["t1"]


class TestReflectionReport:
    def test_empty_report(self) -> None:
        report = ReflectionReport(goal="test")
        assert report.goal == "test"
        assert report.total_issues == 0
        assert not report.has_critical_issues
        assert report.issue_count_by_category == {}

    def test_has_critical_issues(self) -> None:
        report = ReflectionReport(goal="test")
        report.issues = [
            IdentifiedIssue(
                task_id="t1",
                category=ErrorCategory.SYNTAX,
                severity=ErrorSeverity.CRITICAL,
                message="Syntax error",
            )
        ]
        assert report.has_critical_issues

    def test_issue_count_by_category(self) -> None:
        report = ReflectionReport(goal="test")
        report.issues = [
            IdentifiedIssue(
                task_id="t1",
                category=ErrorCategory.SYNTAX,
                severity=ErrorSeverity.CRITICAL,
                message="err1",
            ),
            IdentifiedIssue(
                task_id="t2",
                category=ErrorCategory.SYNTAX,
                severity=ErrorSeverity.HIGH,
                message="err2",
            ),
            IdentifiedIssue(
                task_id="t3",
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.HIGH,
                message="err3",
            ),
        ]
        counts = report.issue_count_by_category
        assert counts["syntax"] == 2
        assert counts["timeout"] == 1

    def test_can_iterate(self) -> None:
        report = ReflectionReport(goal="test", iteration=2, max_iterations=5)
        assert report.can_iterate

    def test_cannot_iterate(self) -> None:
        report = ReflectionReport(goal="test", iteration=5, max_iterations=5)
        assert not report.can_iterate


# ── Exception Tests ───────────────────────────────────────────────


class TestExceptions:
    def test_reflection_error(self) -> None:
        err = ReflectionError("boom")
        assert str(err) == "boom"
        assert err.code == "REFLECTION_ERROR"

    def test_max_iterations_exceeded(self) -> None:
        err = MaxIterationsExceededError(5, ["issue1", "issue2"])
        assert err.max_iterations == 5
        assert err.last_issues == ["issue1", "issue2"]
        assert "5" in str(err)
        assert err.code == "MAX_ITERATIONS_EXCEEDED"


# ── ReflectionService Tests ───────────────────────────────────────


class TestReflectionServiceConstruction:
    def test_default_max_iterations(self) -> None:
        svc = ReflectionService()
        assert svc._max_iterations == 5

    def test_custom_max_iterations(self) -> None:
        svc = ReflectionService(max_iterations=10)
        assert svc._max_iterations == 10


class TestConvergenceDetection:
    def test_converges_when_all_pass(self) -> None:
        tasks = [
            make_task("t1", "s1", "P", TaskStatus.COMPLETED),
            make_task("t2", "s2", "P", TaskStatus.COMPLETED),
        ]
        report = make_report(tasks=tasks)
        svc = ReflectionService()
        result = svc.reflect(report)

        assert result.action == ReflectionAction.CONVERGED
        assert result.total_issues == 0
        assert "success" in result.reasoning.lower()

    def test_converges_empty_report(self) -> None:
        report = make_report(goal="empty")
        svc = ReflectionService()
        result = svc.reflect(report)
        assert result.action == ReflectionAction.CONVERGED


class TestErrorCategorization:
    def test_syntax_error(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.FAILED,
            error="IndentationError: unexpected indent",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService()
        result = svc.reflect(report)

        assert result.issues[0].category == ErrorCategory.SYNTAX
        assert result.issues[0].severity == ErrorSeverity.CRITICAL

    def test_dependency_error(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.FAILED,
            error="ModuleNotFoundError: No module named 'requests'",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService()
        result = svc.reflect(report)

        assert result.issues[0].category == ErrorCategory.DEPENDENCY
        assert result.issues[0].severity == ErrorSeverity.HIGH

    def test_timeout_error(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.FAILED,
            error="Execution timed out after 30s",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService()
        result = svc.reflect(report)

        assert result.issues[0].category == ErrorCategory.TIMEOUT
        assert result.issues[0].severity == ErrorSeverity.HIGH

    def test_logic_error(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.FAILED,
            error="AssertionError: expected 5, got 3",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService()
        result = svc.reflect(report)

        assert result.issues[0].category == ErrorCategory.LOGIC

    def test_validation_error(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.FAILED,
            error="ValidationError: field 'name' is required",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService()
        result = svc.reflect(report)

        assert result.issues[0].category == ErrorCategory.VALIDATION

    def test_configuration_error(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.FAILED,
            error="ConfigurationError: missing API key",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService()
        result = svc.reflect(report)

        assert result.issues[0].category == ErrorCategory.CONFIGURATION

    def test_resource_error(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.FAILED,
            error="OutOfMemoryError: memory limit exceeded",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService()
        result = svc.reflect(report)

        assert result.issues[0].category == ErrorCategory.RESOURCE

    def test_unknown_error(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.FAILED,
            error="Something weird happened",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService()
        result = svc.reflect(report)

        assert result.issues[0].category == ErrorCategory.UNKNOWN


class TestBlockedTaskHandling:
    def test_blocked_tasks_categorized_as_dependency(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.BLOCKED,
            error="Dependencies not met: s0",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService()
        result = svc.reflect(report)

        assert result.issues[0].category == ErrorCategory.DEPENDENCY
        assert result.issues[0].severity == ErrorSeverity.HIGH


class TestSuggestionGeneration:
    def test_suggestions_for_syntax_error(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.FAILED,
            error="SyntaxError: invalid syntax",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService()
        result = svc.reflect(report)

        assert len(result.suggestions) >= 1
        assert "syntax" in result.suggestions[0].description.lower()
        assert len(result.fix_prompts) >= 1

    def test_suggestions_for_timeout(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.FAILED,
            error="Timeout after 60s",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService()
        result = svc.reflect(report)

        assert len(result.suggestions) >= 1
        assert "timeout" in result.suggestions[0].description.lower()

    def test_suggestions_sorted_by_priority(self) -> None:
        tasks = [
            make_task("t1", "s1", "P", TaskStatus.FAILED, error="Syntax error"),
            make_task("t2", "s2", "P", TaskStatus.FAILED, error="Timeout"),
        ]
        report = make_report(tasks=tasks)
        svc = ReflectionService()
        result = svc.reflect(report)

        priorities = [s.priority for s in result.suggestions]
        assert priorities == sorted(priorities)


class TestActionDecision:
    def test_converged_when_no_issues(self) -> None:
        report = make_report(tasks=[make_task("t1", "s1", "P", TaskStatus.COMPLETED)])
        svc = ReflectionService()
        result = svc.reflect(report)
        assert result.action == ReflectionAction.CONVERGED

    def test_fix_and_retry_for_syntax(self) -> None:
        task = make_task("t1", "s1", "P", TaskStatus.FAILED, error="SyntaxError")
        report = make_report(tasks=[task])
        svc = ReflectionService(max_iterations=5)
        result = svc.reflect(report, iteration=0)
        assert result.action == ReflectionAction.FIX_AND_RETRY

    def test_escalate_at_max_iterations(self) -> None:
        task = make_task("t1", "s1", "P", TaskStatus.FAILED, error="SyntaxError")
        report = make_report(tasks=[task])
        svc = ReflectionService(max_iterations=3)

        with pytest.raises(MaxIterationsExceededError):
            svc.reflect(report, iteration=3)

    def test_skip_continue_for_blocked_only(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.BLOCKED,
            error="Dependencies not met: s0",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService(max_iterations=5)
        result = svc.reflect(report, iteration=0)
        assert result.action == ReflectionAction.SKIP_AND_CONTINUE

    def test_retry_for_unknown_error(self) -> None:
        task = make_task(
            "t1",
            "s1",
            "P",
            TaskStatus.FAILED,
            error="Something strange happened",
        )
        report = make_report(tasks=[task])
        svc = ReflectionService(max_iterations=5)
        result = svc.reflect(report, iteration=0)
        assert result.action == ReflectionAction.RETRY


class TestReasoningGeneration:
    def test_converged_reasoning(self) -> None:
        report = make_report(tasks=[make_task("t1", "s1", "P", TaskStatus.COMPLETED)])
        svc = ReflectionService()
        result = svc.reflect(report)
        assert "success" in result.reasoning.lower() or "completed" in result.reasoning.lower()

    def test_escalate_reasoning(self) -> None:
        task = make_task("t1", "s1", "P", TaskStatus.FAILED, error="SyntaxError")
        report = make_report(tasks=[task])
        svc = ReflectionService(max_iterations=1)
        with pytest.raises(MaxIterationsExceededError):
            svc.reflect(report, iteration=1)

    def test_fix_retry_reasoning(self) -> None:
        task = make_task("t1", "s1", "P", TaskStatus.FAILED, error="SyntaxError")
        report = make_report(tasks=[task])
        svc = ReflectionService(max_iterations=5)
        result = svc.reflect(report, iteration=0)
        assert "fix" in result.reasoning.lower() or "retry" in result.reasoning.lower()


class TestMetadataRecording:
    def test_metadata_recorded(self) -> None:
        tasks = [
            make_task("t1", "s1", "P", TaskStatus.COMPLETED),
            make_task("t2", "s2", "P", TaskStatus.FAILED, error="err"),
        ]
        report = make_report(goal="Build API", tasks=tasks)
        svc = ReflectionService()
        result = svc.reflect(report, context={"key": "val"})

        assert result.metadata["total_tasks"] == 2
        assert result.metadata["completed_tasks"] == 1
        assert result.metadata["failed_tasks"] == 1
        assert result.metadata["success_rate"] == 50.0


class TestReflectOnResults:
    def test_all_success(self) -> None:
        svc = ReflectionService()
        result = svc.reflect_on_results(
            _goal="test",
            results=[{"success": True, "output": "ok"}],
        )
        assert result.decision.value == "converged"

    def test_has_failure(self) -> None:
        svc = ReflectionService()
        result = svc.reflect_on_results(
            _goal="test",
            results=[{"success": False, "error": "bad"}],
        )
        assert result.decision.value == "iterate"
        assert len(result.issues) >= 1

    def test_max_iterations_escalates(self) -> None:
        svc = ReflectionService(max_iterations=2)
        result = svc.reflect_on_results(
            _goal="test",
            results=[{"success": False, "error": "bad"}],
            iteration=2,
        )
        assert result.decision.value == "escalate"


class TestLowSuccessRate:
    def test_suggestion_for_low_success_rate(self) -> None:
        tasks = [
            make_task("t1", "s1", "P", TaskStatus.COMPLETED),
            make_task("t2", "s2", "P", TaskStatus.FAILED, error="err1"),
            make_task("t3", "s3", "P", TaskStatus.FAILED, error="err2"),
            make_task("t4", "s4", "P", TaskStatus.FAILED, error="err3"),
        ]
        report = make_report(tasks=tasks)
        svc = ReflectionService()
        result = svc.reflect(report)

        assert report.success_rate == pytest.approx(25.0)
        assert len(result.suggestions) >= 1
