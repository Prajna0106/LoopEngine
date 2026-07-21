"""Outbound port — memory store interface.

Defines the contract for context and history persistence. A memory store
retains workflow state across iterations and provides retrieval by key
or prefix.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MemoryStore(ABC):
    """Contract for context/memory persistence.

    Follows ISP: only key-value storage and retrieval. Does not dictate
    the storage backend (in-memory, SQLite, Redis, etc.).
    """

    @abstractmethod
    def get(self, key: str) -> dict[str, Any] | None:
        """Retrieve a stored value by key. Returns None if not found."""

    @abstractmethod
    def put(self, key: str, value: dict[str, Any]) -> None:
        """Store a value under *key*, overwriting any existing value."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a stored value. Returns True if the key existed."""

    @abstractmethod
    def list_keys(self, *, prefix: str = "") -> list[str]:
        """Return all keys, optionally filtered by *prefix*."""

    @abstractmethod
    def clear(self) -> int:
        """Delete all stored values. Returns the number of entries removed."""

    @abstractmethod
    def contains(self, key: str) -> bool:
        """Return True if *key* exists in the store."""
