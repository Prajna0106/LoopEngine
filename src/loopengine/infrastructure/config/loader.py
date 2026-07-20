"""Configuration file loader — YAML, TOML, env vars."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

import yaml

from loopengine.core.domain.exceptions.base import LoopEngineError
from loopengine.infrastructure.config.schema import (
    LoopEngineConfig,
    default_config,
)


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


# ── File loaders ────────────────────────────────────────────────────────


def _load_yaml(path: Path) -> dict[str, Any]:
    """Parse a YAML file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigLoadError(str(path), str(exc)) from exc

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigLoadError(str(path), str(exc)) from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigLoadError(str(path), "root element must be a mapping")
    return data


def _load_toml(path: Path) -> dict[str, Any]:
    """Parse a TOML file."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ConfigLoadError(str(path), str(exc)) from exc

    try:
        data = tomllib.loads(raw.decode())
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise ConfigLoadError(str(path), str(exc)) from exc

    return data


# ── Env var overrides ───────────────────────────────────────────────────

_ENV_MAP: dict[str, tuple[str, type]] = {
    "LOOP_MAX_ITERATIONS": ("engine.max_iterations", int),
    "LOOP_DEFAULT_AGENT": ("engine.default_agent", str),
    "LOOP_LOG_LEVEL": ("logging.level", str),
    "LOOP_LOG_FORMAT": ("logging.format", str),
    "LOOP_OUTPUT_FORMAT": ("cli.output_format", str),
    "LOOP_PERSISTENCE_BACKEND": ("persistence.backend", str),
    "LOOP_PERSISTENCE_DIR": ("persistence.directory", str),
    "LOOP_PROJECT_PATH": ("engine.project_path", str),
}


def _apply_env_overrides(data: dict[str, Any]) -> dict[str, Any]:
    """Overlay LOOP_* environment variables onto the config dict."""
    for env_var, (dotted_key, cast_fn) in _ENV_MAP.items():
        value = os.environ.get(env_var)
        if value is None:
            continue

        # Cast to target type
        try:
            typed_value: Any = cast_fn(value)
        except (ValueError, TypeError):
            continue

        # Set nested key
        parts = dotted_key.split(".")
        node = data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = typed_value

    return data


# ── Agent env var expansion ─────────────────────────────────────────────


def _expand_agent_env_keys(data: dict[str, Any]) -> dict[str, Any]:
    """For each agent, if api_key_env is set and the env var exists, note it."""
    agents = data.get("agents", {})
    for _name, agent_cfg in agents.items():
        if not isinstance(agent_cfg, dict):
            continue
        env_var = agent_cfg.get("api_key_env", "")
        if env_var and env_var not in os.environ:
            # Don't fail — just leave it for runtime to handle
            pass
    return data


# ── Public API ──────────────────────────────────────────────────────────


def find_config_file(project_dir: Path | None = None) -> Path | None:
    """Search for a config file in priority order.

    Priority: loop.yaml > loop.yml > loopengine.toml
    """
    base = project_dir or Path.cwd()
    candidates = [
        base / "loop.yaml",
        base / "loop.yml",
        base / "loopengine.toml",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_config_file(path: Path) -> dict[str, Any]:
    """Load raw config dict from a YAML or TOML file."""
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return _load_yaml(path)
    if suffix == ".toml":
        return _load_toml(path)
    raise ConfigLoadError(str(path), f"unsupported format: {suffix}")


def load_config(
    config_path: Path | str | None = None,
    *,
    project_dir: Path | None = None,
) -> LoopEngineConfig:
    """Load, merge, and validate the full configuration.

    Resolution order:
    1. Defaults
    2. Config file (YAML or TOML)
    3. Environment variable overrides (LOOP_*)
    """
    # Step 1: start with defaults
    config = default_config()
    data = config.model_dump()

    # Step 2: find or load config file
    if config_path is not None:
        path = Path(config_path)
        if not path.exists():
            raise ConfigLoadError(str(path), "file not found")
        file_data = load_config_file(path)
    else:
        found = find_config_file(project_dir)
        file_data = load_config_file(found) if found is not None else {}

    # Deep-merge file data onto defaults
    data = _deep_merge(data, file_data)

    # Step 3: env var overrides
    data = _apply_env_overrides(data)

    # Step 4: expand agent env key references
    data = _expand_agent_env_keys(data)

    # Step 5: validate
    try:
        return LoopEngineConfig.model_validate(data)
    except Exception as exc:
        raise ConfigValidationError([str(exc)]) from exc


def validate_config(config: LoopEngineConfig) -> list[str]:
    """Validate a config and return a list of warnings (empty = OK)."""
    warnings: list[str] = []

    if config.engine.default_agent not in config.agents:
        warnings.append(f"default_agent {config.engine.default_agent!r} has no configuration")

    if config.engine.max_iterations < 1:
        warnings.append("max_iterations must be >= 1")

    if not config.validation.linters:
        warnings.append("no linters configured")

    return warnings


# ── Helpers ─────────────────────────────────────────────────────────────


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base* (mutates base)."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
