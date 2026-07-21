"""Database reviewer — checks for database design and usage concerns."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.review.base_reviewer import (
    BaseReviewer,
    IssueSeverity,
    ReviewIssue,
)


class DatabaseReviewer(BaseReviewer):
    """Reviews code for database concerns."""

    @property
    def name(self) -> str:
        return "database"

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
                # Raw SQL without parameterization
                if re.search(
                    r"execute\s*\(\s*f?['\"].*\{",
                    line,
                ):
                    issues.append(
                        ReviewIssue(
                            message="SQL string interpolation — possible injection",
                            severity=IssueSeverity.CRITICAL,
                            file=path,
                            line=i,
                            category="injection",
                            recommendation="Use parameterized queries with ? or %s placeholders",
                            rule="sql_interpolation",
                        )
                    )

                # Missing index hints
                if re.search(r"\.filter\(|\.where\(|WHERE\s+", line, re.IGNORECASE) and any(
                    keyword in content.lower()
                    for keyword in ["migration", "model", "schema", "table"]
                ):
                    issues.append(
                        ReviewIssue(
                            message="Filter/where clause — ensure proper indexing",
                            severity=IssueSeverity.LOW,
                            file=path,
                            line=i,
                            category="performance",
                            recommendation=("Add database indexes for frequently queried columns"),
                            rule="missing_index_hint",
                        )
                    )

                # Transaction handling
                if re.search(r"\.save\(\)|\.create\(", line):
                    # Check if there's a transaction context
                    has_transaction = any(
                        keyword in content
                        for keyword in [
                            "transaction",
                            "@transaction",
                            "atomic",
                            "begin",
                        ]
                    )
                    if not has_transaction:
                        issues.append(
                            ReviewIssue(
                                message="Database write without explicit transaction",
                                severity=IssueSeverity.MEDIUM,
                                file=path,
                                line=i,
                                category="integrity",
                                recommendation="Wrap writes in a transaction for atomicity",
                                rule="no_transaction",
                            )
                        )

                # Select all columns
                if re.search(r"SELECT\s+\*\s+FROM", line, re.IGNORECASE):
                    issues.append(
                        ReviewIssue(
                            message="SELECT * — fetches all columns",
                            severity=IssueSeverity.LOW,
                            file=path,
                            line=i,
                            category="performance",
                            recommendation="Select only needed columns to reduce data transfer",
                            rule="select_star",
                        )
                    )

                # N+1 query pattern
                if re.search(r"for\s+\w+\s+in\s+.*\.all\(\)", line):
                    issues.append(
                        ReviewIssue(
                            message="N+1 query pattern in loop",
                            severity=IssueSeverity.HIGH,
                            file=path,
                            line=i,
                            category="performance",
                            recommendation="Use select_related/prefetch_related or JOIN",
                            rule="n_plus_one",
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
        if "injection" in categories:
            recs.append("Always use parameterized queries to prevent SQL injection")
        if "performance" in categories:
            recs.append("Add indexes and avoid SELECT * for better query performance")
        if "integrity" in categories:
            recs.append("Use transactions to ensure data consistency on writes")
        return recs
