"""NPM validation adapter — runs npm test and npm run lint."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound._subprocess_utils import combine_output
from loopengine.adapters.outbound.validation.base_validator import BaseValidator
from loopengine.core.ports.outbound.validator_port import Severity, ValidationIssue


class NPMValidator(BaseValidator):
    """Validates Node.js projects using npm."""

    @property
    def name(self) -> str:
        return "npm"

    @property
    def command(self) -> list[str]:
        return ["npm"]

    def build_args(
        self,
        _paths: list[str],
        *,
        config: dict[str, Any] | None = None,
    ) -> list[str]:
        script = "test"
        if config and config.get("script"):
            script = config["script"]
        args = ["npm", "run", script, "--"]
        if config and config.get("extra_args"):
            args.extend(config["extra_args"])
        return args

    def parse_output(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
    ) -> tuple[bool, list[ValidationIssue]]:
        issues: list[ValidationIssue] = []
        combined = combine_output(stdout, stderr)

        # Parse ESLint errors: "error  ...  rule-name"
        for m in re.finditer(
            r"(\d+)\s+error(?:s)?\s+and\s+(\d+)\s+warning",
            combined,
        ):
            err_count = int(m.group(1))
            warn_count = int(m.group(2))
            if err_count > 0:
                issues.append(
                    ValidationIssue(
                        message=f"{err_count} error(s), {warn_count} warning(s)",
                        severity=Severity.ERROR,
                        rule="lint_errors",
                    )
                )
            elif warn_count > 0:
                issues.append(
                    ValidationIssue(
                        message=f"{warn_count} warning(s)",
                        severity=Severity.WARNING,
                        rule="lint_warnings",
                    )
                )

        # Parse individual ESLint results: "  line  col  severity  message  rule-name"
        for m in re.finditer(
            r"^\s+(\d+):(\d+)\s+(error|warning)\s+(.+?)\s+(\S+)\s*$",
            combined,
            re.MULTILINE,
        ):
            sev = Severity.ERROR if m.group(3) == "error" else Severity.WARNING
            issues.append(
                ValidationIssue(
                    message=m.group(4),
                    line=int(m.group(1)),
                    column=int(m.group(2)),
                    severity=sev,
                    rule=m.group(5),
                )
            )

        # Parse TypeScript errors
        for m in re.finditer(
            r"TS(\d+):\s+(.+?)$",
            combined,
            re.MULTILINE,
        ):
            issues.append(
                ValidationIssue(
                    message=m.group(2),
                    severity=Severity.ERROR,
                    rule=f"TS{m.group(1)}",
                )
            )

        # Parse Jest/Vitest test failures
        for m in re.finditer(
            r"FAIL\s+(\S+)",
            combined,
            re.MULTILINE,
        ):
            issues.append(
                ValidationIssue(
                    message=f"Tests failed in {m.group(1)}",
                    file=m.group(1),
                    severity=Severity.ERROR,
                    rule="test_failure",
                )
            )

        passed = returncode == 0
        return passed, issues
