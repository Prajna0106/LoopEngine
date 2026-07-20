"""Configuration schema definition."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Agent-specific configuration."""

    model: str = "claude-sonnet-4-20250514"
    api_key_env: str = "ANTHROPIC_API_KEY"
    timeout: float = 120.0


class ValidationConfig(BaseModel):
    """Validation pipeline configuration."""

    linters: list[str] = Field(default_factory=lambda: ["ruff"])
    type_checkers: list[str] = Field(default_factory=lambda: ["mypy"])
    test_runner: str = "pytest"


class EngineConfig(BaseModel):
    """Top-level engine configuration."""

    max_iterations: int = 5
    default_agent: str = "claude"
    agents: dict[str, AgentConfig] = Field(default_factory=dict)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)


class LoopEngineConfig(BaseModel):
    """Root configuration loaded from loopengine.toml."""

    engine: EngineConfig = Field(default_factory=EngineConfig)
