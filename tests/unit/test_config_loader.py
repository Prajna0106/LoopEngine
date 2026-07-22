"""Unit tests for configuration loader."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from loopengine.core.domain.exceptions.config_exceptions import ConfigLoadError
from loopengine.infrastructure.config.loader import (
    _apply_env_overrides,
    _deep_merge,
    _load_yaml,
    find_config_file,
    load_config,
    load_config_file,
    validate_config,
)
from loopengine.infrastructure.config.schema import LoopEngineConfig, default_config

if TYPE_CHECKING:
    from pathlib import Path

# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_yaml(tmp_path: Path) -> Path:
    """Write a minimal YAML config to tmp_path."""
    p = tmp_path / "loop.yaml"
    p.write_text(
        "engine:\n"
        "  max_iterations: 3\n"
        "  default_agent: openai\n"
        "agents:\n"
        "  openai:\n"
        "    model: gpt-4o\n"
        "    api_key_env: OPENAI_API_KEY\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture()
def tmp_toml(tmp_path: Path) -> Path:
    """Write a minimal TOML config to tmp_path."""
    p = tmp_path / "loopengine.toml"
    p.write_text(
        '[engine]\nmax_iterations = 7\ndefault_agent = "claude"\n',
        encoding="utf-8",
    )
    return p


# ── YAML loading ────────────────────────────────────────────────────────


class TestLoadYaml:
    def test_load_valid(self, tmp_yaml: Path) -> None:
        data = _load_yaml(tmp_yaml)
        assert data["engine"]["max_iterations"] == 3
        assert data["engine"]["default_agent"] == "openai"

    def test_load_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.yaml"
        p.write_text("", encoding="utf-8")
        data = _load_yaml(p)
        assert data == {}

    def test_load_nonexistent_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigLoadError):
            _load_yaml(tmp_path / "nope.yaml")

    def test_load_invalid_yaml_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.yaml"
        p.write_text(":\n  - :\n    [invalid", encoding="utf-8")
        with pytest.raises(ConfigLoadError):
            _load_yaml(p)

    def test_load_non_mapping_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "list.yaml"
        p.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ConfigLoadError, match="root element must be a mapping"):
            _load_yaml(p)


# ── TOML loading ────────────────────────────────────────────────────────


class TestLoadToml:
    def test_load_valid(self, tmp_toml: Path) -> None:
        data = _load_yaml(tmp_toml) if tmp_toml.suffix == ".yaml" else load_config_file(tmp_toml)
        assert data["engine"]["max_iterations"] == 7

    def test_load_invalid_toml_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.toml"
        p.write_text("this is not [valid toml", encoding="utf-8")
        with pytest.raises(ConfigLoadError):
            load_config_file(p)


# ── find_config_file ────────────────────────────────────────────────────


class TestFindConfigFile:
    def test_finds_yaml(self, tmp_path: Path) -> None:
        (tmp_path / "loop.yaml").write_text("engine: {}\n", encoding="utf-8")
        assert find_config_file(tmp_path) == tmp_path / "loop.yaml"

    def test_finds_yml(self, tmp_path: Path) -> None:
        (tmp_path / "loop.yml").write_text("engine: {}\n", encoding="utf-8")
        assert find_config_file(tmp_path) == tmp_path / "loop.yml"

    def test_finds_toml(self, tmp_path: Path) -> None:
        (tmp_path / "loopengine.toml").write_text("[engine]\n", encoding="utf-8")
        assert find_config_file(tmp_path) == tmp_path / "loopengine.toml"

    def test_yaml_priority_over_toml(self, tmp_path: Path) -> None:
        (tmp_path / "loop.yaml").write_text("engine: {}\n", encoding="utf-8")
        (tmp_path / "loopengine.toml").write_text("[engine]\n", encoding="utf-8")
        assert find_config_file(tmp_path) == tmp_path / "loop.yaml"

    def test_returns_none_when_missing(self, tmp_path: Path) -> None:
        assert find_config_file(tmp_path) is None


# ── load_config (full pipeline) ─────────────────────────────────────────


class TestLoadConfig:
    def test_load_explicit_yaml(self, tmp_yaml: Path) -> None:
        cfg = load_config(tmp_yaml)
        assert cfg.engine.max_iterations == 3
        assert cfg.engine.default_agent == "openai"

    def test_load_auto_discover(self, tmp_path: Path) -> None:
        (tmp_path / "loop.yaml").write_text(
            "engine:\n  max_iterations: 9\n",
            encoding="utf-8",
        )
        cfg = load_config(project_dir=tmp_path)
        assert cfg.engine.max_iterations == 9

    def test_load_defaults_when_no_file(self, tmp_path: Path) -> None:
        cfg = load_config(project_dir=tmp_path)
        assert cfg.engine.max_iterations == 5

    def test_nonexistent_explicit_path_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigLoadError, match="file not found"):
            load_config(tmp_path / "nope.yaml")


# ── Env var overrides ───────────────────────────────────────────────────


class TestEnvOverrides:
    def test_apply_env_overrides(self) -> None:
        os.environ["LOOP_MAX_ITERATIONS"] = "42"
        try:
            data: dict = {"engine": {"max_iterations": 5}}
            result = _apply_env_overrides(data)
            assert result["engine"]["max_iterations"] == 42
        finally:
            del os.environ["LOOP_MAX_ITERATIONS"]

    def test_env_overrides_invalid_int_ignored(self) -> None:
        os.environ["LOOP_MAX_ITERATIONS"] = "not_a_number"
        try:
            data: dict = {"engine": {"max_iterations": 5}}
            result = _apply_env_overrides(data)
            assert result["engine"]["max_iterations"] == 5
        finally:
            del os.environ["LOOP_MAX_ITERATIONS"]

    def test_load_config_with_env_override(self, tmp_path: Path) -> None:
        os.environ["LOOP_MAX_ITERATIONS"] = "99"
        try:
            cfg = load_config(project_dir=tmp_path)
            assert cfg.engine.max_iterations == 99
        finally:
            del os.environ["LOOP_MAX_ITERATIONS"]


# ── Deep merge ──────────────────────────────────────────────────────────


class TestDeepMerge:
    def test_merge_nested(self) -> None:
        base = {"a": {"b": 1, "c": 2}}
        override = {"a": {"b": 10}}
        result = _deep_merge(base, override)
        assert result["a"]["b"] == 10
        assert result["a"]["c"] == 2

    def test_merge_adds_keys(self) -> None:
        base = {"a": 1}
        override = {"b": 2}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 2}

    def test_merge_override_replaces_dict(self) -> None:
        base = {"a": {"b": 1}}
        override = {"a": "string"}
        result = _deep_merge(base, override)
        assert result["a"] == "string"


# ── validate_config ─────────────────────────────────────────────────────


class TestValidateConfig:
    def test_valid_config_no_warnings(self) -> None:
        cfg = default_config()
        warnings = validate_config(cfg)
        assert warnings == []

    def test_missing_default_agent_warns(self) -> None:
        cfg = LoopEngineConfig(agents={})
        warnings = validate_config(cfg)
        assert any("default_agent" in w for w in warnings)
