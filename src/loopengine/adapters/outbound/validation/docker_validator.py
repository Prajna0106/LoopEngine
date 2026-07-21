"""Docker validation adapter — runs docker build and/or hadolint."""

from __future__ import annotations

import re
from typing import Any

from loopengine.adapters.outbound.validation.base_validator import BaseValidator
from loopengine.core.ports.outbound.validator_port import Severity, ValidationIssue


class DockerValidator(BaseValidator):
    """Validates Dockerfiles using docker build or hadolint."""

    @property
    def name(self) -> str:
        return "docker"

    @property
    def command(self) -> list[str]:
        return ["docker"]

    def build_args(
        self,
        paths: list[str],
        *,
        config: dict[str, Any] | None = None,
    ) -> list[str]:
        mode = "build" if not config else config.get("mode", "build")

        if mode == "hadolint":
            return ["hadolint", *paths]

        # docker build mode
        dockerfile = paths[0] if paths else "Dockerfile"
        args = ["docker", "build", "--no-cache", "-f", dockerfile, "."]
        if config and config.get("build_args"):
            for k, v in config["build_args"].items():
                args.extend(["--build-arg", f"{k}={v}"])
        return args

    def parse_output(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
    ) -> tuple[bool, list[ValidationIssue]]:
        issues: list[ValidationIssue] = []
        combined = stdout + "\n" + stderr

        # Hadolint warnings: "Dockerfile:line DL3006 warning: message"
        for m in re.finditer(
            r"(.+?):(\d+)\s+(DL\d+)\s+(warning|error|info):\s*(.+)$",
            combined,
            re.MULTILINE,
        ):
            sev = Severity.ERROR if m.group(4) == "error" else Severity.WARNING
            issues.append(
                ValidationIssue(
                    message=m.group(5),
                    file=m.group(1),
                    line=int(m.group(2)),
                    severity=sev,
                    rule=m.group(3),
                )
            )

        # Hadolint failure: "DL3001 DL3001 ..."
        for m in re.finditer(r"(DL\d+)\s+(.+)$", combined, re.MULTILINE):
            if not any(i.rule == m.group(1) for i in issues):
                issues.append(
                    ValidationIssue(
                        message=m.group(2),
                        severity=Severity.WARNING,
                        rule=m.group(1),
                    )
                )

        # Docker build errors
        for m in re.finditer(r"error:\s+(.+)$", combined, re.MULTILINE):
            issues.append(
                ValidationIssue(
                    message=m.group(1),
                    severity=Severity.ERROR,
                    rule="docker_build_error",
                )
            )

        # Dockerfile syntax errors
        for m in re.finditer(
            r"^(\w+):\s+instruction missing or unknown",
            combined,
            re.MULTILINE,
        ):
            issues.append(
                ValidationIssue(
                    message=f"Instruction '{m.group(1)}' missing or unknown",
                    severity=Severity.ERROR,
                    rule="syntax_error",
                )
            )

        passed = returncode == 0
        return passed, issues
