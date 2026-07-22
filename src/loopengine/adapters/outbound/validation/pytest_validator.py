"""Pytest validation adapter — runs pytest and parses results."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound._subprocess_utils import combine_output
from loopengine.adapters.outbound.validation.base_validator import BaseValidator
from loopengine.core.ports.outbound.validator_port import Severity, ValidationIssue


class PytestValidator(BaseValidator):
    """Validates Python tests using pytest."""

    @property
    def name(self) -> str:
        return "pytest"

    @property
    def command(self) -> list[str]:
        return ["pytest"]

    def build_args(
        self,
        paths: list[str],
        *,
        config: dict[str, Any] | None = None,
    ) -> list[str]:
        args = ["pytest", "--tb=short", "--no-header", "-q"]
        if config:
            if config.get("markers"):
                args.extend(["-m", config["markers"]])
            if config.get("extra_args"):
                args.extend(config["extra_args"])
        if paths:
            args.extend(paths)
        return args

    def parse_output(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
    ) -> tuple[bool, list[ValidationIssue]]:
        issues: list[ValidationIssue] = []
        combined = combine_output(stdout, stderr)

        failed_count = 0
        error_count = 0

        summary_match = re.search(
            r"(\d+)\s+passed.*?(\d+)\s+failed.*?(\d+)\s+error",
            combined,
        )
        if summary_match:
            failed_count = int(summary_match.group(2))
            error_count = int(summary_match.group(3))
        else:
            fail_match = re.search(r"(\d+)\s+failed", combined)
            err_match = re.search(r"(\d+)\s+error", combined)
            if fail_match:
                failed_count = int(fail_match.group(1))
            if err_match:
                error_count = int(err_match.group(1))

        for m in re.finditer(r"FAILED\s+(\S+?)(?:\s+-\s+(.+))?$", combined, re.MULTILINE):
            issues.append(
                ValidationIssue(
                    message=m.group(2) or "test failed",
                    file=m.group(1),
                    severity=Severity.ERROR,
                    rule="test_failure",
                )
            )

        for m in re.finditer(r"ERROR\s+(\S+?)(?:\s+-\s+(.+))?$", combined, re.MULTILINE):
            issues.append(
                ValidationIssue(
                    message=m.group(2) or "test error",
                    file=m.group(1),
                    severity=Severity.ERROR,
                    rule="test_error",
                )
            )

        for m in re.finditer(r"WARNING\s+(.+)$", combined, re.MULTILINE):
            issues.append(
                ValidationIssue(
                    message=m.group(1),
                    severity=Severity.WARNING,
                    rule="warning",
                )
            )

        passed = returncode == 0 and failed_count == 0 and error_count == 0
        return passed, issues
