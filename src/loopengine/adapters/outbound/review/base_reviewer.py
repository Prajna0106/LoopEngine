"""Base reviewer — common infrastructure for rule-based reviewers.

Provides artifact analysis, issue collection, score calculation, and
structured logging.  Concrete reviewers override ``_analyze`` to apply
domain-specific checks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import structlog

from loopengine.core.ports.outbound.reviewer_port import (
    ReviewComment,
    Reviewer,
    ReviewResult,
    ReviewVerdict,
)

log = structlog.get_logger()


# ── Models ─────────────────────────────────────────────────────────────


class IssueSeverity:
    """Severity levels for review issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass(frozen=True)
class ReviewIssue:
    """A specific issue found during review."""

    message: str
    severity: str = IssueSeverity.MEDIUM
    file: str = ""
    line: int = 0
    category: str = ""
    recommendation: str = ""
    rule: str = ""


@dataclass(frozen=True)
class ReviewReport:
    """Aggregated report from one or more reviewers."""

    reviewer: str
    score: float = 0.0
    issues: list[ReviewIssue] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.LOW)


# ── Base reviewer ──────────────────────────────────────────────────────


class BaseReviewer(Reviewer):
    """Abstract reviewer that applies rule-based checks to artifacts.

    Subclasses override:
    * ``_analyze`` — apply domain-specific checks and return issues.
    * ``_recommendations`` — generate high-level recommendations.
    """

    def __init__(self, *, weight: float = 1.0) -> None:
        self._weight = weight

    def review(
        self,
        *,
        goal: str,
        artifacts: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> ReviewResult:
        report = self._build_report(goal=goal, artifacts=artifacts, context=context)

        comments = [
            ReviewComment(
                file=i.file,
                line=i.line,
                message=f"[{i.severity.upper()}] {i.message}",
                severity=i.severity,
            )
            for i in report.issues
        ]

        verdict = self._score_to_verdict(report.score)

        return ReviewResult(
            verdict=verdict,
            comments=comments,
            summary=report.summary,
            score=report.score,
            metadata={
                "reviewer": self.name,
                "issues": [
                    {
                        "message": i.message,
                        "severity": i.severity,
                        "file": i.file,
                        "line": i.line,
                        "category": i.category,
                        "recommendation": i.recommendation,
                        "rule": i.rule,
                    }
                    for i in report.issues
                ],
                "recommendations": report.recommendations,
            },
        )

    def _build_report(
        self,
        *,
        goal: str,
        artifacts: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> ReviewReport:
        issues = self._analyze(goal=goal, artifacts=artifacts, context=context)
        recommendations = self._recommendations(goal=goal, artifacts=artifacts, issues=issues)
        score = self._calculate_score(issues)
        summary = self._generate_summary(score, issues)

        return ReviewReport(
            reviewer=self.name,
            score=score,
            issues=issues,
            recommendations=recommendations,
            summary=summary,
        )

    def _analyze(
        self,
        *,
        goal: str,  # noqa: ARG002
        artifacts: list[dict[str, Any]],  # noqa: ARG002
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[ReviewIssue]:
        return []

    def _recommendations(
        self,
        *,
        goal: str,  # noqa: ARG002
        artifacts: list[dict[str, Any]],  # noqa: ARG002
        issues: list[ReviewIssue],  # noqa: ARG002
    ) -> list[str]:
        return []

    def _calculate_score(self, issues: list[ReviewIssue]) -> float:
        penalty = 0.0
        for issue in issues:
            if issue.severity == IssueSeverity.CRITICAL:
                penalty += 3.0
            elif issue.severity == IssueSeverity.HIGH:
                penalty += 2.0
            elif issue.severity == IssueSeverity.MEDIUM:
                penalty += 1.0
            elif issue.severity == IssueSeverity.LOW:
                penalty += 0.5
        raw = 10.0 - penalty
        return max(0.0, min(10.0, raw))

    def _generate_summary(self, score: float, issues: list[ReviewIssue]) -> str:
        if not issues:
            return f"No issues found. Score: {score:.1f}/10"
        counts: dict[str, int] = {}
        for i in issues:
            counts[i.severity] = counts.get(i.severity, 0) + 1
        parts = [f"{v} {k}" for k, v in sorted(counts.items())]
        return f"Score: {score:.1f}/10 — {', '.join(parts)}"

    def _score_to_verdict(self, score: float) -> ReviewVerdict:
        if score >= 8.0:
            return ReviewVerdict.APPROVED
        if score >= 5.0:
            return ReviewVerdict.CHANGES_REQUESTED
        return ReviewVerdict.REJECTED

    # ── Artifact helpers ──────────────────────────────────────────────

    @staticmethod
    def _get_content(artifacts: list[dict[str, Any]], kind: str) -> str:
        for a in artifacts:
            if a.get("kind") == kind:
                return str(a.get("content", ""))
        return ""

    @staticmethod
    def _get_files(artifacts: list[dict[str, Any]]) -> dict[str, str]:
        files: dict[str, str] = {}
        for a in artifacts:
            if a.get("kind") == "file":
                path = a.get("path", "")
                content = a.get("content", "")
                if path:
                    files[path] = content
        return files

    @staticmethod
    def _count_lines(files: dict[str, str]) -> int:
        total = 0
        for content in files.values():
            total += content.count("\n") + 1
        return total

    @staticmethod
    def _has_pattern(files: dict[str, str], pattern: str) -> list[tuple[str, int]]:
        matches: list[tuple[str, int]] = []
        regex = re.compile(pattern)
        for path, content in files.items():
            for i, line in enumerate(content.splitlines(), 1):
                if regex.search(line):
                    matches.append((path, i))
        return matches
