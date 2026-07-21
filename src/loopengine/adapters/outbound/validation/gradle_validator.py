"""Gradle validation adapter — runs gradle check / build."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.validation.base_validator import BaseValidator
from loopengine.core.ports.outbound.validator_port import Severity, ValidationIssue


class GradleValidator(BaseValidator):
    """Validates Java/Kotlin projects using Gradle."""

    @property
    def name(self) -> str:
        return "gradle"

    @property
    def command(self) -> list[str]:
        return ["gradle"]

    def build_args(
        self,
        _paths: list[str],
        *,
        config: dict[str, Any] | None = None,
    ) -> list[str]:
        task = "check"
        if config and config.get("task"):
            task = config["task"]
        args = ["gradle", task, "--no-daemon", "--console=plain"]
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
        combined = stdout + "\n" + stderr

        # Parse compilation errors: "> Task :compileJava FAILED" style
        for m in re.finditer(
            r"> Task\s+:(\S+)\s+FAILED",
            combined,
            re.MULTILINE,
        ):
            issues.append(
                ValidationIssue(
                    message=f"Task '{m.group(1)}' failed",
                    severity=Severity.ERROR,
                    rule="task_failure",
                )
            )

        # Parse Java compilation errors
        for m in re.finditer(
            r"(\S+\.java):(\d+):\s*error:\s*(.+)$",
            combined,
            re.MULTILINE,
        ):
            issues.append(
                ValidationIssue(
                    message=m.group(3),
                    file=m.group(1),
                    line=int(m.group(2)),
                    severity=Severity.ERROR,
                    rule="compilation_error",
                )
            )

        # Parse Kotlin compilation errors
        for m in re.finditer(
            r"e:\s+(\S+\.kt):(\d+):\d+\s+(.+)$",
            combined,
            re.MULTILINE,
        ):
            issues.append(
                ValidationIssue(
                    message=m.group(3),
                    file=m.group(1),
                    line=int(m.group(2)),
                    severity=Severity.ERROR,
                    rule="compilation_error",
                )
            )

        # Parse test failures
        for _m in re.finditer(
            r"> Task\s+:test\s+FAILED",
            combined,
            re.MULTILINE,
        ):
            issues.append(
                ValidationIssue(
                    message="Tests failed",
                    severity=Severity.ERROR,
                    rule="test_failure",
                )
            )

        # Generic BUILD FAILED
        if not issues and "BUILD FAILED" in combined:
            for m in re.finditer(r"FAILURE:\s+(.+?)$", combined, re.MULTILINE):
                issues.append(
                    ValidationIssue(
                        message=m.group(1),
                        severity=Severity.ERROR,
                        rule="build_failure",
                    )
                )

        passed = returncode == 0 and "BUILD FAILED" not in combined
        return passed, issues
