"""Unit tests for configuration schema."""

from __future__ import annotations

import pytest

from loopengine.infrastructure.config.schema import (
    AgentConfig,
    EngineConfig,
    LoggingConfig,
    LoopEngineConfig,
    PersistenceConfig,
    ValidationConfig,
    default_config,
)


class TestAgentConfig:
    def test_defaults(self) -> None:
        cfg = AgentConfig()
        assert cfg.model == "claude-sonnet-5-20260514"
        assert cfg.api_key_env == "ANTHROPIC_API_KEY"
        assert cfg.timeout == 300.0

    def test_timeout_bounds(self) -> None:
        with pytest.raises(ValueError):
            AgentConfig(timeout=0.0)
        with pytest.raises(ValueError):
            AgentConfig(timeout=999.0)

    def test_temperature_bounds(self) -> None:
        with pytest.raises(ValueError):
            AgentConfig(temperature=-0.1)
        with pytest.raises(ValueError):
            AgentConfig(temperature=3.0)

    def test_blank_model_rejected(self) -> None:
        with pytest.raises(ValueError):
            AgentConfig(model="   ")

    def test_model_stripped(self) -> None:
        cfg = AgentConfig(model="  gpt-4o  ")
        assert cfg.model == "gpt-4o"


class TestValidationConfig:
    def test_defaults(self) -> None:
        cfg = ValidationConfig()
        assert cfg.linters == ["ruff"]
        assert cfg.type_checkers == ["mypy"]
        assert cfg.test_runner == "pytest"
        assert cfg.coverage_threshold == 80

    def test_empty_linters_rejected(self) -> None:
        with pytest.raises(ValueError):
            ValidationConfig(linters=[])

    def test_whitespace_only_linters_rejected(self) -> None:
        with pytest.raises(ValueError):
            ValidationConfig(linters=["  ", "  "])

    def test_coverage_threshold_bounds(self) -> None:
        with pytest.raises(ValueError):
            ValidationConfig(coverage_threshold=-1)
        with pytest.raises(ValueError):
            ValidationConfig(coverage_threshold=101)


class TestPersistenceConfig:
    def test_defaults(self) -> None:
        cfg = PersistenceConfig()
        assert cfg.backend == "json"
        assert cfg.directory == ".loopengine"


class TestLoggingConfig:
    def test_defaults(self) -> None:
        cfg = LoggingConfig()
        assert cfg.level == "INFO"
        assert cfg.format == "console"

    def test_invalid_format_rejected(self) -> None:
        with pytest.raises(ValueError):
            LoggingConfig(format="xml")


class TestEngineConfig:
    def test_defaults(self) -> None:
        cfg = EngineConfig()
        assert cfg.max_iterations == 5
        assert cfg.default_agent == "claude"

    def test_max_iterations_bounds(self) -> None:
        with pytest.raises(ValueError):
            EngineConfig(max_iterations=0)
        with pytest.raises(ValueError):
            EngineConfig(max_iterations=200)


class TestLoopEngineConfig:
    def test_defaults(self) -> None:
        cfg = LoopEngineConfig()
        assert isinstance(cfg.engine, EngineConfig)
        assert isinstance(cfg.validation, ValidationConfig)

    def test_get_agent_default(self) -> None:
        cfg = default_config()
        agent = cfg.get_agent()
        assert agent.model == "claude-sonnet-5-20260514"

    def test_get_agent_by_name(self) -> None:
        cfg = default_config()
        agent = cfg.get_agent("openai")
        assert agent.model == "gpt-4o"

    def test_get_agent_missing_raises(self) -> None:
        cfg = LoopEngineConfig(agents={})
        with pytest.raises(ValueError, match="not configured"):
            cfg.get_agent("nonexistent")


class TestDefaultConfig:
    def test_has_claude_and_openai(self) -> None:
        cfg = default_config()
        assert "claude" in cfg.agents
        assert "openai" in cfg.agents

    def test_is_valid(self) -> None:
        cfg = default_config()
        errors = cfg.model_validate(cfg.model_dump()).model_dump()
        assert errors is not None
