"""Unit tests for ExecutionEngine."""

from __future__ import annotations

from typing import Any

import pytest

from loopengine.core.domain.exceptions.execution_exceptions import (
    DependencyNotMetError,
    ExecutionError,
    PlanNotProvidedError,
    TaskFailedError,
)
from loopengine.core.ports.outbound.executor_port import ExecutionResult, Executor
from loopengine.core.ports.outbound.planner_port import (
    PlanPhase,
    PlanResult,
    PlanStep,
    StepPriority,
)
from loopengine.core.services.execution_engine import (
    ExecutionEngine,
    ExecutionPhase,
    ExecutionReport,
    PhaseRecord,
    TaskRecord,
    TaskStatus,
)

# ── Test Doubles ──────────────────────────────────────────────────


class StubExecutor(Executor):
    """Stub executor for testing."""

    def __init__(
        self,
        success: bool = True,
        output: str = "ok",
        fail_ids: set[str] | None = None,
    ) -> None:
        self._success = success
        self._output = output
        self._fail_ids = fail_ids or set()
        self.call_count = 0
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def execute(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        self.call_count += 1
        self.calls.append((task, context))

        step_id = (context or {}).get("step_id", "")
        if step_id in self._fail_ids:
            return ExecutionResult(
                output="failed",
                success=False,
                metadata={"error": f"Task {step_id} failed"},
            )

        return ExecutionResult(
            output=self._output,
            success=self._success,
            metadata={"step_id": step_id},
        )

    def can_execute(self, task_type: str) -> bool:
        return True


class FailingExecutor(Executor):
    """Executor that always raises."""

    def execute(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        raise ExecutionError("Executor exploded")

    def can_execute(self, task_type: str) -> bool:
        return True


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture()
def stub_executor() -> StubExecutor:
    return StubExecutor()


@pytest.fixture()
def engine(stub_executor: StubExecutor) -> ExecutionEngine:
    return ExecutionEngine(stub_executor)


def make_simple_plan() -> PlanResult:
    """Create a simple 3-step plan for testing."""
    return PlanResult(
        goal="Build a feature",
        phases=[
            PlanPhase(
                name="Plan",
                description="Planning phase",
                steps=[
                    PlanStep(
                        id="plan-1",
                        description="Analyze requirements",
                        priority=StepPriority.HIGH,
                        expected_output="Requirements doc",
                        acceptance_criteria=["Requirements are clear"],
                    ),
                ],
            ),
            PlanPhase(
                name="Execute",
                description="Execution phase",
                steps=[
                    PlanStep(
                        id="exec-1",
                        description="Implement feature",
                        priority=StepPriority.CRITICAL,
                        dependencies=["plan-1"],
                        expected_output="Code",
                        acceptance_criteria=["Code works"],
                    ),
                ],
            ),
            PlanPhase(
                name="Validate",
                description="Validation phase",
                steps=[
                    PlanStep(
                        id="val-1",
                        description="Run tests",
                        priority=StepPriority.HIGH,
                        dependencies=["exec-1"],
                        expected_output="Test results",
                        acceptance_criteria=["Tests pass"],
                    ),
                ],
            ),
        ],
    )


# ── Data Model Tests ──────────────────────────────────────────────


class TestTaskStatus:
    def test_values(self) -> None:
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.SKIPPED.value == "skipped"
        assert TaskStatus.BLOCKED.value == "blocked"


class TestExecutionPhase:
    def test_values(self) -> None:
        assert ExecutionPhase.IDLE.value == "idle"
        assert ExecutionPhase.RUNNING.value == "running"
        assert ExecutionPhase.COMPLETED.value == "completed"
        assert ExecutionPhase.FAILED.value == "failed"
        assert ExecutionPhase.CANCELLED.value == "cancelled"


class TestTaskRecord:
    def test_defaults(self) -> None:
        rec = TaskRecord(
            task_id="t1",
            step_id="s1",
            phase_name="Phase",
            description="Do thing",
        )
        assert rec.status == TaskStatus.PENDING
        assert rec.result is None
        assert rec.error == ""
        assert rec.duration_ms == 0.0
        assert not rec.is_terminal

    def test_mark_running(self) -> None:
        rec = TaskRecord(task_id="t1", step_id="s1", phase_name="P", description="D")
        rec.mark_running()
        assert rec.status == TaskStatus.RUNNING
        assert rec.started_at > 0

    def test_mark_completed(self) -> None:
        rec = TaskRecord(task_id="t1", step_id="s1", phase_name="P", description="D")
        rec.mark_running()
        result = ExecutionResult(output="done")
        rec.mark_completed(result)
        assert rec.status == TaskStatus.COMPLETED
        assert rec.result == result
        assert rec.is_terminal
        assert rec.duration_ms >= 0

    def test_mark_failed(self) -> None:
        rec = TaskRecord(task_id="t1", step_id="s1", phase_name="P", description="D")
        rec.mark_running()
        rec.mark_failed("oops")
        assert rec.status == TaskStatus.FAILED
        assert rec.error == "oops"
        assert rec.is_terminal

    def test_mark_skipped(self) -> None:
        rec = TaskRecord(task_id="t1", step_id="s1", phase_name="P", description="D")
        rec.mark_skipped("not needed")
        assert rec.status == TaskStatus.SKIPPED
        assert rec.error == "not needed"
        assert rec.is_terminal

    def test_mark_blocked(self) -> None:
        rec = TaskRecord(task_id="t1", step_id="s1", phase_name="P", description="D")
        rec.mark_blocked("waiting for dep")
        assert rec.status == TaskStatus.BLOCKED
        assert rec.error == "waiting for dep"


class TestPhaseRecord:
    def test_empty_phase(self) -> None:
        rec = PhaseRecord(phase_name="Empty", description="")
        assert rec.status == ExecutionPhase.IDLE
        assert rec.total_count == 0
        assert rec.completed_count == 0
        assert rec.failed_count == 0

    def test_phase_status_running(self) -> None:
        rec = PhaseRecord(phase_name="P", description="D")
        task = TaskRecord(task_id="t1", step_id="s1", phase_name="P", description="D")
        task.mark_running()
        rec.tasks.append(task)
        assert rec.status == ExecutionPhase.RUNNING

    def test_phase_status_completed(self) -> None:
        rec = PhaseRecord(phase_name="P", description="D")
        task = TaskRecord(task_id="t1", step_id="s1", phase_name="P", description="D")
        task.mark_running()
        task.mark_completed(ExecutionResult(output="ok"))
        rec.tasks.append(task)
        assert rec.status == ExecutionPhase.COMPLETED

    def test_phase_status_failed(self) -> None:
        rec = PhaseRecord(phase_name="P", description="D")
        t1 = TaskRecord(task_id="t1", step_id="s1", phase_name="P", description="D")
        t1.mark_running()
        t1.mark_completed(ExecutionResult(output="ok"))
        t2 = TaskRecord(task_id="t2", step_id="s2", phase_name="P", description="D")
        t2.mark_running()
        t2.mark_failed("error")
        rec.tasks.extend([t1, t2])
        assert rec.status == ExecutionPhase.FAILED


class TestExecutionReport:
    def test_empty_report(self) -> None:
        report = ExecutionReport(goal="test")
        assert report.total_tasks == 0
        assert report.completed_tasks == 0
        assert report.failed_tasks == 0
        assert report.success_rate == 0.0

    def test_success_rate(self) -> None:
        report = ExecutionReport(goal="test")
        phase = PhaseRecord(phase_name="P", description="D")
        for i in range(4):
            t = TaskRecord(task_id=f"t{i}", step_id=f"s{i}", phase_name="P", description="D")
            t.mark_running()
            t.mark_completed(ExecutionResult(output="ok"))
            phase.tasks.append(t)
        t_fail = TaskRecord(task_id="tf", step_id="sf", phase_name="P", description="D")
        t_fail.mark_running()
        t_fail.mark_failed("err")
        phase.tasks.append(t_fail)
        report.phases.append(phase)
        assert report.total_tasks == 5
        assert report.completed_tasks == 4
        assert report.failed_tasks == 1
        assert report.success_rate == pytest.approx(80.0)


# ── Exception Tests ───────────────────────────────────────────────


class TestExceptions:
    def test_execution_error(self) -> None:
        err = ExecutionError("boom")
        assert str(err) == "boom"
        assert err.code == "EXECUTION_ERROR"

    def test_task_failed_error(self) -> None:
        err = TaskFailedError("t1", "bad input")
        assert "t1" in str(err)
        assert "bad input" in str(err)
        assert err.task_id == "t1"
        assert err.code == "TASK_FAILED"

    def test_dependency_not_met_error(self) -> None:
        err = DependencyNotMetError("t2", ["t0", "t1"])
        assert "t2" in str(err)
        assert err.missing == ["t0", "t1"]
        assert err.code == "DEPENDENCY_NOT_MET"

    def test_plan_not_provided_error(self) -> None:
        err = PlanNotProvidedError()
        assert "No plan" in str(err)
        assert err.code == "PLAN_NOT_PROVIDED"


# ── ExecutionEngine Tests ─────────────────────────────────────────


class TestExecutionEngineConstruction:
    def test_creates_with_executor(self, stub_executor: StubExecutor) -> None:
        engine = ExecutionEngine(stub_executor)
        assert engine._executor is stub_executor


class TestExecuteSequential:
    def test_executes_all_steps(
        self, stub_executor: StubExecutor, engine: ExecutionEngine
    ) -> None:
        plan = make_simple_plan()
        report = engine.execute(plan)

        assert report.status == ExecutionPhase.COMPLETED
        assert report.total_tasks == 3
        assert report.completed_tasks == 3
        assert report.failed_tasks == 0
        assert stub_executor.call_count == 3

    def test_executes_in_order(self, stub_executor: StubExecutor, engine: ExecutionEngine) -> None:
        plan = make_simple_plan()
        engine.execute(plan)

        step_ids = [call[1].get("step_id", "") for call in stub_executor.calls]
        assert step_ids == ["plan-1", "exec-1", "val-1"]

    def test_context_passed_to_tasks(
        self, stub_executor: StubExecutor, engine: ExecutionEngine
    ) -> None:
        plan = make_simple_plan()
        ctx = {"project": "loopengine"}
        engine.execute(plan, context=ctx)

        for _, call_ctx in stub_executor.calls:
            assert call_ctx is not None
            assert call_ctx["project"] == "loopengine"

    def test_empty_plan(self, engine: ExecutionEngine) -> None:
        plan = PlanResult(goal="empty")
        report = engine.execute(plan)
        assert report.status == ExecutionPhase.COMPLETED
        assert report.total_tasks == 0

    def test_plan_with_no_steps_in_phase(self, engine: ExecutionEngine) -> None:
        plan = PlanResult(
            goal="test",
            phases=[PlanPhase(name="Empty", description="No steps")],
        )
        report = engine.execute(plan)
        assert report.status == ExecutionPhase.COMPLETED
        assert report.total_tasks == 0


class TestDependencyHandling:
    def test_blocks_tasks_with_unmet_deps(self) -> None:
        plan = PlanResult(
            goal="test deps",
            phases=[
                PlanPhase(
                    name="Phase1",
                    steps=[
                        PlanStep(
                            id="b",
                            description="B depends on A",
                            dependencies=["a"],
                        ),
                    ],
                ),
            ],
        )
        engine = ExecutionEngine(StubExecutor())
        report = engine.execute(plan)

        assert report.total_tasks == 1
        task = report.all_task_records[0]
        assert task.status == TaskStatus.BLOCKED
        assert "Dependencies not met" in task.error

    def test_resolves_deps_across_phases(self) -> None:
        plan = make_simple_plan()
        engine = ExecutionEngine(StubExecutor())
        report = engine.execute(plan)

        assert report.completed_tasks == 3
        for task in report.all_task_records:
            assert task.status == TaskStatus.COMPLETED


class TestFailureHandling:
    def test_records_failure(self) -> None:
        executor = StubExecutor(success=False, output="fail")
        engine = ExecutionEngine(executor)
        plan = make_simple_plan()
        report = engine.execute(plan)

        assert report.failed_tasks == 1
        assert report.status == ExecutionPhase.FAILED
        blocked = [t for t in report.all_task_records if t.status == TaskStatus.BLOCKED]
        assert len(blocked) == 2

    def test_stops_on_max_failures(self) -> None:
        executor = StubExecutor(fail_ids={"plan-1"})
        engine = ExecutionEngine(executor)
        plan = make_simple_plan()
        report = engine.execute(plan, max_failures=1)

        blocked = [t for t in report.all_task_records if t.status == TaskStatus.BLOCKED]
        assert len(blocked) > 0
        failed = [t for t in report.all_task_records if t.status == TaskStatus.FAILED]
        assert len(failed) == 1

    def test_exception_in_executor(self) -> None:
        engine = ExecutionEngine(FailingExecutor())
        plan = make_simple_plan()
        report = engine.execute(plan)

        assert report.failed_tasks == 1
        assert report.status == ExecutionPhase.FAILED
        failed = [t for t in report.all_task_records if t.status == TaskStatus.FAILED]
        assert len(failed) == 1
        assert "Executor exploded" in failed[0].error
        blocked = [t for t in report.all_task_records if t.status == TaskStatus.BLOCKED]
        assert len(blocked) == 2


class TestExecuteStep:
    def test_execute_single_step(self, engine: ExecutionEngine) -> None:
        step = PlanStep(
            id="s1",
            description="Do thing",
            expected_output="Result",
            acceptance_criteria=["Done"],
        )
        task = engine.execute_step(step, phase_name="Test")
        assert task.status == TaskStatus.COMPLETED
        assert task.result is not None
        assert task.result.output == "ok"

    def test_execute_step_with_missing_dep(self, engine: ExecutionEngine) -> None:
        step = PlanStep(
            id="s2",
            description="Needs s1",
            dependencies=["s1"],
        )
        task = engine.execute_step(step, completed_ids=set())
        assert task.status == TaskStatus.BLOCKED

    def test_execute_step_with_met_dep(self, engine: ExecutionEngine) -> None:
        step = PlanStep(
            id="s2",
            description="Needs s1",
            dependencies=["s1"],
        )
        task = engine.execute_step(step, completed_ids={"s1"})
        assert task.status == TaskStatus.COMPLETED


class TestReportMetadata:
    def test_goal_is_recorded(self, engine: ExecutionEngine) -> None:
        plan = PlanResult(goal="Build API")
        report = engine.execute(plan)
        assert report.goal == "Build API"

    def test_duration_is_recorded(self, engine: ExecutionEngine) -> None:
        plan = make_simple_plan()
        report = engine.execute(plan)
        assert report.total_duration_ms >= 0
        assert report.started_at > 0
        assert report.finished_at > 0

    def test_phase_records_are_created(self, engine: ExecutionEngine) -> None:
        plan = make_simple_plan()
        report = engine.execute(plan)
        assert len(report.phases) == 3
        assert report.phases[0].phase_name == "Plan"
        assert report.phases[1].phase_name == "Execute"
        assert report.phases[2].phase_name == "Validate"

    def test_phase_descriptions(self, engine: ExecutionEngine) -> None:
        plan = make_simple_plan()
        report = engine.execute(plan)
        assert report.phases[0].description == "Planning phase"
        assert report.phases[1].description == "Execution phase"
        assert report.phases[2].description == "Validation phase"
