"""Outbound port — reviewer interface.

Defines the contract for high-level workflow review. A reviewer examines
the full set of artifacts and produces a verdict with actionable feedback.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ReviewVerdict(StrEnum):
    """Review outcome."""

    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ReviewComment:
    """A single review comment."""

    file: str = ""
    line: int = 0
    message: str = ""
    severity: str = "info"


@dataclass(frozen=True)
class ReviewResult:
    """Structured output of a review cycle."""

    verdict: ReviewVerdict
    comments: list[ReviewComment] = field(default_factory=list)
    summary: str = ""
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class Reviewer(ABC):
    """Contract for workflow reviewers.

    Follows ISP: only review. A reviewer examines the full output of a
    workflow and produces a verdict with structured feedback.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Reviewer identifier (e.g. 'code_review', 'security_review')."""

    @abstractmethod
    def review(
        self,
        *,
        goal: str,
        artifacts: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> ReviewResult:
        """Review workflow artifacts and return a verdict.

        Parameters
        ----------
        goal:
            The original workflow goal.
        artifacts:
            List of artifact dicts (kind, content, path, etc.).
        context:
            Optional additional context (config, prior reviews, etc.).

        Raises
        ------
        ReviewError
            If the review itself fails.
        """
