"""Outbound port — plugin registry interface.

Defines the contract for plugin discovery, registration, lifecycle
management, and dependency resolution. Follows ISP: each concern is
a separate method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum


class PluginState(StrEnum):
    """Plugin lifecycle state."""

    REGISTERED = "registered"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass(frozen=True)
class PluginMetadata:
    """Declarative metadata for a plugin."""

    name: str
    version: str = "0.1.0"
    author: str = ""
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    min_loopengine_version: str = ""


@dataclass(frozen=True)
class PluginInfo:
    """Summary of a registered plugin."""

    name: str
    version: str
    description: str
    author: str
    state: PluginState
    dependencies: list[str] = field(default_factory=list)


class BasePlugin(ABC):
    """Abstract base for all plugins.

    Plugins implement lifecycle hooks. The registry calls these at
    appropriate times. Default implementations are no-ops so plugins
    only override what they need.
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return declarative metadata for this plugin."""

    def on_register(self) -> None:  # noqa: B027
        """Called when the plugin is first registered."""

    def on_enable(self) -> None:  # noqa: B027
        """Called when the plugin transitions to enabled."""

    def on_disable(self) -> None:  # noqa: B027
        """Called when the plugin transitions to disabled."""

    def on_unregister(self) -> None:  # noqa: B027
        """Called when the plugin is removed from the registry."""


class PluginRegistry(ABC):
    """Contract for plugin lifecycle management.

    Follows ISP: registration, discovery, enable/disable, and dependency
    queries are separate concerns.
    """

    @abstractmethod
    def register(self, plugin: BasePlugin) -> None:
        """Register a plugin instance.

        Raises
        ------
        PluginLoadError
            If a plugin with the same name is already registered.
        """

    @abstractmethod
    def unregister(self, name: str) -> None:
        """Remove a plugin by name.

        Raises
        ------
        PluginNotFoundError
            If the plugin is not registered.
        """

    @abstractmethod
    def get(self, name: str) -> BasePlugin:
        """Retrieve a registered plugin by name.

        Raises
        ------
        PluginNotFoundError
            If the plugin is not registered.
        """

    @abstractmethod
    def list_plugins(self) -> list[PluginInfo]:
        """Return summary info for all registered plugins."""

    @abstractmethod
    def enable(self, name: str) -> None:
        """Enable a registered plugin.

        Triggers on_enable() lifecycle hook. Validates dependencies
        are satisfied.

        Raises
        ------
        PluginNotFoundError
            If the plugin is not registered.
        PluginDependencyError
            If a required dependency is not registered or enabled.
        """

    @abstractmethod
    def disable(self, name: str) -> None:
        """Disable a registered plugin.

        Triggers on_disable() lifecycle hook.

        Raises
        ------
        PluginNotFoundError
            If the plugin is not registered.
        """

    @abstractmethod
    def is_enabled(self, name: str) -> bool:
        """Check if a plugin is in the enabled state."""

    @abstractmethod
    def load_from_directory(self, path: str) -> list[str]:
        """Discover and register plugins from a directory.

        Scans for Python modules containing BasePlugin subclasses.
        Returns list of successfully loaded plugin names.
        """
