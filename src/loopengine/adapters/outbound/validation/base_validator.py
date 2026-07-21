"""Base validator — common infrastructure for CLI-based validators.

Provides subprocess execution, timeout, error handling, and structured
logging.  Concrete validators override ``command``, ``build_args``, and
``parse_output`` to wrap a specific tool.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from loopengine.core.ports.outbound.validator_port import (
    Severity,
    ValidationIssue,
    ValidationResult,
    Validator,
)

log = structlog.get_logger()


# ── Configuration ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class ValidatorConfig:
    """Tuning knobs for subprocess execution."""

    timeout: float = 120.0
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)


# ── Base validator ─────────────────────────────────────────────────────


class BaseValidator(Validator):
    """Abstract adapter that validates by running a CLI tool.

    Subclasses override:
    * ``command``  — the CLI executable (e.g. ``["ruff", "check"]``).
    * ``build_args`` — turn paths + config into CLI arguments.
    * ``parse_output`` — extract issues from stdout/stderr.
    * ``is_available`` — check whether the CLI is installed.
    """

    def __init__(self, *, config: ValidatorConfig | None = None) -> None:
        self._config = config or ValidatorConfig()

    # ── Subclass hooks ────────────────────────────────────────────────

    @property
    def command(self) -> list[str]:
        raise NotImplementedError

    def build_args(
        self,
        paths: list[str],
        *,
        config: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[str]:
        return [*self.command, *paths]

    def parse_output(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
    ) -> tuple[bool, list[ValidationIssue]]:
        """Parse raw output into (passed, issues).

        The default implementation: returncode 0 = pass, non-zero = fail
        with the combined output as a single issue.
        """
        if returncode == 0:
            return True, []
        message = stderr.strip() or stdout.strip() or f"exit code {returncode}"
        return False, [ValidationIssue(message=message, severity=Severity.ERROR)]

    def is_available(self) -> bool:
        """Check whether the CLI binary exists on PATH."""
        cmd = self.command[0] if self.command else ""
        return shutil.which(cmd) is not None

    # ── Core invocation ───────────────────────────────────────────────

    def validate(
        self,
        paths: list[str],
        *,
        content: dict[str, str] | None = None,  # noqa: ARG002
        config: dict[str, Any] | None = None,
    ) -> ValidationResult:
        if not self.is_available():
            return ValidationResult(
                validator=self.name,
                passed=False,
                issues=[
                    ValidationIssue(
                        message=f"Tool '{self.name}' is not installed or not on PATH",
                        severity=Severity.ERROR,
                    )
                ],
            )

        args = self.build_args(paths, config=config)

        log.debug(
            "validator_invoke",
            validator=self.name,
            command=args[0] if args else "",
            paths_count=len(paths),
        )

        merged_env = {**_base_env(), **self._config.env}

        start = time.monotonic()
        try:
            result = subprocess.run(  # noqa: S603
                args,
                capture_output=True,
                text=True,
                timeout=self._config.timeout,
                cwd=self._config.cwd,
                env=merged_env,
                check=False,
            )
            elapsed_ms = (time.monotonic() - start) * 1000
        except subprocess.TimeoutExpired:
            elapsed_ms = (time.monotonic() - start) * 1000
            return ValidationResult(
                validator=self.name,
                passed=False,
                issues=[
                    ValidationIssue(
                        message=f"Validation timed out after {self._config.timeout}s",
                        severity=Severity.ERROR,
                    )
                ],
                duration_ms=elapsed_ms,
            )
        except FileNotFoundError:
            elapsed_ms = (time.monotonic() - start) * 1000
            return ValidationResult(
                validator=self.name,
                passed=False,
                issues=[
                    ValidationIssue(
                        message=f"CLI not found: {args[0]!r}",
                        severity=Severity.ERROR,
                    )
                ],
                duration_ms=elapsed_ms,
            )
        except OSError as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            return ValidationResult(
                validator=self.name,
                passed=False,
                issues=[
                    ValidationIssue(
                        message=f"Failed to execute {args[0]!r}: {exc}",
                        severity=Severity.ERROR,
                    )
                ],
                duration_ms=elapsed_ms,
            )

        passed, issues = self.parse_output(result.stdout, result.stderr, result.returncode)

        return ValidationResult(
            validator=self.name,
            passed=passed,
            issues=issues,
            duration_ms=elapsed_ms,
        )


# ── Helpers ────────────────────────────────────────────────────────────


def _base_env() -> dict[str, str]:
    """Return a minimal env dict (inherits current env)."""
    import os

    return dict(os.environ)
