"""Configuration schema — Pydantic models for loop.yaml."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

# ── Enums ───────────────────────────────────────────────────────────────


class AgentBackend(StrEnum):
    """Supported AI agent backends."""

    CLAUDE = "claude"
    OPENAI = "openai"
    COPILOT = "copilot"
    GEMINI = "gemini"
    CUSTOM = "custom"


class OutputFormat(StrEnum):
    """CLI output format."""

    CONSOLE = "console"
    JSON = "json"


class LogLevel(StrEnum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# ── Nested models ───────────────────────────────────────────────────────


class AgentConfig(BaseModel):
    """Configuration for a single agent backend."""

    model: str = Field(default="claude-sonnet-5-20260514", description="Model identifier")
    api_key_env: str = Field(
        default="ANTHROPIC_API_KEY",
        description="Env var name holding the API key",
    )
    timeout: float = Field(
        default=120.0,
        ge=1.0,
        le=600.0,
        description="Request timeout (seconds)",
    )
    max_tokens: int | None = Field(default=None, ge=1, description="Max response tokens")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature")

    @field_validator("model")
    @classmethod
    def model_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("model must not be blank")
        return v.strip()


class ValidationConfig(BaseModel):
    """Validation pipeline configuration."""

    linters: list[str] = Field(default_factory=lambda: ["ruff"])
    type_checkers: list[str] = Field(default_factory=lambda: ["mypy"])
    test_runner: str = Field(default="pytest")
    security_scanner: bool = Field(default=False, description="Enable security scanning")
    coverage_threshold: int = Field(default=80, ge=0, le=100, description="Min coverage %")

    @field_validator("linters", "type_checkers")
    @classmethod
    def no_empty_tools(cls, v: list[str]) -> list[str]:
        cleaned = [t.strip() for t in v if t.strip()]
        if not cleaned:
            raise ValueError("list must contain at least one tool")
        return cleaned


class PersistenceConfig(BaseModel):
    """Workflow state persistence configuration."""

    backend: str = Field(default="json", description="Storage backend (json | sqlite)")
    directory: str = Field(default=".loopengine", description="Storage directory")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: LogLevel = Field(default=LogLevel.INFO)
    format: str = Field(default="console", description="Log format (console | json)")

    @field_validator("format")
    @classmethod
    def valid_format(cls, v: str) -> str:
        if v not in ("console", "json"):
            raise ValueError(f"format must be 'console' or 'json', got {v!r}")
        return v


class CliConfig(BaseModel):
    """CLI behaviour configuration."""

    output_format: OutputFormat = Field(default=OutputFormat.CONSOLE)
    verbose: bool = Field(default=False)


class EngineConfig(BaseModel):
    """Engine-level settings."""

    max_iterations: int = Field(default=5, ge=1, le=100)
    default_agent: str = Field(default="claude")
    project_path: str = Field(default=".")


# ── Root config ─────────────────────────────────────────────────────────


DEFAULT_AGENTS: dict[str, dict[str, Any]] = {
    "claude": {
        "model": "claude-sonnet-5-20260514",
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    "openai": {
        "model": "gpt-4o",
        "api_key_env": "OPENAI_API_KEY",
    },
}


class LoopEngineConfig(BaseModel):
    """Root configuration — matches loop.yaml structure."""

    engine: EngineConfig = Field(default_factory=EngineConfig)
    agents: dict[str, AgentConfig] = Field(default_factory=dict)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cli: CliConfig = Field(default_factory=CliConfig)

    def get_agent(self, name: str | None = None) -> AgentConfig:
        """Return agent config by name, falling back to engine default."""
        agent_name = name or self.engine.default_agent
        if agent_name not in self.agents:
            available = ", ".join(self.agents) or "(none)"
            raise ValueError(f"Agent {agent_name!r} not configured. Available: {available}")
        return self.agents[agent_name]

    def resolve_project_path(self, base: Path | None = None) -> Path:
        """Return the absolute project path."""
        return (base or Path.cwd()).resolve()


def default_config() -> LoopEngineConfig:
    """Return a config with sensible defaults (including default agents)."""
    agents = {k: AgentConfig.model_validate(v) for k, v in DEFAULT_AGENTS.items()}
    return LoopEngineConfig(agents=agents)
