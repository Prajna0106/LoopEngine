"""Testing reviewer — checks for test coverage and quality."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.review.base_reviewer import (
    BaseReviewer,
    IssueSeverity,
    ReviewIssue,
)


class TestingReviewer(BaseReviewer):
    """Reviews code for testing quality."""

    @property
    def name(self) -> str:
        return "testing"

    def _analyze(
        self,
        *,
        goal: str,  # noqa: ARG002
        artifacts: list[dict[str, Any]],
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[ReviewIssue]:
        issues: list[ReviewIssue] = []
        files = self._get_files(artifacts)

        test_files = {p: c for p, c in files.items() if "test" in p}
        src_files = {p: c for p, c in files.items() if "test" not in p and p.endswith(".py")}

        # Check if tests exist
        if not test_files:
            issues.append(
                ReviewIssue(
                    message="No test files found",
                    severity=IssueSeverity.HIGH,
                    category="coverage",
                    recommendation="Add unit tests for all modules",
                    rule="no_tests",
                )
            )
            return issues

        # Check test-to-source ratio
        src_count = len(src_files)
        test_count = len(test_files)
        if src_count > 0 and test_count / src_count < 0.5:
            issues.append(
                ReviewIssue(
                    message=(
                        f"Low test file ratio: {test_count} tests for {src_count} source files"
                    ),
                    severity=IssueSeverity.MEDIUM,
                    category="coverage",
                    recommendation="Aim for at least 1 test file per source file",
                    rule="low_test_ratio",
                )
            )

        # Check for assertions in tests
        for path, content in test_files.items():
            test_funcs = re.findall(r"def\s+(test_\w+)\(", content)
            assert_count = len(re.findall(r"\bassert\b", content))
            if test_funcs and assert_count == 0:
                issues.append(
                    ReviewIssue(
                        message=f"Test file has {len(test_funcs)} tests but no assertions",
                        severity=IssueSeverity.HIGH,
                        file=path,
                        category="quality",
                        recommendation="Every test should have at least one assertion",
                        rule="no_assertions",
                    )
                )

            # Check for test isolation (no global state)
            if re.search(r"^[A-Z_]+\s*=", content, re.MULTILINE):
                issues.append(
                    ReviewIssue(
                        message="Global state in test file may cause test pollution",
                        severity=IssueSeverity.MEDIUM,
                        file=path,
                        category="isolation",
                        recommendation="Use fixtures or setUp/tearDown for test state",
                        rule="global_test_state",
                    )
                )

            # Check for hardcoded values
            for i, line in enumerate(content.splitlines(), 1):
                if re.search(r"assert.*==\s*\d{4,}", line):
                    issues.append(
                        ReviewIssue(
                            message="Hardcoded expected value in assertion",
                            severity=IssueSeverity.LOW,
                            file=path,
                            line=i,
                            category="maintainability",
                            recommendation="Use named constants or descriptive expected values",
                            rule="hardcoded_assert",
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
        if any(i.rule == "no_tests" for i in issues):
            recs.append("Write unit tests for all business logic")
        if any(i.rule == "low_test_ratio" for i in issues):
            recs.append("Increase test coverage to match source file count")
        if any(i.rule == "no_assertions" for i in issues):
            recs.append("Ensure every test function contains assertions")
        return recs
