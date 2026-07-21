"""Complexity reviewer — checks for code complexity and maintainability."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.review.base_reviewer import (
    BaseReviewer,
    IssueSeverity,
    ReviewIssue,
)


class ComplexityReviewer(BaseReviewer):
    """Reviews code for complexity concerns."""

    @property
    def name(self) -> str:
        return "complexity"

    def _analyze(
        self,
        *,
        goal: str,  # noqa: ARG002
        artifacts: list[dict[str, Any]],
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        files = self._get_files(artifacts)

        for path, content in files.items():
            if not path.endswith(".py"):
                continue

            lines = content.splitlines()
            func_name = ""
            func_start = 0
            nesting = 0

            for i, line in enumerate(lines, 1):
                # Track function boundaries
                m = re.match(r"\s*(?:async\s+)?def\s+(\w+)\(", line)
                if m:
                    if func_name and (i - func_start) > 50:
                        issues.append(
                            ReviewIssue(
                                message=f"Function '{func_name}' is {i - func_start} lines long",
                                severity=IssueSeverity.MEDIUM,
                                file=path,
                                line=func_start,
                                category="length",
                                recommendation="Break into smaller functions (max ~30 lines)",
                                rule="long_function",
                            )
                        )
                    func_name = m.group(1)
                    func_start = i
                    nesting = 0

                # Track nesting depth
                stripped = line.lstrip()
                indent = len(line) - len(stripped)
                current_nesting = indent // 4
                if current_nesting > nesting:
                    nesting = current_nesting

                # Check for deep nesting
                if nesting > 4:
                    issues.append(
                        ReviewIssue(
                            message=f"Deep nesting ({nesting} levels) in '{func_name}'",
                            severity=IssueSeverity.MEDIUM,
                            file=path,
                            line=i,
                            category="nesting",
                            recommendation="Extract inner logic into helper functions",
                            rule="deep_nesting",
                        )
                    )
                    nesting = 0  # Reset to avoid duplicate reports

                # Check for too many parameters
                if m:
                    param_match = re.search(r"\(([^)]*)\)", line)
                    if param_match:
                        params = [
                            p.strip()
                            for p in param_match.group(1).split(",")
                            if p.strip() and p.strip() != "self" and p.strip() != "cls"
                        ]
                        if len(params) > 5:
                            issues.append(
                                ReviewIssue(
                                    message=f"Function '{func_name}' has {len(params)} parameters",
                                    severity=IssueSeverity.MEDIUM,
                                    file=path,
                                    line=i,
                                    category="parameters",
                                    recommendation="Use a dataclass or dict for many parameters",
                                    rule="too_many_params",
                                )
                            )

            # Check last function
            if func_name and (len(lines) - func_start) > 50:
                issues.append(
                    ReviewIssue(
                        message=f"Function '{func_name}' is {len(lines) - func_start} lines long",
                        severity=IssueSeverity.MEDIUM,
                        file=path,
                        line=func_start,
                        category="length",
                        recommendation="Break into smaller functions",
                        rule="long_function",
                    )
                )

        return issues

    def _recommendations(
        self,
        *,
        goal: str,  # noqa: ARG002
        artifacts: list[dict[str, Any]],  # noqa: ARG002
        issues: list[ReviewIssue],
    ) -> list[str]:
        recs: list[str] = []
        if any(i.rule == "long_function" for i in issues):
            recs.append("Keep functions under 30 lines for readability")
        if any(i.rule == "deep_nesting" for i in issues):
            recs.append("Reduce nesting by extracting helper functions or using early returns")
        if any(i.rule == "too_many_params" for i in issues):
            recs.append("Group related parameters into a dataclass or config object")
        return recs
