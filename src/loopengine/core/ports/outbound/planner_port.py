"""Outbound port — planner interface.

Defines the contract for workflow planning. A planner takes a goal and
produces a structured plan with phases, steps, and acceptance criteria.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class StepPriority(StrEnum):
    """Priority level for a plan step."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StepComplexity(StrEnum):
    """Estimated complexity for a plan step."""

    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass(frozen=True)
class PlanStep:
    """A single step inside a plan phase."""

    id: str
    description: str
    priority: StepPriority = StepPriority.MEDIUM
    dependencies: list[str] = field(default_factory=list)
    complexity: StepComplexity = StepComplexity.MODERATE
    expected_output: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PlanPhase:
    """A phase in the workflow plan."""

    name: str
    steps: list[PlanStep] = field(default_factory=list)
    description: str = ""


@dataclass(frozen=True)
class PlanResult:
    """Structured plan produced by a Planner."""

    goal: str
    phases: list[PlanPhase] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Planner(ABC):
    """Contract for workflow planners.

    Follows ISP: only planning. A planner transforms a high-level goal
    into an ordered sequence of phases and steps.
    """

    @abstractmethod
    def create_plan(
        self,
        goal: str,
        *,
        context: dict[str, Any] | None = None,
        constraints: list[str] | None = None,
    ) -> PlanResult:
        """Produce a plan for achieving *goal*.

        Parameters
        ----------
        goal:
            Natural-language description of what the workflow should achieve.
        context:
            Optional existing context (project structure, prior attempts, etc.).
        constraints:
            Optional hard constraints the plan must satisfy.

        Raises
        ------
        PlanError
            If planning fails (e.g. unresolvable constraints).
        """
