"""Planner service — transforms goals into structured execution plans.

This module provides a domain service that decomposes high-level goals
into ordered phases and steps, each with metadata like priority,
complexity, dependencies, and acceptance criteria.
"""

from __future__ import annotations

import re
from typing import Any

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


class PlannerService:
    """Domain service that decomposes goals into structured plans.

    The planner operates in three stages:
    1. Goal analysis — extract intent, scope, and constraints
    2. Phase decomposition — organize work into logical phases
    3. Step generation — create granular tasks with full metadata
    """

    def create_plan(
        self,
        goal: str,
        *,
        context: dict[str, Any] | None = None,
        constraints: list[str] | None = None,
    ) -> PlanResult:
        """Produce a structured plan for achieving *goal*.

        Parameters
        ----------
        goal:
            Natural-language engineering request.
        context:
            Optional project context (languages, frameworks, structure).
        constraints:
            Optional hard constraints the plan must satisfy.

        Returns
        -------
        PlanResult
            A fully structured plan with phases, steps, and criteria.

        Raises
        ------
        PlanError
            If planning fails due to invalid input or unresolvable constraints.
        """
        if not goal or not goal.strip():
            raise PlanError("Goal cannot be empty")

        context = context or {}
        constraints = constraints or []

        analysis = self._analyze_goal(goal)
        phases = self._decompose_phases(goal, analysis, context)
        global_criteria = self._extract_global_criteria(goal, analysis)

        plan = PlanResult(
            goal=goal.strip(),
            phases=phases,
            acceptance_criteria=global_criteria,
            metadata={
                "intent": analysis["intent"],
                "scope": analysis["scope"],
                "constraints": constraints,
                "context_keys": list(context.keys()),
            },
        )

        self._validate_plan(plan)
        return plan

    # ── Goal Analysis ──────────────────────────────────────────────

    def _analyze_goal(self, goal: str) -> dict[str, Any]:
        """Extract intent, scope, and keywords from the goal."""
        lower = goal.lower()

        intent = self._detect_intent(lower)
        scope = self._detect_scope(lower)
        keywords = self._extract_keywords(lower)

        return {
            "intent": intent,
            "scope": scope,
            "keywords": keywords,
        }

    def _detect_intent(self, lower_goal: str) -> str:
        """Classify the primary intent of the goal."""
        if any(w in lower_goal for w in ("test", "verify", "validate")):
            return "test"
        if any(w in lower_goal for w in ("fix", "repair", "resolve", "patch")):
            return "fix"
        if any(w in lower_goal for w in ("refactor", "restructure", "reorganize", "clean")):
            return "refactor"
        if any(w in lower_goal for w in ("add", "implement", "create", "build", "introduce")):
            return "create"
        if any(w in lower_goal for w in ("document", "write doc", "add comment")):
            return "document"
        if any(w in lower_goal for w in ("optimize", "improve performance", "speed up")):
            return "optimize"
        return "general"

    def _detect_scope(self, lower_goal: str) -> str:
        """Estimate the scope of the goal."""
        large_indicators = ("system", "architecture", "infrastructure", "platform", "framework")
        medium_indicators = ("module", "component", "service", "feature", "api", "endpoint")
        small_indicators = ("file", "function", "method", "variable", "typo", "line")

        if any(w in lower_goal for w in large_indicators):
            return "large"
        if any(w in lower_goal for w in medium_indicators):
            return "medium"
        if any(w in lower_goal for w in small_indicators):
            return "small"
        return "medium"

    def _extract_keywords(self, lower_goal: str) -> list[str]:
        """Extract meaningful keywords from the goal."""
        stop_words = {
            "a",
            "an",
            "the",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "shall",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "and",
            "but",
            "or",
            "not",
            "so",
            "if",
            "that",
            "this",
            "it",
            "its",
            "i",
            "we",
            "you",
            "they",
            "he",
            "she",
            "me",
            "us",
            "him",
            "her",
            "my",
            "our",
            "your",
            "their",
            "what",
            "which",
            "who",
            "how",
            "when",
            "where",
            "why",
        }
        words = re.findall(r"[a-z]+", lower_goal)
        return [w for w in words if w not in stop_words and len(w) > 2]

    # ── Phase Decomposition ────────────────────────────────────────

    def _decompose_phases(
        self,
        goal: str,
        analysis: dict[str, Any],
        context: dict[str, Any],
    ) -> list[PlanPhase]:
        """Break the goal into ordered phases."""
        intent = analysis["intent"]
        scope = analysis["scope"]

        if intent == "create":
            return self._build_create_phases(goal, scope, context)
        if intent == "fix":
            return self._build_fix_phases(goal, scope, context)
        if intent == "refactor":
            return self._build_refactor_phases(goal, scope, context)
        if intent == "test":
            return self._build_test_phases(goal, scope, context)
        if intent == "document":
            return self._build_document_phases(goal, scope, context)
        if intent == "optimize":
            return self._build_optimize_phases(goal, scope, context)
        return self._build_general_phases(goal, scope, context)

    def _build_create_phases(
        self, _goal: str, scope: str, _context: dict[str, Any]
    ) -> list[PlanPhase]:
        """Build phases for creation tasks."""
        plan_phase = PlanPhase(
            name="Plan",
            description="Analyze requirements and design the approach",
            steps=[
                PlanStep(
                    id="plan-1",
                    description="Analyze requirements and define success criteria",
                    priority=StepPriority.HIGH,
                    complexity=StepComplexity.SIMPLE,
                    expected_output="Clear requirements document",
                    acceptance_criteria=[
                        "Requirements are specific and measurable",
                        "Success criteria are defined",
                    ],
                ),
                PlanStep(
                    id="plan-2",
                    description="Design the implementation approach",
                    priority=StepPriority.HIGH,
                    complexity=StepComplexity.MODERATE,
                    dependencies=["plan-1"],
                    expected_output="Design document or architecture plan",
                    acceptance_criteria=[
                        "Approach is feasible within constraints",
                        "Edge cases are considered",
                    ],
                ),
            ],
        )

        execute_phase = PlanPhase(
            name="Execute",
            description="Implement the solution",
            steps=[
                PlanStep(
                    id="exec-1",
                    description="Implement core functionality",
                    priority=StepPriority.CRITICAL,
                    complexity=(
                        StepComplexity.COMPLEX if scope == "large" else StepComplexity.MODERATE
                    ),
                    dependencies=["plan-2"],
                    expected_output="Working implementation",
                    acceptance_criteria=[
                        "Core functionality works as specified",
                        "Code follows project conventions",
                    ],
                ),
            ],
        )

        validate_phase = PlanPhase(
            name="Validate",
            description="Verify the implementation",
            steps=[
                PlanStep(
                    id="val-1",
                    description="Run tests and validation checks",
                    priority=StepPriority.HIGH,
                    complexity=StepComplexity.SIMPLE,
                    dependencies=["exec-1"],
                    expected_output="Validation report",
                    acceptance_criteria=[
                        "All tests pass",
                        "No lint errors",
                        "No type errors",
                    ],
                ),
            ],
        )

        return [plan_phase, execute_phase, validate_phase]

    def _build_fix_phases(
        self, _goal: str, _scope: str, _context: dict[str, Any]
    ) -> list[PlanPhase]:
        """Build phases for bug fix tasks."""
        return [
            PlanPhase(
                name="Investigate",
                description="Understand the bug and its root cause",
                steps=[
                    PlanStep(
                        id="inv-1",
                        description="Reproduce the issue and gather evidence",
                        priority=StepPriority.CRITICAL,
                        complexity=StepComplexity.SIMPLE,
                        expected_output="Reproduction steps and error details",
                        acceptance_criteria=[
                            "Bug can be reliably reproduced",
                            "Error messages are captured",
                        ],
                    ),
                    PlanStep(
                        id="inv-2",
                        description="Identify root cause",
                        priority=StepPriority.CRITICAL,
                        dependencies=["inv-1"],
                        complexity=StepComplexity.MODERATE,
                        expected_output="Root cause analysis",
                        acceptance_criteria=[
                            "Root cause is identified",
                            "Impact scope is understood",
                        ],
                    ),
                ],
            ),
            PlanPhase(
                name="Fix",
                description="Implement the fix",
                steps=[
                    PlanStep(
                        id="fix-1",
                        description="Implement the bug fix",
                        priority=StepPriority.CRITICAL,
                        dependencies=["inv-2"],
                        complexity=StepComplexity.MODERATE,
                        expected_output="Code fix",
                        acceptance_criteria=[
                            "Fix addresses root cause",
                            "No regressions introduced",
                        ],
                    ),
                ],
            ),
            PlanPhase(
                name="Verify",
                description="Confirm the fix works",
                steps=[
                    PlanStep(
                        id="ver-1",
                        description="Test the fix and run validation suite",
                        priority=StepPriority.HIGH,
                        dependencies=["fix-1"],
                        complexity=StepComplexity.SIMPLE,
                        expected_output="Verification report",
                        acceptance_criteria=[
                            "Original bug no longer occurs",
                            "Existing tests still pass",
                        ],
                    ),
                ],
            ),
        ]

    def _build_refactor_phases(
        self, _goal: str, scope: str, _context: dict[str, Any]
    ) -> list[PlanPhase]:
        """Build phases for refactoring tasks."""
        return [
            PlanPhase(
                name="Analyze",
                description="Understand current state and plan changes",
                steps=[
                    PlanStep(
                        id="ana-1",
                        description="Analyze current code structure and dependencies",
                        priority=StepPriority.HIGH,
                        complexity=StepComplexity.MODERATE,
                        expected_output="Code analysis report",
                        acceptance_criteria=[
                            "Dependencies are mapped",
                            "Coupling points identified",
                        ],
                    ),
                    PlanStep(
                        id="ana-2",
                        description="Plan refactoring steps",
                        priority=StepPriority.HIGH,
                        dependencies=["ana-1"],
                        complexity=StepComplexity.SIMPLE,
                        expected_output="Refactoring plan",
                        acceptance_criteria=[
                            "Changes are incremental",
                            "Behavior preservation strategy defined",
                        ],
                    ),
                ],
            ),
            PlanPhase(
                name="Refactor",
                description="Apply refactoring changes",
                steps=[
                    PlanStep(
                        id="ref-1",
                        description="Apply refactoring changes incrementally",
                        priority=StepPriority.CRITICAL,
                        dependencies=["ana-2"],
                        complexity=(
                            StepComplexity.COMPLEX if scope == "large" else StepComplexity.MODERATE
                        ),
                        expected_output="Refactored code",
                        acceptance_criteria=[
                            "Code structure is improved",
                            "Behavior is preserved",
                        ],
                    ),
                ],
            ),
            PlanPhase(
                name="Validate",
                description="Ensure behavior is preserved",
                steps=[
                    PlanStep(
                        id="val-1",
                        description="Run full test suite to verify no regressions",
                        priority=StepPriority.HIGH,
                        dependencies=["ref-1"],
                        complexity=StepComplexity.SIMPLE,
                        expected_output="Test results",
                        acceptance_criteria=[
                            "All tests pass",
                            "Code coverage maintained or improved",
                        ],
                    ),
                ],
            ),
        ]

    def _build_test_phases(
        self, _goal: str, _scope: str, _context: dict[str, Any]
    ) -> list[PlanPhase]:
        """Build phases for test creation tasks."""
        return [
            PlanPhase(
                name="Plan",
                description="Design test strategy",
                steps=[
                    PlanStep(
                        id="tplan-1",
                        description="Identify test cases and edge cases",
                        priority=StepPriority.HIGH,
                        complexity=StepComplexity.MODERATE,
                        expected_output="Test plan with cases list",
                        acceptance_criteria=[
                            "Edge cases are identified",
                            "Test data requirements defined",
                        ],
                    ),
                ],
            ),
            PlanPhase(
                name="Implement",
                description="Write test code",
                steps=[
                    PlanStep(
                        id="timpl-1",
                        description="Implement test cases",
                        priority=StepPriority.CRITICAL,
                        dependencies=["tplan-1"],
                        complexity=StepComplexity.MODERATE,
                        expected_output="Test code",
                        acceptance_criteria=[
                            "Tests are well-structured",
                            "Tests follow project conventions",
                        ],
                    ),
                ],
            ),
            PlanPhase(
                name="Run",
                description="Execute tests and analyze results",
                steps=[
                    PlanStep(
                        id="trun-1",
                        description="Run tests and verify results",
                        priority=StepPriority.HIGH,
                        dependencies=["timpl-1"],
                        complexity=StepComplexity.SIMPLE,
                        expected_output="Test report",
                        acceptance_criteria=[
                            "All new tests pass",
                            "Existing tests unaffected",
                        ],
                    ),
                ],
            ),
        ]

    def _build_document_phases(
        self, _goal: str, _scope: str, _context: dict[str, Any]
    ) -> list[PlanPhase]:
        """Build phases for documentation tasks."""
        return [
            PlanPhase(
                name="Analyze",
                description="Understand what needs documentation",
                steps=[
                    PlanStep(
                        id="dan-1",
                        description="Identify documentation gaps",
                        priority=StepPriority.HIGH,
                        complexity=StepComplexity.SIMPLE,
                        expected_output="Documentation gaps list",
                        acceptance_criteria=[
                            "Gaps are prioritized",
                            "Target audience identified",
                        ],
                    ),
                ],
            ),
            PlanPhase(
                name="Write",
                description="Create documentation",
                steps=[
                    PlanStep(
                        id="dwr-1",
                        description="Write documentation content",
                        priority=StepPriority.CRITICAL,
                        dependencies=["dan-1"],
                        complexity=StepComplexity.MODERATE,
                        expected_output="Documentation draft",
                        acceptance_criteria=[
                            "Content is accurate",
                            "Examples are provided",
                        ],
                    ),
                ],
            ),
        ]

    def _build_optimize_phases(
        self, _goal: str, _scope: str, _context: dict[str, Any]
    ) -> list[PlanPhase]:
        """Build phases for optimization tasks."""
        return [
            PlanPhase(
                name="Profile",
                description="Identify performance bottlenecks",
                steps=[
                    PlanStep(
                        id="prof-1",
                        description="Profile and identify bottlenecks",
                        priority=StepPriority.CRITICAL,
                        complexity=StepComplexity.COMPLEX,
                        expected_output="Performance analysis report",
                        acceptance_criteria=[
                            "Bottlenecks are quantified",
                            "Baseline metrics established",
                        ],
                    ),
                ],
            ),
            PlanPhase(
                name="Optimize",
                description="Apply optimizations",
                steps=[
                    PlanStep(
                        id="opt-1",
                        description="Implement optimizations",
                        priority=StepPriority.CRITICAL,
                        dependencies=["prof-1"],
                        complexity=StepComplexity.COMPLEX,
                        expected_output="Optimized code",
                        acceptance_criteria=[
                            "Performance improved measurably",
                            "Correctness preserved",
                        ],
                    ),
                ],
            ),
            PlanPhase(
                name="Benchmark",
                description="Verify improvements",
                steps=[
                    PlanStep(
                        id="bench-1",
                        description="Run benchmarks and compare",
                        priority=StepPriority.HIGH,
                        dependencies=["opt-1"],
                        complexity=StepComplexity.SIMPLE,
                        expected_output="Benchmark results",
                        acceptance_criteria=[
                            "Meets performance targets",
                            "No regressions in other metrics",
                        ],
                    ),
                ],
            ),
        ]

    def _build_general_phases(
        self, _goal: str, _scope: str, _context: dict[str, Any]
    ) -> list[PlanPhase]:
        """Build phases for general tasks."""
        return [
            PlanPhase(
                name="Understand",
                description="Clarify requirements and approach",
                steps=[
                    PlanStep(
                        id="gen-1",
                        description="Analyze the goal and define approach",
                        priority=StepPriority.HIGH,
                        complexity=StepComplexity.MODERATE,
                        expected_output="Approach document",
                        acceptance_criteria=[
                            "Goal is well understood",
                            "Approach is defined",
                        ],
                    ),
                ],
            ),
            PlanPhase(
                name="Execute",
                description="Carry out the plan",
                steps=[
                    PlanStep(
                        id="gen-2",
                        description="Implement the approach",
                        priority=StepPriority.CRITICAL,
                        dependencies=["gen-1"],
                        complexity=StepComplexity.MODERATE,
                        expected_output="Result",
                        acceptance_criteria=[
                            "Goal is achieved",
                            "Quality standards met",
                        ],
                    ),
                ],
            ),
        ]

    # ── Global Criteria ────────────────────────────────────────────

    def _extract_global_criteria(self, goal: str, _analysis: dict[str, Any]) -> list[str]:
        """Extract high-level acceptance criteria from the goal."""
        criteria: list[str] = []

        lower = goal.lower()

        if any(w in lower for w in ("test", "verify", "validate")):
            criteria.append("All tests pass")
        if any(w in lower for w in ("lint", "format", "clean")):
            criteria.append("No lint or format errors")
        if any(w in lower for w in ("type", "mypy", "pyright")):
            criteria.append("No type errors")
        if any(w in lower for w in ("performance", "fast", "optimize")):
            criteria.append("Performance targets met")
        if any(w in lower for w in ("secure", "security")):
            criteria.append("No security vulnerabilities")

        if not criteria:
            criteria.append("Goal is achieved as specified")

        return criteria

    # ── Validation ─────────────────────────────────────────────────

    def _validate_plan(self, plan: PlanResult) -> None:
        """Validate the plan for internal consistency."""
        issues: list[str] = []

        all_step_ids: set[str] = set()
        for phase in plan.phases:
            for step in phase.steps:
                if step.id in all_step_ids:
                    issues.append(f"Duplicate step ID: {step.id}")
                all_step_ids.add(step.id)

        for phase in plan.phases:
            for step in phase.steps:
                for dep_id in step.dependencies:
                    if dep_id not in all_step_ids:
                        issues.append(f"Step '{step.id}' depends on unknown step '{dep_id}'")

        cycle = self._detect_cycle(plan)
        if cycle:
            raise PlanCyclicDependencyError(cycle)

        if issues:
            raise PlanValidationError(
                f"Plan has {len(issues)} validation issue(s)",
                issues=issues,
            )

    def _detect_cycle(self, plan: PlanResult) -> list[str] | None:
        """Detect cyclic dependencies using DFS. Returns cycle path or None."""
        graph: dict[str, list[str]] = {}
        for phase in plan.phases:
            for step in phase.steps:
                graph[step.id] = list(step.dependencies)

        white, gray, black = 0, 1, 2
        color: dict[str, int] = dict.fromkeys(graph, white)
        parent: dict[str, str | None] = dict.fromkeys(graph)

        def dfs(node: str) -> list[str] | None:
            color[node] = gray
            for neighbor in graph.get(node, []):
                if neighbor not in color:
                    continue
                if color[neighbor] == gray:
                    cycle = [neighbor, node]
                    cur = node
                    while parent[cur] is not None and parent[cur] != neighbor:
                        cur = parent[cur]  # type: ignore[assignment]
                        cycle.append(cur)
                    cycle.reverse()
                    return cycle
                if color[neighbor] == white:
                    parent[neighbor] = node
                    result = dfs(neighbor)
                    if result:
                        return result
            color[node] = black
            return None

        for node in graph:
            if color[node] == white:
                result = dfs(node)
                if result:
                    return result
        return None
