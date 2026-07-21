"""Performance reviewer — checks for common performance issues."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.review.base_reviewer import (
    BaseReviewer,
    IssueSeverity,
    ReviewIssue,
)


class PerformanceReviewer(BaseReviewer):
    """Reviews code for performance concerns."""

    @property
    def name(self) -> str:
        return "performance"

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
                # N+1 query pattern
                if re.search(r"for\s+\w+\s+in\s+.*\.all\(\)", line):
                    issues.append(
                        ReviewIssue(
                            message="Possible N+1 query pattern",
                            severity=IssueSeverity.HIGH,
                            file=path,
                            line=i,
                            category="database",
                            recommendation="Use eager loading or batch queries",
                            rule="n_plus_one",
                        )
                    )

                # String concatenation in loops
                if re.search(r"for\s+.+:\s*$", line):
                    for j in range(i, min(i + 5, len(lines) + 1)):
                        next_line = lines[j - 1] if j <= len(lines) else ""
                        if re.search(r"\+=.*['\"]", next_line):
                            issues.append(
                                ReviewIssue(
                                    message="String concatenation in loop — use join()",
                                    severity=IssueSeverity.MEDIUM,
                                    file=path,
                                    line=j,
                                    category="computation",
                                    recommendation="Collect into list, then ''.join()",
                                    rule="string_concat_loop",
                                )
                            )
                            break

                # Unbounded growth
                if re.search(r"\.append\(.*\)\s*$", line):
                    # Check if inside a while True or similar
                    for j in range(max(0, i - 10), i):
                        if "while True" in lines[j]:
                            issues.append(
                                ReviewIssue(
                                    message="Unbounded list growth in infinite loop",
                                    severity=IssueSeverity.HIGH,
                                    file=path,
                                    line=i,
                                    category="memory",
                                    recommendation="Add bounds or use a bounded buffer",
                                    rule="unbounded_growth",
                                )
                            )
                            break

                # Synchronous I/O in async context
                if re.search(r"async\s+def\s+", line):
                    for j in range(i, min(i + 20, len(lines) + 1)):
                        next_line = lines[j - 1] if j <= len(lines) else ""
                        if re.search(r"time\.sleep\(", next_line):
                            issues.append(
                                ReviewIssue(
                                    message="Blocking time.sleep() in async function",
                                    severity=IssueSeverity.HIGH,
                                    file=path,
                                    line=j,
                                    category="async",
                                    recommendation="Use asyncio.sleep() instead",
                                    rule="blocking_sleep",
                                )
                            )
                            break

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
        if "database" in categories:
            recs.append("Optimize database queries with eager loading or batching")
        if "memory" in categories:
            recs.append("Monitor memory usage and add bounds to growing collections")
        if "async" in categories:
            recs.append("Use async-compatible alternatives to blocking calls")
        return recs
