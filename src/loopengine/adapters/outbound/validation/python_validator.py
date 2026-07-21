"""Python validation adapter — runs ruff check for linting and syntax."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.validation.base_validator import BaseValidator
from loopengine.core.ports.outbound.validator_port import Severity, ValidationIssue


class PythonValidator(BaseValidator):
    """Validates Python code using ruff check."""

    @property
    def name(self) -> str:
        return "python"

    @property
    def command(self) -> list[str]:
        return ["ruff", "check"]

    def build_args(
        self,
        paths: list[str],
        *,
        config: dict[str, Any] | None = None,
    ) -> list[str]:
        args = ["ruff", "check", "--output-format=json"]
        if config:
            if config.get("select"):
                args.extend(["--select", ",".join(config["select"])])
            if config.get("ignore"):
                args.extend(["--ignore", ",".join(config["ignore"])])
        args.extend(paths)
        return args

    def parse_output(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
    ) -> tuple[bool, list[ValidationIssue]]:
        import json

        if not stdout.strip():
            if returncode == 0:
                return True, []
            message = stderr.strip() or f"exit code {returncode}"
            return False, [ValidationIssue(message=message, severity=Severity.ERROR)]

        try:
            violations = json.loads(stdout)
        except json.JSONDecodeError:
            # Fall back to line-by-line parsing
            return self._parse_text_output(stdout, returncode)

        issues: list[ValidationIssue] = []
        for v in violations:
            severity = Severity.WARNING
            code = v.get("code", "")
            # F821 (undefined name) and E999 (syntax error) are errors
            if code.startswith("F8") or code == "E999":
                severity = Severity.ERROR
            issues.append(
                ValidationIssue(
                    message=v.get("message", ""),
                    file=v.get("filename", ""),
                    line=v.get("location", {}).get("row", 0),
                    column=v.get("location", {}).get("column", 0),
                    severity=severity,
                    rule=code,
                )
            )

        passed = returncode == 0 and not any(i.severity == Severity.ERROR for i in issues)
        return passed, issues

    def _parse_text_output(
        self, output: str, returncode: int
    ) -> tuple[bool, list[ValidationIssue]]:
        issues: list[ValidationIssue] = []
        pattern = re.compile(r"^(.+?):(\d+):(\d+):\s+(\w+)\s+(.+)$", re.MULTILINE)
        for m in pattern.finditer(output):
            issues.append(
                ValidationIssue(
                    message=m.group(5),
                    file=m.group(1),
                    line=int(m.group(2)),
                    column=int(m.group(3)),
                    severity=Severity.WARNING,
                    rule=m.group(4),
                )
            )
        passed = returncode == 0
        return passed, issues
