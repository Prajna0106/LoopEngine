"""Orchestrator — concrete implementation of OrchestratorPort.

Wires together planner, execution engine, reflection, review, and
validation into a coherent workflow.  All dependencies are injected
through the constructor, following Clean Architecture principles.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import structlog

from loopengine.core.ports.inbound.orchestrator_port import (
    CheckItem,
    DoctorResult,
    ImproveResult,
    InitResult,
    OrchestratorPort,
    PlanResult,
    ReviewResult,
    RunResult,
)

if TYPE_CHECKING:
    from loopengine.core.ports.outbound.executor_port import Executor
    from loopengine.core.ports.outbound.reviewer_port import Reviewer
    from loopengine.core.ports.outbound.validator_port import Validator
    from loopengine.core.services.execution_engine import ExecutionEngine
    from loopengine.core.services.planner import PlannerService
    from loopengine.core.services.reflection_service import ReflectionService
    from loopengine.infrastructure.config.schema import LoopEngineConfig

log = structlog.get_logger()


class Orchestrator(OrchestratorPort):
    """Application-layer orchestrator that coordinates all workflow stages.

    Dependencies are injected — no concrete implementations are imported
    at the module level.  Every component communicates through port
    interfaces.
    """

    def __init__(
        self,
        *,
        planner: PlannerService,
        executor: Executor,
        execution_engine: ExecutionEngine,
        reflection: ReflectionService,
        config: LoopEngineConfig | None = None,
        validators: list[Validator] | None = None,
        reviewers: list[Reviewer] | None = None,
    ) -> None:
        self._planner = planner
        self._executor = executor
        self._engine = execution_engine
        self._reflection = reflection
        self._config = config
        self._validators = validators or []
        self._reviewers = reviewers or []
        self._workflows: dict[str, dict[str, Any]] = {}

    # ── init ────────────────────────────────────────────────────────

    def init(self, project_path: str) -> InitResult:
        """Initialise a LoopEngine project."""
        from pathlib import Path

        path = Path(project_path).resolve()
        path.mkdir(parents=True, exist_ok=True)

        config_path = path / "loop.yaml"
        if not config_path.exists():
            config_path.write_text(
                "# LoopEngine configuration\n"
                "engine:\n"
                "  max_iterations: 5\n"
                "  default_agent: claude\n\n"
                "agents:\n"
                "  claude:\n"
                "    model: claude-sonnet-4-20250514\n"
                "    api_key_env: ANTHROPIC_API_KEY\n\n"
                "validation:\n"
                "  linters: [ruff]\n"
                "  type_checkers: [mypy]\n"
                "  test_runner: pytest\n",
                encoding="utf-8",
            )

        log.info("project_init", path=str(path))
        return InitResult(
            project_path=str(path),
            config_path=str(config_path),
        )

    # ── doctor ──────────────────────────────────────────────────────

    def doctor(self) -> DoctorResult:
        """Run environment health checks."""
        import shutil

        checks = [
            CheckItem(
                name="Python",
                ok=True,
                detail=f"{__import__('sys').version.split()[0]}",
            ),
            CheckItem(
                name="Git",
                ok=shutil.which("git") is not None,
                detail="installed" if shutil.which("git") else "not found",
            ),
        ]

        # Check configured agents
        if self._config:
            for name in self._config.agents:
                agent_cfg = self._config.agents[name]
                api_key_env = agent_cfg.api_key_env
                import os

                has_key = bool(os.environ.get(api_key_env))
                checks.append(
                    CheckItem(
                        name=f"Agent: {name}",
                        ok=has_key,
                        detail=f"API key ({api_key_env}) {'set' if has_key else 'missing'}",
                    )
                )

        log.info("doctor_complete", checks=len(checks))
        return DoctorResult(checks=checks)

    # ── plan ────────────────────────────────────────────────────────

    def plan(self, config_path: str | None = None, *, goal: str | None = None) -> PlanResult:  # noqa: ARG002
        """Plan a workflow from a goal or configuration."""
        effective_goal = goal or "Execute configured workflow"

        log.info("plan_start", goal=effective_goal)

        plan_result = self._planner.create_plan(effective_goal)

        workflow_id = f"wf-{uuid.uuid4().hex[:8]}"
        self._workflows[workflow_id] = {
            "goal": effective_goal,
            "plan": plan_result,
            "status": "planned",
        }

        phase_names = [p.name for p in plan_result.phases]
        summary = (
            f"Plan created: {len(plan_result.phases)} phase(s), "
            f"{sum(len(p.steps) for p in plan_result.phases)} step(s)"
        )

        log.info("plan_complete", workflow_id=workflow_id, phases=phase_names)
        return PlanResult(
            workflow_id=workflow_id,
            phases=phase_names,
            summary=summary,
        )

    # ── run ─────────────────────────────────────────────────────────

    def run(
        self,
        config_path: str | None = None,  # noqa: ARG002
        *,
        dry_run: bool = False,
        goal: str | None = None,
    ) -> RunResult:
        """Execute a workflow."""
        effective_goal = goal or "Execute configured workflow"

        log.info("run_start", goal=effective_goal, dry_run=dry_run)

        # Create plan
        plan_result = self._planner.create_plan(effective_goal)
        workflow_id = f"wf-{uuid.uuid4().hex[:8]}"

        if dry_run:
            self._workflows[workflow_id] = {
                "goal": effective_goal,
                "plan": plan_result,
                "status": "dry_run",
            }
            phase_names = [p.name for p in plan_result.phases]
            return RunResult(
                workflow_id=workflow_id,
                status="dry_run",
                iterations=0,
                summary=f"Dry run: {len(phase_names)} phase(s) planned",
            )

        # Execute
        report = self._engine.execute(plan_result)

        # Collect results for reflection
        results = []
        for task in report.all_task_records:
            if task.result:
                results.append(
                    {
                        "output": task.result.output,
                        "success": task.result.success,
                        "task_id": task.step_id,
                    }
                )

        # Reflect
        reflection = self._reflection.reflect_on_results(
            _goal=effective_goal,
            results=results,
            iteration=0,
        )

        # Store workflow
        self._workflows[workflow_id] = {
            "goal": effective_goal,
            "plan": plan_result,
            "report": report,
            "reflection": reflection,
            "status": report.status.value,
        }

        status = report.status.value
        summary = (
            f"Completed: {report.completed_tasks}/{report.total_tasks} tasks "
            f"({report.success_rate:.0f}% success). "
            f"Reflection: {reflection.decision.value}"
        )

        log.info("run_complete", workflow_id=workflow_id, status=status)
        return RunResult(
            workflow_id=workflow_id,
            status=status,
            iterations=1,
            summary=summary,
        )

    # ── review ──────────────────────────────────────────────────────

    def review(self, workflow_id: str) -> ReviewResult:
        """Review results of a completed workflow."""
        if workflow_id not in self._workflows:
            from loopengine.core.domain.exceptions.workflow_exceptions import (
                WorkflowNotFoundError,
            )

            raise WorkflowNotFoundError(workflow_id)

        wf = self._workflows[workflow_id]
        goal = wf.get("goal", "")
        report = wf.get("report")

        # Collect artifacts from execution
        artifacts: list[dict[str, Any]] = []
        if report:
            for task in report.all_task_records:
                if task.result:
                    artifacts.append(
                        {
                            "kind": "execution_result",
                            "content": task.result.output,
                            "success": task.result.success,
                        }
                    )

        # Run reviewers
        all_issues: list[str] = []
        total_score = 0.0
        reviewer_count = 0

        for reviewer in self._reviewers:
            try:
                review_result = reviewer.review(goal=goal, artifacts=artifacts)
                total_score += review_result.score
                reviewer_count += 1
                for comment in review_result.comments:
                    all_issues.append(f"[{reviewer.name}] {comment.message}")
            except Exception as exc:
                log.warning("reviewer_failed", reviewer=reviewer.name, error=str(exc))

        avg_score = total_score / reviewer_count if reviewer_count > 0 else 0.0
        verdict = "converged" if avg_score >= 7.0 and not all_issues else "needs_improvement"

        summary = f"Score: {avg_score:.1f}/10. {len(all_issues)} issue(s) found."
        log.info("review_complete", workflow_id=workflow_id, verdict=verdict, score=avg_score)

        return ReviewResult(
            workflow_id=workflow_id,
            verdict=verdict,
            issues=all_issues,
            summary=summary,
        )

    # ── improve ─────────────────────────────────────────────────────

    def improve(self, workflow_id: str) -> ImproveResult:
        """Trigger an improvement iteration on an existing workflow."""
        if workflow_id not in self._workflows:
            from loopengine.core.domain.exceptions.workflow_exceptions import (
                WorkflowNotFoundError,
            )

            raise WorkflowNotFoundError(workflow_id)

        wf = self._workflows[workflow_id]
        goal = wf.get("goal", "")
        iteration = wf.get("iteration", 0) + 1

        log.info("improve_start", workflow_id=workflow_id, iteration=iteration)

        # Re-plan with improvement context
        plan_result = self._planner.create_plan(
            goal,
            context={"previous_iteration": iteration, "improve": True},
        )

        # Re-execute
        report = self._engine.execute(plan_result)

        # Reflect
        results = []
        for task in report.all_task_records:
            if task.result:
                results.append(
                    {
                        "output": task.result.output,
                        "success": task.result.success,
                        "task_id": task.step_id,
                    }
                )

        reflection = self._reflection.reflect_on_results(
            _goal=goal,
            results=results,
            iteration=iteration,
        )

        # Update workflow
        wf["report"] = report
        wf["reflection"] = reflection
        wf["iteration"] = iteration
        wf["status"] = report.status.value

        changes = [f"Iteration {iteration}: {report.completed_tasks} tasks completed"]
        summary = f"Impovement iteration {iteration}. Reflection: {reflection.decision.value}"

        log.info("improve_complete", workflow_id=workflow_id, iteration=iteration)
        return ImproveResult(
            workflow_id=workflow_id,
            iteration=iteration,
            changes=changes,
            summary=summary,
        )
