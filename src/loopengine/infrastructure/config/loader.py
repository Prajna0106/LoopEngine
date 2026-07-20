"""Configuration file loader."""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

from loopengine.core.domain.exceptions.base import LoopEngineError
from loopengine.infrastructure.config.schema import LoopEngineConfig

if TYPE_CHECKING:
    from pathlib import Path


class ConfigLoadError(LoopEngineError):
    """Failed to load configuration."""

    def __init__(self, path: str, reason: str = "") -> None:
        msg = f"Cannot load config: {path}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg, code="CONFIG_LOAD_ERROR")


def load_config(path: Path) -> LoopEngineConfig:
    """Load and validate a loopengine.toml file."""
    if not path.exists():
        return LoopEngineConfig()

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ConfigLoadError(str(path), str(exc)) from exc

    try:
        data = tomllib.loads(raw.decode())
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise ConfigLoadError(str(path), str(exc)) from exc

    return LoopEngineConfig.model_validate(data)
