"""Shared subprocess utilities for adapters.

Provides common helpers for CLI-based adapters (agents, validators)
to avoid code duplication across base classes.
"""

from __future__ import annotations

import os
import shutil


def base_env() -> dict[str, str]:
    """Return a copy of the current process environment.

    Used by subprocess-based adapters to inherit the parent environment
    while allowing callers to overlay custom values.
    """
    return dict(os.environ)


def is_command_available(command: list[str]) -> bool:
    """Check whether the first element of *command* exists on PATH.

    Returns ``False`` for an empty command list.
    """
    cmd = command[0] if command else ""
    return shutil.which(cmd) is not None


def combine_output(stdout: str, stderr: str) -> str:
    """Combine stdout and stderr into a single string for parsing."""
    return stdout + "\n" + stderr
