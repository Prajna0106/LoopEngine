"""Documentation reviewer — checks for documentation coverage and quality."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.review.base_reviewer import (
    BaseReviewer,
    IssueSeverity,
    ReviewIssue,
)


class DocumentationReviewer(BaseReviewer):
    """Reviews code for documentation quality."""

    @property
    def name(self) -> str:
        return "documentation"

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
            has_module_docstring = len(lines) > 0 and (
                lines[0].startswith('"""')
                or lines[0].startswith("'''")
                or (len(lines) > 1 and lines[1].startswith('"""'))
            )

            if not has_module_docstring:
                issues.append(
                    ReviewIssue(
                        message="Missing module docstring",
                        severity=IssueSeverity.LOW,
                        file=path,
                        category="docstrings",
                        recommendation="Add a module-level docstring explaining purpose",
                        rule="missing_module_doc",
                    )
                )

            # Check for functions without docstrings
            for i, line in enumerate(lines, 1):
                m = re.match(r"\s*(?:async\s+)?def\s+(\w+)\(", line)
                if m:
                    func_name = m.group(1)
                    if func_name.startswith("_") and func_name != "__init__":
                        continue
                    # Check next non-empty line for docstring
                    has_doc = False
                    for j in range(i + 1, min(i + 4, len(lines) + 1)):
                        next_line = lines[j - 1] if j <= len(lines) else ""
                        stripped = next_line.strip()
                        if stripped.startswith('"""') or stripped.startswith("'''"):
                            has_doc = True
                            break
                        if stripped and not stripped.startswith("#"):
                            break
                    if not has_doc:
                        issues.append(
                            ReviewIssue(
                                message=f"Function '{func_name}' missing docstring",
                                severity=IssueSeverity.LOW,
                                file=path,
                                line=i,
                                category="docstrings",
                                recommendation=(
                                    "Add a docstring describing parameters and return value"
                                ),
                                rule="missing_func_doc",
                            )
                        )

            # Check for TODO/FIXME without tracking
            for i, line in enumerate(lines, 1):
                m = re.search(r"#\s*(TODO|FIXME|HACK|XXX)\b", line)
                if m:
                    tag = m.group(1)
                    # Check if there's a ticket reference
                    has_ticket = re.search(r"\[\w+-\d+\]|#\d+", line)
                    if not has_ticket:
                        issues.append(
                            ReviewIssue(
                                message=f"{tag} without ticket/issue reference",
                                severity=IssueSeverity.INFO,
                                file=path,
                                line=i,
                                category="tracking",
                                recommendation="Link to a tracking issue",
                                rule="todo_no_ticket",
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
        if any(i.rule == "missing_module_doc" for i in issues):
            recs.append("Add module docstrings to explain purpose and usage")
        if any(i.rule == "missing_func_doc" for i in issues):
            recs.append("Document public functions with docstrings (args + returns)")
        if any(i.rule == "todo_no_ticket" for i in issues):
            recs.append("Track all TODOs with ticket references for accountability")
        return recs
