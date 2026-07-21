"""Architecture reviewer — checks for SOLID principles, separation of concerns."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.review.base_reviewer import (
    BaseReviewer,
    IssueSeverity,
    ReviewIssue,
)


class ArchitectureReviewer(BaseReviewer):
    """Reviews code for architectural concerns."""

    @property
    def name(self) -> str:
        return "architecture"

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

            # Check for god classes (too many methods)
            class_methods = 0
            for line in lines:
                if re.match(r"\s+def\s+\w+", line):
                    class_methods += 1
            if class_methods > 20:
                issues.append(
                    ReviewIssue(
                        message=f"Class has {class_methods} methods — consider splitting",
                        severity=IssueSeverity.HIGH,
                        file=path,
                        category="separation_of_concerns",
                        recommendation="Break into smaller classes with single responsibility",
                        rule="god_class",
                    )
                )

            # Check for circular imports (basic: file importing itself)
            if path.endswith(".py"):
                module = path.replace("/", ".").replace("\\", ".").removesuffix(".py")
                for line in lines:
                    m = re.match(r"from\s+([\w.]+)\s+import", line)
                    if m and module.startswith(m.group(1)):
                        issues.append(
                            ReviewIssue(
                                message="Possible circular import detected",
                                severity=IssueSeverity.HIGH,
                                file=path,
                                category="dependency",
                                recommendation="Use lazy imports or restructure modules",
                                rule="circular_import",
                            )
                        )

            # Check for hard-coded dependencies (no DI)
            hard_coded = re.findall(
                r"from\s+([\w.]+)\s+import\s+\w+.*\n(?:.*\n)*?\s+\w+\s*=\s*\w+\(",
                content,
            )
            if hard_coded and "adapter" not in path.lower():
                issues.append(
                    ReviewIssue(
                        message="Hard-coded dependency instantiation detected",
                        severity=IssueSeverity.MEDIUM,
                        file=path,
                        category="dependency_injection",
                        recommendation="Use dependency injection for testability",
                        rule="hard_coded_dep",
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
        if any(i.rule == "god_class" for i in issues):
            recs.append("Apply Single Responsibility Principle — split large classes")
        if any(i.rule == "circular_import" for i in issues):
            recs.append("Restructure module dependencies to avoid circular imports")
        if any(i.rule == "hard_coded_dep" for i in issues):
            recs.append("Introduce dependency injection for better testability")
        return recs
