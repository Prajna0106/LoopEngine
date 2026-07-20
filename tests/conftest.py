"""Shared test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture()
def anyio_backend() -> str:
    """Default async backend for anyio/pytest-asyncio."""
    return "asyncio"
