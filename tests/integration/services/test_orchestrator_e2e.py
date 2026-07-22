"""End-to-end integration tests — full workflow pipeline.

Tests the orchestrator wiring together planner, executor, reflection,
review, and validation through port interfaces.
"""

from __future__ import annotations

from typing import Any

import pytest

from loopengine.adapters.inbound.orchestrator import Orchestrator
from loopengine.adapters.outbound.agents.agent_executor import AgentExecutor
from loopengine.core.domain.exceptions.base import LoopEngineError
from loopengine.core.ports.outbound.executor_port import ExecutionResult, Executor
from loopengine.core.ports.outbound.reviewer_port import ReviewComment, ReviewResult, ReviewVerdict
from loopengine.core.ports.outbound.validator_port import (
    ValidationResult,
)
from loopengine.core.services.execution_engine import ExecutionEngine
from loopengine.core.services.planner import PlannerService
from loopengine.core.services.reflection_service import ReflectionService
from tests.stubs.stub_agent import StubAgent


class StubExecutor(Executor):
    """Simple stub executor for testing."""

    def __init__(self, output: str = "Done", success: bool = True) -> None:
        self._output = output
        self._success = success
        self.call_count = 0

    def execute(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        self.call_count += 1
        return ExecutionResult(
            output=self._output,
            success=self._success,
            artifacts=[],
            duration_ms=10.0,
        )

    def can_execute(self, task_type: str) -> bool:
        return True


class StubReviewer:
    """Stub reviewer for testing."""

    name = "stub-reviewer"

    def review(
        self,
        *,
        goal: str,
        artifacts: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> ReviewResult:
        return ReviewResult(
            verdict=ReviewVerdict.APPROVED,
            comments=[ReviewComment(message="Looks good")],
            summary="All clear",
            score=8.5,
        )


class StubValidator:
    """Stub validator for testing."""

    name = "stub-validator"

    def validate(
        self,
        paths: list[str],
        *,
        content: dict[str, str] | None = None,
        config: dict[str, Any] | None = None,
    ) -> ValidationResult:
        return ValidationResult(
            validator="stub-validator",
            passed=True,
            issues=[],
            duration_ms=5.0,
        )


class TestOrchestratorPlan:
    """Test orchestrator plan workflow."""

    def test_plan_creates_workflow(self) -> None:
        planner = PlannerService()
        executor = StubExecutor()
        engine = ExecutionEngine(executor)
        reflection = ReflectionService()

        orch = Orchestrator(
            planner=planner,
            executor=executor,
            execution_engine=engine,
            reflection=reflection,
        )

        result = orch.plan(goal="Build authentication service")

        assert result.workflow_id.startswith("wf-")
        assert len(result.phases) > 0
        assert "Plan created" in result.summary

    def test_plan_without_goal(self) -> None:
        planner = PlannerService()
        executor = StubExecutor()
        engine = ExecutionEngine(executor)
        reflection = ReflectionService()

        orch = Orchestrator(
            planner=planner,
            executor=executor,
            execution_engine=engine,
            reflection=reflection,
        )

        result = orch.plan()

        assert result.workflow_id.startswith("wf-")
        assert len(result.phases) > 0


class TestOrchestratorRun:
    """Test orchestrator run workflow."""

    def test_run_executes_all_tasks(self) -> None:
        planner = PlannerService()
        executor = StubExecutor(output="Built successfully")
        engine = ExecutionEngine(executor)
        reflection = ReflectionService()

        orch = Orchestrator(
            planner=planner,
            executor=executor,
            execution_engine=engine,
            reflection=reflection,
        )

        result = orch.run(goal="Build authentication service")

        assert result.workflow_id.startswith("wf-")
        assert result.status in ("completed", "failed")
        assert result.iterations >= 1
        assert executor.call_count > 0

    def test_run_dry_run(self) -> None:
        planner = PlannerService()
        executor = StubExecutor()
        engine = ExecutionEngine(executor)
        reflection = ReflectionService()

        orch = Orchestrator(
            planner=planner,
            executor=executor,
            execution_engine=engine,
            reflection=reflection,
        )

        result = orch.run(goal="Build feature", dry_run=True)

        assert result.status == "dry_run"
        assert executor.call_count == 0

    def test_run_with_reflection(self) -> None:
        planner = PlannerService()
        executor = StubExecutor(output="Success", success=True)
        engine = ExecutionEngine(executor)
        reflection = ReflectionService()

        orch = Orchestrator(
            planner=planner,
            executor=executor,
            execution_engine=engine,
            reflection=reflection,
        )

        result = orch.run(goal="Build REST API")

        assert "Reflection" in result.summary


class TestOrchestratorReview:
    """Test orchestrator review workflow."""

    def test_review_completed_workflow(self) -> None:
        planner = PlannerService()
        executor = StubExecutor(output="Done")
        engine = ExecutionEngine(executor)
        reflection = ReflectionService()
        reviewer = StubReviewer()

        orch = Orchestrator(
            planner=planner,
            executor=executor,
            execution_engine=engine,
            reflection=reflection,
            reviewers=[reviewer],
        )

        # First run to create the workflow
        run_result = orch.run(goal="Build feature")

        # Then review it
        review_result = orch.review(run_result.workflow_id)

        assert review_result.workflow_id == run_result.workflow_id
        assert review_result.verdict in ("converged", "needs_improvement")
        assert "Score" in review_result.summary

    def test_review_unknown_workflow(self) -> None:
        planner = PlannerService()
        executor = StubExecutor()
        engine = ExecutionEngine(executor)
        reflection = ReflectionService()

        orch = Orchestrator(
            planner=planner,
            executor=executor,
            execution_engine=engine,
            reflection=reflection,
        )

        with pytest.raises(LoopEngineError):
            orch.review("wf-nonexistent")


class TestOrchestratorImprove:
    """Test orchestrator improve workflow."""

    def test_improve_creates_iteration(self) -> None:
        planner = PlannerService()
        executor = StubExecutor(output="Improved")
        engine = ExecutionEngine(executor)
        reflection = ReflectionService()

        orch = Orchestrator(
            planner=planner,
            executor=executor,
            execution_engine=engine,
            reflection=reflection,
        )

        # First run
        run_result = orch.run(goal="Build feature")

        # Then improve
        improve_result = orch.improve(run_result.workflow_id)

        assert improve_result.iteration == 1
        assert len(improve_result.changes) > 0


class TestOrchestratorDoctor:
    """Test orchestrator doctor workflow."""

    def test_doctor_returns_checks(self) -> None:
        planner = PlannerService()
        executor = StubExecutor()
        engine = ExecutionEngine(executor)
        reflection = ReflectionService()

        orch = Orchestrator(
            planner=planner,
            executor=executor,
            execution_engine=engine,
            reflection=reflection,
        )

        result = orch.doctor()

        assert len(result.checks) > 0
        # Python check should always pass
        python_check = next(c for c in result.checks if c.name == "Python")
        assert python_check.ok


class TestOrchestratorInit:
    """Test orchestrator init workflow."""

    def test_init_creates_project(self, tmp_path: Any) -> None:
        from pathlib import Path

        planner = PlannerService()
        executor = StubExecutor()
        engine = ExecutionEngine(executor)
        reflection = ReflectionService()

        orch = Orchestrator(
            planner=planner,
            executor=executor,
            execution_engine=engine,
            reflection=reflection,
        )

        project_dir = str(tmp_path / "new-project")
        result = orch.init(project_dir)

        assert Path(result.project_path).exists()
        assert Path(result.config_path).exists()


class TestAgentExecutor:
    """Test the AgentExecutor adapter."""

    def test_agent_executor_wraps_agent(self) -> None:
        agent = StubAgent(content="Agent response")
        executor = AgentExecutor(agent)

        result = executor.execute("Do something")

        assert result.success is True
        assert result.output == "Agent response"
        assert result.metadata["agent"] == "stub-agent"

    def test_agent_executor_handles_exception(self) -> None:
        class FailingAgent:
            name = "failing"
            model = "failing"

            def invoke(self, prompt: str, **kwargs: Any) -> Any:
                raise RuntimeError("Agent crashed")

            def is_available(self) -> bool:
                return True

        executor = AgentExecutor(FailingAgent())  # type: ignore[arg-type]
        result = executor.execute("Do something")

        assert result.success is False
        assert "Agent error" in result.output

    def test_agent_executor_can_execute_anything(self) -> None:
        agent = StubAgent(content="ok")
        executor = AgentExecutor(agent)

        assert executor.can_execute("code") is True
        assert executor.can_execute("test") is True
