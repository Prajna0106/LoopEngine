"""Scalability reviewer — checks for scalability concerns."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.review.base_reviewer import (
    BaseReviewer,
    IssueSeverity,
    ReviewIssue,
)


class ScalabilityReviewer(BaseReviewer):
    """Reviews code for scalability concerns."""

    @property
    def name(self) -> str:
        return "scalability"

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
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                # Synchronous processing of large datasets
                if re.search(r"\.readlines\(\)", line):
                    issues.append(
                        ReviewIssue(
                            message="Reading entire file into memory — may not scale",
                            severity=IssueSeverity.MEDIUM,
                            file=path,
                            line=i,
                            category="memory",
                            recommendation="Use streaming/chunked reading for large files",
                            rule="full_file_read",
                        )
                    )

                # Single-threaded processing
                if re.search(r"for\s+\w+\s+in\s+.*\.items\(\)", line):
                    # Check if there's a nested loop (O(n²))
                    for j in range(i + 1, min(i + 10, len(lines) + 1)):
                        next_line = lines[j - 1] if j <= len(lines) else ""
                        if re.search(r"for\s+\w+\s+in\s+", next_line):
                            issues.append(
                                ReviewIssue(
                                    message="Nested iteration — O(n²) complexity",
                                    severity=IssueSeverity.HIGH,
                                    file=path,
                                    line=j,
                                    category="algorithmic",
                                    recommendation="Consider using sets/dicts for O(1) lookups",
                                    rule="nested_iteration",
                                )
                            )
                            break

                # No caching/memoization for repeated computations
                if re.search(r"def\s+\w+.*:", line):
                    func_name = re.search(r"def\s+(\w+)", line)
                    if func_name:
                        # Check if function is called multiple times
                        call_count = content.count(f"{func_name.group(1)}(")
                        has_cache = "@lru_cache" in content or "@cache" in content
                        if call_count > 5 and not has_cache:
                            issues.append(
                                ReviewIssue(
                                    message=(
                                        f"Function '{func_name.group(1)}' called"
                                        f" {call_count} times without caching"
                                    ),
                                    severity=IssueSeverity.LOW,
                                    file=path,
                                    line=i,
                                    category="caching",
                                    recommendation=(
                                        "Consider @lru_cache for expensive computations"
                                    ),
                                    rule="no_caching",
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
        categories = {i.category for i in issues}
        if "memory" in categories:
            recs.append("Use streaming/iterators for large data processing")
        if "algorithmic" in categories:
            recs.append("Optimize nested loops with data structures (sets, dicts)")
        if "caching" in categories:
            recs.append("Add memoization for expensive or frequently called functions")
        return recs
