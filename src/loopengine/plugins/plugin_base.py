"""Abstract plugin base class.

Defines the lifecycle and hook registration contract for all LoopEngine
plugins. Plugins are discovered via entry points and managed by the
plugin registry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Plugin(ABC):
    """Contract for LoopEngine plugins.

    Follows ISP: lifecycle only. Hook registration is handled separately
    by the hook dispatcher; this interface covers load/activate/deactivate.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique plugin identifier (e.g. 'coverage_enhancer')."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Semver version string (e.g. '1.0.0')."""

    @property
    def description(self) -> str:
        """Short human-readable description."""
        return ""

    @abstractmethod
    def activate(self) -> None:
        """Called when the plugin is activated.

        Allocate resources, register hooks, etc.
        """

    @abstractmethod
    def deactivate(self) -> None:
        """Called when the plugin is deactivated.

        Release resources, unregister hooks, etc.
        """

    def on_load(self) -> None:  # noqa: B027
        """Called once after the plugin is imported. Override if needed."""

    def on_unload(self) -> None:  # noqa: B027
        """Called once before the plugin is removed. Override if needed."""

    @abstractmethod
    def get_hooks(self) -> dict[str, Any]:
        """Return a mapping of hook_name → callable for this plugin.

        Returns
        -------
        dict[str, callable]
            Keys are hook names (e.g. 'before_phase', 'after_validation').
            Values are the callables to invoke when the hook fires.
        """
