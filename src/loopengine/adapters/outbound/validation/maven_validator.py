"""Maven validation adapter — runs mvn validate / compile / test."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound._subprocess_utils import combine_output
from loopengine.adapters.outbound.validation.base_validator import BaseValidator
from loopengine.core.ports.outbound.validator_port import Severity, ValidationIssue


class MavenValidator(BaseValidator):
    """Validates Java projects using Maven."""

    @property
    def name(self) -> str:
        return "maven"

    @property
    def command(self) -> list[str]:
        return ["mvn"]

    def build_args(
        self,
        _paths: list[str],
        *,
        config: dict[str, Any] | None = None,
    ) -> list[str]:
        goal = "validate"
        if config and config.get("goal"):
            goal = config["goal"]
        args = ["mvn", goal, "--batch-mode", "--fail-at-end"]
        if config:
            if config.get("profiles"):
                args.extend(["-P", ",".join(config["profiles"])])
            if config.get("properties"):
                for k, v in config["properties"].items():
                    args.extend([f"-D{k}={v}"])
        return args

    def parse_output(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
    ) -> tuple[bool, list[ValidationIssue]]:
        issues: list[ValidationIssue] = []
        combined = combine_output(stdout, stderr)

        # Parse compilation errors: "[ERROR] /path/File.java:[line,col]"
        for m in re.finditer(
            r"\[ERROR\]\s+(\S+\.java):\[(\d+),(\d+)\]\s*(.+)$",
            combined,
            re.MULTILINE,
        ):
            issues.append(
                ValidationIssue(
                    message=m.group(4),
                    file=m.group(1),
                    line=int(m.group(2)),
                    column=int(m.group(3)),
                    severity=Severity.ERROR,
                    rule="compilation_error",
                )
            )

        # Parse test failures
        for m in re.finditer(
            r"\[ERROR\]\s+Tests?\s+run:\s+\d+,\s+Failures:\s+(\d+),"
            r"\s+Errors:\s+(\d+).*?\[ERROR\]\s+(.+?)\s+Time elapsed",
            combined,
            re.MULTILINE,
        ):
            failures = int(m.group(1))
            errors = int(m.group(2))
            if failures > 0 or errors > 0:
                issues.append(
                    ValidationIssue(
                        message=f"{m.group(3)} — {failures} failures, {errors} errors",
                        severity=Severity.ERROR,
                        rule="test_failure",
                    )
                )

        # Parse BUILD FAILURE / SUCCESS
        build_failed = "[ERROR] BUILD FAILURE" in combined

        # Generic error lines
        if not issues:
            for m in re.finditer(r"\[ERROR\]\s+(.+)$", combined, re.MULTILINE):
                msg = m.group(1)
                if "BUILD" in msg:
                    continue
                issues.append(
                    ValidationIssue(
                        message=msg,
                        severity=Severity.ERROR,
                        rule="maven_error",
                    )
                )

        passed = returncode == 0 and not build_failed
        return passed, issues
