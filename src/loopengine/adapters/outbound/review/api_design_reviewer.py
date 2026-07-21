"""API Design reviewer — checks for API design quality."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.review.base_reviewer import (
    BaseReviewer,
    IssueSeverity,
    ReviewIssue,
)


class APIDesignReviewer(BaseReviewer):
    """Reviews code for API design quality."""

    @property
    def name(self) -> str:
        return "api_design"

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

            # Check for inconsistent naming
            snake_case_funcs = re.findall(r"def\s+([a-z_][a-z0-9_]*)\(", content)
            camel_case_funcs = re.findall(r"def\s+([a-z][a-zA-Z0-9]*)\(", content)
            if snake_case_funcs and camel_case_funcs:
                issues.append(
                    ReviewIssue(
                        message="Mixed naming conventions (snake_case and camelCase)",
                        severity=IssueSeverity.MEDIUM,
                        file=path,
                        category="naming",
                        recommendation="Use snake_case for Python functions (PEP 8)",
                        rule="mixed_naming",
                    )
                )

            # Check for mutable default arguments
            for i, line in enumerate(lines, 1):
                m = re.search(r"def\s+\w+\(.*=\s*(\[\]|\{\})\)", line)
                if m:
                    issues.append(
                        ReviewIssue(
                            message=f"Mutable default argument: {m.group(1)}",
                            severity=IssueSeverity.HIGH,
                            file=path,
                            line=i,
                            category="safety",
                            recommendation=(
                                "Use None as default and create mutable inside function"
                            ),
                            rule="mutable_default",
                        )
                    )

            # Check for bare except
            for i, line in enumerate(lines, 1):
                if re.search(r"except\s*:", line):
                    issues.append(
                        ReviewIssue(
                            message="Bare except clause catches all exceptions",
                            severity=IssueSeverity.HIGH,
                            file=path,
                            line=i,
                            category="error_handling",
                            recommendation="Catch specific exceptions (e.g., except ValueError:)",
                            rule="bare_except",
                        )
                    )

            # Check for return type annotations
            for i, line in enumerate(lines, 1):
                m = re.match(r"\s*(?:async\s+)?def\s+(\w+)\(", line)
                if m and not m.group(1).startswith("_"):
                    func_line = line
                    # Find closing paren
                    paren_depth = 0
                    for ch in line[line.index("(") :]:
                        if ch == "(":
                            paren_depth += 1
                        elif ch == ")":
                            paren_depth -= 1
                            break
                    if "->" not in func_line and paren_depth == 0:
                        issues.append(
                            ReviewIssue(
                                message=f"Function '{m.group(1)}' missing return type annotation",
                                severity=IssueSeverity.LOW,
                                file=path,
                                line=i,
                                category="typing",
                                recommendation="Add return type annotation for clarity",
                                rule="missing_return_type",
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
        if any(i.rule == "mixed_naming" for i in issues):
            recs.append("Standardize on snake_case for Python code (PEP 8)")
        if any(i.rule == "mutable_default" for i in issues):
            recs.append("Use None as default; create mutable objects inside the function")
        if any(i.rule == "bare_except" for i in issues):
            recs.append("Catch specific exceptions to avoid masking errors")
        if any(i.rule == "missing_return_type" for i in issues):
            recs.append("Add type annotations to improve code clarity and tooling support")
        return recs
