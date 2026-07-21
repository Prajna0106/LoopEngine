"""Outbound port — reflection engine interface.

Defines the contract for analyzing execution results and deciding
whether to converge, iterate, or escalate.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ReflectionDecision(StrEnum):
    """Possible decisions after reflection."""

    CONVERGED = "converged"
    ITERATE = "iterate"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class ReflectionResult:
    """Output of a reflection cycle."""

    decision: ReflectionDecision
    reasoning: str = ""
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ReflectionEngine(ABC):
    """Contract for reflection engines.

    Follows ISP: only reflection and decision-making. A reflection engine
    compares results against goals and decides the next action.
    """

    @abstractmethod
    def reflect(
        self,
        *,
        goal: str,
        results: list[dict[str, Any]],
        iteration: int = 0,
        max_iterations: int = 5,
    ) -> ReflectionResult:
        """Analyze results and decide next action.

        Parameters
        ----------
        goal:
            The original workflow goal.
        results:
            Collected results from executed phases/steps.
        iteration:
            Current iteration number (0-based).
        max_iterations:
            Maximum allowed iterations before forced escalation.

        Raises
        ------
        ReflectionError
            If reflection itself fails (e.g. LLM unavailable).
        """
