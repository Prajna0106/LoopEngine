"""Pydantic settings configuration."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class LogLevel(StrEnum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class OutputFormat(StrEnum):
    """Supported output formats."""

    CONSOLE = "console"
    JSON = "json"


class Settings(BaseSettings):
    """Application settings loaded from env / config file."""

    model_config = {"env_prefix": "LOOP_", "env_file": ".env", "extra": "ignore"}

    # Engine
    max_iterations: int = Field(default=5, description="Max improvement iterations")
    default_agent: str = Field(default="claude", description="Default agent backend")

    # Paths
    config_path: str = Field(default="loopengine.toml", description="Config file path")
    project_path: str = Field(default=".", description="Project root")

    # CLI
    output_format: OutputFormat = Field(default=OutputFormat.CONSOLE)
    log_level: LogLevel = Field(default=LogLevel.INFO)

    # Agent defaults
    agent_model: str = Field(default="claude-sonnet-4-20250514")
    request_timeout: float = Field(default=120.0, description="Agent timeout in seconds")

    def resolve_config_path(self) -> Path:
        """Return the absolute config file path."""
        return Path(self.config_path).resolve()

    def resolve_project_path(self) -> Path:
        """Return the absolute project path."""
        return Path(self.project_path).resolve()
