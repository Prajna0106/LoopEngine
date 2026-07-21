"""Unit tests for PlannerService."""

from __future__ import annotations

import pytest

from loopengine.core.domain.exceptions.planner_exceptions import (
    PlanCyclicDependencyError,
    PlanError,
    PlanValidationError,
)
from loopengine.core.ports.outbound.planner_port import (
    PlanPhase,
    PlanResult,
    PlanStep,
    StepComplexity,
    StepPriority,
)
from loopengine.core.services.planner import PlannerService


@pytest.fixture()
def planner() -> PlannerService:
    return PlannerService()


# ── Data Model Tests ──────────────────────────────────────────────


class TestPlanStep:
    def test_defaults(self) -> None:
        step = PlanStep(id="s1", description="Do something")
        assert step.id == "s1"
        assert step.description == "Do something"
        assert step.priority == StepPriority.MEDIUM
        assert step.dependencies == []
        assert step.complexity == StepComplexity.MODERATE
        assert step.expected_output == ""
        assert step.acceptance_criteria == []

    def test_full_construction(self) -> None:
        step = PlanStep(
            id="s1",
            description="Do something",
            priority=StepPriority.HIGH,
            dependencies=["s0"],
            complexity=StepComplexity.COMPLEX,
            expected_output="Result",
            acceptance_criteria=["Works correctly"],
        )
        assert step.priority == StepPriority.HIGH
        assert step.dependencies == ["s0"]
        assert step.complexity == StepComplexity.COMPLEX
        assert step.expected_output == "Result"
        assert step.acceptance_criteria == ["Works correctly"]

    def test_frozen(self) -> None:
        step = PlanStep(id="s1", description="Do something")
        with pytest.raises(AttributeError):
            step.id = "s2"  # type: ignore[misc]


class TestPlanPhase:
    def test_defaults(self) -> None:
        phase = PlanPhase(name="Test")
        assert phase.name == "Test"
        assert phase.steps == []
        assert phase.description == ""

    def test_with_steps(self) -> None:
        step = PlanStep(id="s1", description="Step 1")
        phase = PlanPhase(name="Phase", steps=[step], description="Desc")
        assert len(phase.steps) == 1
        assert phase.description == "Desc"


class TestPlanResult:
    def test_defaults(self) -> None:
        plan = PlanResult(goal="Do something")
        assert plan.goal == "Do something"
        assert plan.phases == []
        assert plan.acceptance_criteria == []
        assert plan.metadata == {}


class TestEnums:
    def test_step_priority_values(self) -> None:
        assert StepPriority.CRITICAL.value == "critical"
        assert StepPriority.HIGH.value == "high"
        assert StepPriority.MEDIUM.value == "medium"
        assert StepPriority.LOW.value == "low"

    def test_step_complexity_values(self) -> None:
        assert StepComplexity.TRIVIAL.value == "trivial"
        assert StepComplexity.SIMPLE.value == "simple"
        assert StepComplexity.MODERATE.value == "moderate"
        assert StepComplexity.COMPLEX.value == "complex"
        assert StepComplexity.VERY_COMPLEX.value == "very_complex"


# ── Exception Tests ───────────────────────────────────────────────


class TestExceptions:
    def test_plan_error(self) -> None:
        err = PlanError("test message")
        assert str(err) == "test message"
        assert err.code == "PLAN_ERROR"

    def test_plan_validation_error(self) -> None:
        err = PlanValidationError("bad plan", issues=["issue1", "issue2"])
        assert err.issues == ["issue1", "issue2"]
        assert err.code == "PLAN_VALIDATION_ERROR"

    def test_plan_cyclic_dependency_error(self) -> None:
        err = PlanCyclicDependencyError(cycle=["a", "b", "c"])
        assert "a -> b -> c" in str(err)
        assert err.cycle == ["a", "b", "c"]
        assert err.code == "PLAN_CYCLIC_DEPENDENCY"


# ── PlannerService Goal Analysis Tests ────────────────────────────


