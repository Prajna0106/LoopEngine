"""Integration tests — planner + executor + reflection pipeline."""

from __future__ import annotations

from loopengine.core.services.execution_engine import ExecutionEngine, ExecutionPhase
from loopengine.core.services.planner import PlannerService
from loopengine.core.services.reflection_service import ReflectionService
from tests.stubs.stub_executor import StubExecutor
from tests.stubs.stub_logger import StubLogger
from tests.stubs.stub_metrics import StubMetrics


class TestPlannerToExecutionPipeline:
    """Test the full pipeline: plan -> execute -> reflect."""

    def test_plan_and_execute(self) -> None:
        planner = PlannerService()
        executor = StubExecutor(output="Built successfully")
        engine = ExecutionEngine(executor)

        plan = planner.create_plan("Build authentication module")
        report = engine.execute(plan)

        assert report.status == ExecutionPhase.COMPLETED
        assert report.total_tasks > 0
        assert report.failed_tasks == 0
        assert executor.call_count == report.total_tasks

    def test_execute_with_failing_executor(self) -> None:
        planner = PlannerService()
        executor = StubExecutor(output="Error", success=False)
        engine = ExecutionEngine(executor)

        plan = planner.create_plan("Build feature")
        report = engine.execute(plan)

        assert report.status == ExecutionPhase.FAILED
        assert report.failed_tasks > 0

    def test_execute_with_max_failures(self) -> None:
        planner = PlannerService()
        executor = StubExecutor(output="Error", success=False)
        engine = ExecutionEngine(executor)

        plan = planner.create_plan("Build feature")
        report = engine.execute(plan, max_failures=1)

        assert report.failed_tasks >= 1

    def test_execute_empty_plan(self) -> None:
        executor = StubExecutor()
        engine = ExecutionEngine(executor)
        plan = PlannerService().create_plan("Do nothing specific")
        report = engine.execute(plan)
        assert report.status == ExecutionPhase.COMPLETED


class TestPlannerAndReflectionPipeline:
    """Test planner + reflection integration."""

    def test_reflection_on_successful_execution(self) -> None:
        planner = PlannerService()
        executor = StubExecutor(output="Success", success=True)
        engine = ExecutionEngine(executor)
        reflection = ReflectionService()

        plan = planner.create_plan("Build authentication")
        engine.execute(plan)

        result = reflection.reflect_on_results(
            _goal=plan.goal,
            results=[{"output": "Success", "success": True}],
            iteration=1,
        )
        assert result.decision.value in ("converged", "retry", "fix_and_retry")


class TestPlannerAndMetricsIntegration:
    """Test that services can work with metrics."""

    def test_plan_creates_steps(self) -> None:
        planner = PlannerService()
        plan = planner.create_plan("Build REST API with auth")
        total_steps = sum(len(p.steps) for p in plan.phases)
        assert total_steps > 0
        assert plan.goal == "Build REST API with auth"

    def test_execution_tracks_duration(self) -> None:
        executor = StubExecutor()
        engine = ExecutionEngine(executor)
        plan = PlannerService().create_plan("Quick task")
        report = engine.execute(plan)
        assert report.total_duration_ms >= 0


class TestStubIntegration:
    """Test that stubs work correctly in integration."""

    def test_stub_logger_records_calls(self) -> None:
        logger = StubLogger()
        logger.info("hello", key="value")
        logger.error("fail")
        assert len(logger.entries) == 2
        assert logger.entries[0] == ("info", "hello", {"key": "value"})
        assert logger.entries[1] == ("error", "fail", {})

    def test_stub_metrics_records_calls(self) -> None:
        metrics = StubMetrics()
        metrics.increment("req")
        metrics.gauge("connections", 5.0)
        metrics.timing("latency", 42.0)
        assert len(metrics.get_metrics()) == 3

    def test_stub_executor_tracks_calls(self) -> None:
        executor = StubExecutor()
        executor.execute("task 1")
        executor.execute("task 2")
        assert executor.call_count == 2
        assert executor.last_task == "task 2"

    def test_stub_agent_tracks_calls(self) -> None:
        from tests.stubs.stub_agent import StubAgent

        agent = StubAgent(content="Agent response")
        resp = agent.invoke("do something")
        assert agent.call_count == 1
        assert resp.content == "Agent response"
        assert agent.is_available()
