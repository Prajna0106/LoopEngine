"""Outbound port — validator interface.

Defines the contract for artifact validation. Each validator wraps an
external tool (linter, type checker, test runner, security scanner)
behind a uniform interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    """Issue severity level."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ValidationIssue:
    """A single issue found during validation."""

    message: str
    file: str = ""
    line: int = 0
    column: int = 0
    severity: Severity = Severity.ERROR
    rule: str = ""


@dataclass(frozen=True)
class ValidationResult:
    """Aggregated result from a single validator."""

    validator: str
    passed: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)


class Validator(ABC):
    """Contract for artifact validators.

    Follows ISP: only validation. Each concrete validator wraps one
    external tool (ruff, mypy, pytest, bandit, etc.).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this validator (e.g. 'ruff', 'mypy')."""

    @abstractmethod
    def validate(
        self,
        paths: list[str],
        *,
        content: dict[str, str] | None = None,
        config: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Validate the given paths or in-memory content.

        Parameters
        ----------
        paths:
            File system paths to validate.
        content:
            Optional in-memory file contents {path: content}. When provided,
            validators should prefer this over reading from disk.
        config:
            Optional tool-specific configuration overrides.

        Raises
        ------
        ValidationError
            If the validator itself fails (e.g. tool not installed).
        """
