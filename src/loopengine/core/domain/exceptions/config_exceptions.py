"""Configuration-related exceptions."""

from __future__ import annotations

from loopengine.core.domain.exceptions.base import LoopEngineError


class ConfigLoadError(LoopEngineError):
    """Failed to load configuration."""

    def __init__(self, path: str, reason: str = "") -> None:
        msg = f"Cannot load config: {path}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg, code="CONFIG_LOAD_ERROR")


class ConfigValidationError(LoopEngineError):
    """Configuration failed validation."""

    def __init__(self, errors: list[str]) -> None:
        msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(msg, code="CONFIG_VALIDATION_ERROR")
        self.errors = errors
