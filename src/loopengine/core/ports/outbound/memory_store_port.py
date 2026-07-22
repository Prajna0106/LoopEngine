"""Outbound port — memory store interface.

Defines the contract for context and history persistence. A memory store
retains workflow state across iterations and provides retrieval by key
or prefix. Supports typed repositories for domain objects.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StoredExecution:
    """A serialized execution record."""

    workflow_id: str
    goal: str
    status: str
    started_at: str
    completed_at: str = ""
    iterations: int = 0
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StoredReflection:
    """A serialized reflection record."""

    execution_id: str
    iteration: int
    decision: str
    issues_count: int = 0
    suggestions_count: int = 0
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StoredReview:
    """A serialized review record."""

    execution_id: str
    score: float
    verdict: str
    issues_count: int = 0
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StoredProjectMeta:
    """Project metadata record."""

    project_path: str
    name: str = ""
    language: str = ""
    framework: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


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


class ExecutionHistory(ABC):
    """Repository for execution history records."""

    @abstractmethod
    def save(self, execution: StoredExecution) -> None:
        """Save or update an execution record."""

    @abstractmethod
    def get(self, workflow_id: str) -> StoredExecution | None:
        """Get an execution by workflow ID."""

    @abstractmethod
    def list_all(self) -> list[StoredExecution]:
        """List all execution records."""

    @abstractmethod
    def delete(self, workflow_id: str) -> bool:
        """Delete an execution record. Returns True if it existed."""


class ReflectionStore(ABC):
    """Repository for reflection records."""

    @abstractmethod
    def save(self, reflection: StoredReflection) -> None:
        """Save a reflection record."""

    @abstractmethod
    def list_for_execution(self, execution_id: str) -> list[StoredReflection]:
        """List all reflections for a given execution, sorted by iteration."""

    @abstractmethod
    def delete(self, execution_id: str) -> int:
        """Delete all reflections for an execution. Returns count deleted."""


class ReviewStore(ABC):
    """Repository for review records."""

    @abstractmethod
    def save(self, review: StoredReview) -> None:
        """Save a review record."""

    @abstractmethod
    def list_for_execution(self, execution_id: str) -> list[StoredReview]:
        """List all reviews for a given execution."""

    @abstractmethod
    def delete(self, execution_id: str) -> int:
        """Delete all reviews for an execution. Returns count deleted."""


class ProjectMetaStore(ABC):
    """Repository for project metadata records."""

    @abstractmethod
    def save(self, meta: StoredProjectMeta) -> None:
        """Save or update project metadata."""

    @abstractmethod
    def get(self, project_path: str) -> StoredProjectMeta | None:
        """Get metadata for a project by path."""

    @abstractmethod
    def list_all(self) -> list[StoredProjectMeta]:
        """List all project metadata records."""

    @abstractmethod
    def delete(self, project_path: str) -> bool:
        """Delete project metadata. Returns True if it existed."""