class TestGoalAnalysis:
    def test_empty_goal_raises(self, planner: PlannerService) -> None:
        with pytest.raises(PlanError, match="Goal cannot be empty"):
            planner.create_plan("")

    def test_whitespace_only_goal_raises(self, planner: PlannerService) -> None:
        with pytest.raises(PlanError, match="Goal cannot be empty"):
            planner.create_plan("   ")

    def test_create_intent(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Add a new authentication module")
        assert plan.metadata["intent"] == "create"
        assert any(p.name == "Plan" for p in plan.phases)
        assert any(p.name == "Execute" for p in plan.phases)
        assert any(p.name == "Validate" for p in plan.phases)

    def test_fix_intent(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Fix the login timeout bug")
        assert plan.metadata["intent"] == "fix"
        assert any(p.name == "Investigate" for p in plan.phases)
        assert any(p.name == "Fix" for p in plan.phases)
        assert any(p.name == "Verify" for p in plan.phases)

    def test_refactor_intent(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Refactor the payment service")
        assert plan.metadata["intent"] == "refactor"
        assert any(p.name == "Analyze" for p in plan.phases)
        assert any(p.name == "Refactor" for p in plan.phases)

    def test_test_intent(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Add tests for the user module")
        assert plan.metadata["intent"] == "test"

    def test_document_intent(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Write documentation for the API")
        assert plan.metadata["intent"] == "document"

    def test_optimize_intent(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Optimize database query performance")
        assert plan.metadata["intent"] == "optimize"

    def test_general_intent(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Review the codebase")
        assert plan.metadata["intent"] == "general"


class TestScopeDetection:
    def test_large_scope(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Build a new microservices architecture")
        assert plan.metadata["scope"] == "large"

    def test_medium_scope(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Add a new API endpoint")
        assert plan.metadata["scope"] == "medium"

    def test_small_scope(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Fix a typo in the function name")
        assert plan.metadata["scope"] == "small"


# ── PlannerService Plan Structure Tests ───────────────────────────


class TestPlanStructure:
    def test_plan_has_phases(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Implement user authentication")
        assert len(plan.phases) > 0

    def test_plan_has_goal(self, planner: PlannerService) -> None:
        goal = "Add a caching layer"
        plan = planner.create_plan(goal)
        assert plan.goal == goal

    def test_plan_has_acceptance_criteria(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Add tests for the API")
        assert len(plan.acceptance_criteria) > 0

    def test_steps_have_ids(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Fix the login bug")
        for phase in plan.phases:
            for step in phase.steps:
                assert step.id, f"Step in phase '{phase.name}' has no ID"

    def test_steps_have_descriptions(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Refactor the payment module")
        for phase in plan.phases:
            for step in phase.steps:
                assert step.description, f"Step '{step.id}' has no description"

    def test_steps_have_priorities(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Add a new feature")
        for phase in plan.phases:
            for step in phase.steps:
                assert isinstance(step.priority, StepPriority)

    def test_steps_have_complexity(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Build a complex system")
        for phase in plan.phases:
            for step in phase.steps:
                assert isinstance(step.complexity, StepComplexity)


class TestPlanPhaseSteps:
    def test_plan_phases_have_steps(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Implement authentication")
        for phase in plan.phases:
            assert len(phase.steps) > 0, f"Phase '{phase.name}' has no steps"

    def test_plan_steps_have_expected_output(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Fix the bug")
        for phase in plan.phases:
            for step in phase.steps:
                assert step.expected_output, f"Step '{step.id}' has no expected output"

    def test_plan_steps_have_acceptance_criteria(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Add tests")
        for phase in plan.phases:
            for step in phase.steps:
                assert len(step.acceptance_criteria) > 0, (
                    f"Step '{step.id}' has no acceptance criteria"
                )


# ── Dependency Validation Tests ───────────────────────────────────


class TestDependencyValidation:
    def test_dependencies_reference_valid_steps(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Implement a new feature")
        all_ids = set()
        for phase in plan.phases:
            for step in phase.steps:
                all_ids.add(step.id)

        for phase in plan.phases:
            for step in phase.steps:
                for dep in step.dependencies:
                    assert dep in all_ids, f"Step '{step.id}' depends on unknown step '{dep}'"

    def test_no_duplicate_step_ids(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Fix the critical bug")
        ids = []
        for phase in plan.phases:
            for step in phase.steps:
                ids.append(step.id)
        assert len(ids) == len(set(ids)), f"Duplicate step IDs found: {ids}"


# ── Context and Constraints Tests ─────────────────────────────────


class TestContextAndConstraints:
    def test_context_is_recorded_in_metadata(self, planner: PlannerService) -> None:
        context = {"language": "python", "framework": "fastapi"}
        plan = planner.create_plan("Add an endpoint", context=context)
        assert plan.metadata["context_keys"] == ["language", "framework"]

    def test_constraints_are_recorded_in_metadata(self, planner: PlannerService) -> None:
        constraints = ["must use async", "no external deps"]
        plan = planner.create_plan("Implement feature", constraints=constraints)
        assert plan.metadata["constraints"] == constraints


# ── Acceptance Criteria Tests ─────────────────────────────────────


class TestAcceptanceCriteria:
    def test_test_goal_has_test_criteria(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Add unit tests for the API")
        assert "All tests pass" in plan.acceptance_criteria

    def test_optimize_goal_has_performance_criteria(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Optimize query performance")
        assert "Performance targets met" in plan.acceptance_criteria

    def test_default_criteria_when_no_match(self, planner: PlannerService) -> None:
        plan = planner.create_plan("Do something vague")
        assert "Goal is achieved as specified" in plan.acceptance_criteria
