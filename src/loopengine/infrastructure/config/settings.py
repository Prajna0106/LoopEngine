"""Pydantic settings — env-var-only runtime settings for the CLI."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Lightweight env-var settings for CLI bootstrap.

    This is NOT the project config (that's LoopEngineConfig).
    This captures runtime env vars needed before the config file is loaded.
    """

    model_config = {"env_prefix": "LOOP_", "env_file": ".env", "extra": "ignore"}

    log_level: str = Field(default="INFO")
    log_format: str = Field(default="console")
    output_format: str = Field(default="console")
    verbose: bool = Field(default=False)
