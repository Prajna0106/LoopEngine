"""Outbound port — prompt management interface.

Defines the contract for loading, versioning, rendering, caching, and
validating prompts. Follows ISP: each concern is a separate method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PromptTemplate:
    """A versioned prompt template with metadata."""

    name: str
    content: str
    version: str = "1.0.0"
    provider: str = "default"
    variables: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    description: str = ""


@dataclass(frozen=True)
class PromptVersion:
    """A historical version of a prompt."""

    version: str
    content: str
    changelog: str = ""


class PromptProvider(ABC):
    """Contract for loading prompts from an external source.

    Follows ISP: only loading. Each provider reads from one source
    (filesystem, database, HTTP, etc.).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this provider (e.g. 'filesystem', 'http')."""

    @abstractmethod
    def load_all(self) -> list[PromptTemplate]:
        """Load all available prompts from this provider."""

    @abstractmethod
    def load(self, name: str) -> PromptTemplate | None:
        """Load a specific prompt by name. Returns None if not found."""


class PromptRegistry(ABC):
    """Contract for prompt versioning, rendering, and caching.

    Follows ISP: versioning, rendering, and querying are separate
    concerns.
    """

    @abstractmethod
    def register(self, template: PromptTemplate) -> None:
        """Register a prompt template. Overwrites existing if same name+version."""

    @abstractmethod
    def get(self, name: str, version: str | None = None) -> PromptTemplate:
        """Get a prompt by name and optional version.

        If version is None, returns the latest version.

        Raises
        ------
        PromptNotFoundError
            If no prompt matches the given name/version.
        """

    @abstractmethod
    def list_prompts(self, *, tag: str | None = None) -> list[PromptTemplate]:
        """List all registered prompts, optionally filtered by tag."""

    @abstractmethod
    def list_versions(self, name: str) -> list[PromptVersion]:
        """List all versions of a prompt.

        Raises
        ------
        PromptNotFoundError
            If no prompt with that name exists.
        """

    @abstractmethod
    def render(self, name: str, variables: dict[str, Any] | None = None) -> str:
        """Render a prompt with variable substitution.

        Uses ``{var}`` syntax for variables. Missing variables raise
        PromptValidationError.

        Raises
        ------
        PromptNotFoundError
            If the prompt is not registered.
        PromptValidationError
            If required variables are missing or template syntax is invalid.
        """

    @abstractmethod
    def invalidate_cache(self, name: str | None = None) -> None:
        """Invalidate cached renders. If name is None, invalidate all."""
