"""Configuration manager — load, save, merge, defaults."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from loopengine.infrastructure.config.loader import (
    find_config_file,
    load_config,
)
from loopengine.infrastructure.config.schema import (
    LoopEngineConfig,
    default_config,
)

# ── Default config YAML ────────────────────────────────────────────────

DEFAULT_CONFIG_YAML = """\
# LoopEngine configuration
# See docs/configuration_reference.md for all options.

engine:
  max_iterations: 5
  default_agent: claude
  project_path: "."

agents:
  claude:
    model: claude-sonnet-4-20250514
    api_key_env: ANTHROPIC_API_KEY
    timeout: 120.0
  openai:
    model: gpt-4o
    api_key_env: OPENAI_API_KEY
    timeout: 120.0

validation:
  linters:
    - ruff
  type_checkers:
    - mypy
  test_runner: pytest
  security_scanner: false
  coverage_threshold: 80

persistence:
  backend: json
  directory: .loopengine

logging:
  level: INFO
  format: console

cli:
  output_format: console
  verbose: false
"""


class ConfigManager:
    """High-level configuration manager.

    Usage::

        mgr = ConfigManager()
        config = mgr.load()                   # auto-discover config file
        config = mgr.load("loop.yaml")        # explicit path
        mgr.save_default(".")                 # write loop.yaml to dir
    """

    def __init__(self, project_dir: Path | None = None) -> None:
        self._project_dir = project_dir or Path.cwd()
        self._config: LoopEngineConfig | None = None
        self._config_path: Path | None = None

    # ── Loading ─────────────────────────────────────────────────────

    def load(self, config_path: str | Path | None = None) -> LoopEngineConfig:
        """Load configuration from file + env vars.

        If *config_path* is None, auto-discovers loop.yaml / loopengine.toml.
        """
        path = Path(config_path) if config_path else None
        self._config = load_config(path, project_dir=self._project_dir)
        self._config_path = path
        return self._config

    def load_from_dict(self, data: dict[str, Any]) -> LoopEngineConfig:
        """Build config from a raw dictionary (useful in tests)."""
        merged = default_config().model_dump()
        merged = _deep_merge(merged, data)
        self._config = LoopEngineConfig.model_validate(merged)
        return self._config

    @property
    def config(self) -> LoopEngineConfig:
        """Return the loaded config (loads defaults if not yet loaded)."""
        if self._config is None:
            self._config = default_config()
        return self._config

    # ── Saving ──────────────────────────────────────────────────────

    def save_default(self, directory: Path | str | None = None) -> Path:
        """Write a default loop.yaml and return the path."""
        dest = Path(directory or self._project_dir) / "loop.yaml"
        dest.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
        return dest

    def save(self, config: LoopEngineConfig | None = None) -> Path:
        """Save the current (or provided) config to its source file."""
        cfg = config or self.config
        path = self._config_path or (self._project_dir / "loop.yaml")
        data = cfg.model_dump(mode="json")
        path.write_text(yaml.safe_dump(data, default_flow_style=False), encoding="utf-8")
        return path

    # ── Introspection ───────────────────────────────────────────────

    def exists(self) -> bool:
        """Check if a config file exists in the project directory."""
        return find_config_file(self._project_dir) is not None

    def get_config_path(self) -> Path | None:
        """Return the discovered config file path, or None."""
        return find_config_file(self._project_dir)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the current config to a plain dict."""
        return self.config.model_dump(mode="json")

    def to_yaml(self) -> str:
        """Serialize the current config to a YAML string."""
        data = self.config.model_dump(mode="json")
        result: str = yaml.safe_dump(data, default_flow_style=False)
        return result


# ── Helpers ─────────────────────────────────────────────────────────────


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
