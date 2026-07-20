"""Common type aliases."""

from __future__ import annotations

from typing import Any, TypeVar

T = TypeVar("T")
E = TypeVar("E")

JSON = dict[str, Any]
CommitHash = str
FilePath = str
