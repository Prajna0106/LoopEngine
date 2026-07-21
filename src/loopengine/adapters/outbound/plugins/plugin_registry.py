"""Concrete plugin registry adapter.

Provides in-memory plugin registration, lifecycle management,
dependency resolution, and filesystem discovery.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

from loopengine.core.domain.exceptions.plugin_exceptions import (
    PluginDependencyError,
    PluginLoadError,
    PluginNotFoundError,
)
from loopengine.core.ports.outbound.plugin_registry_port import (
    BasePlugin,
    PluginInfo,
    PluginMetadata,
    PluginRegistry,
    PluginState,
)


class InMemoryPluginRegistry(PluginRegistry):
    """In-memory implementation of the plugin registry.

    Stores plugin instances in a dict keyed by name. Manages lifecycle
    transitions and dependency validation.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, _PluginEntry] = {}

    def register(self, plugin: BasePlugin) -> None:
        meta = plugin.metadata
        if meta.name in self._plugins:
            raise PluginLoadError(meta.name, "already registered")
        self._plugins[meta.name] = _PluginEntry(
            plugin=plugin,
            metadata=meta,
            state=PluginState.REGISTERED,
        )
        plugin.on_register()

    def unregister(self, name: str) -> None:
        entry = self._get_entry(name)
        if entry.state == PluginState.ENABLED:
            entry.plugin.on_disable()
        entry.plugin.on_unregister()
        del self._plugins[name]

    def get(self, name: str) -> BasePlugin:
        return self._get_entry(name).plugin

    def list_plugins(self) -> list[PluginInfo]:
        return [
            PluginInfo(
                name=e.metadata.name,
                version=e.metadata.version,
                description=e.metadata.description,
                author=e.metadata.author,
                state=e.state,
                dependencies=list(e.metadata.dependencies),
            )
            for e in self._plugins.values()
        ]

    def enable(self, name: str) -> None:
        entry = self._get_entry(name)
        missing = self._check_dependencies(entry.metadata)
        if missing:
            raise PluginDependencyError(name, missing)
        if entry.state == PluginState.ENABLED:
            return
        entry.state = PluginState.ENABLED
        entry.plugin.on_enable()

    def disable(self, name: str) -> None:
        entry = self._get_entry(name)
        if entry.state == PluginState.DISABLED:
            return
        if entry.state == PluginState.ENABLED:
            entry.plugin.on_disable()
        entry.state = PluginState.DISABLED

    def is_enabled(self, name: str) -> bool:
        entry = self._get_entry(name)
        return entry.state == PluginState.ENABLED

    def load_from_directory(self, path: str) -> list[str]:
        plugin_dir = Path(path)
        if not plugin_dir.is_dir():
            return []
        loaded: list[str] = []
        for py_file in plugin_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                plugin_name = self._load_module_from_path(py_file)
                if plugin_name:
                    loaded.append(plugin_name)
            except Exception:  # noqa: S112
                continue
        return loaded

    def _load_module_from_path(self, file_path: Path) -> str | None:
        module_name = f"loopengine_plugin_{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BasePlugin)
                and attr is not BasePlugin
                and not getattr(attr, "__abstractmethods__", None)
            ):
                instance = attr()
                if not self._plugin_exists(instance.metadata.name):
                    self.register(instance)
                    return instance.metadata.name
        return None

    def _plugin_exists(self, name: str) -> bool:
        return name in self._plugins

    def _check_dependencies(self, metadata: PluginMetadata) -> list[str]:
        return [
            dep
            for dep in metadata.dependencies
            if dep not in self._plugins or self._plugins[dep].state != PluginState.ENABLED
        ]

    def _get_entry(self, name: str) -> _PluginEntry:
        if name not in self._plugins:
            raise PluginNotFoundError(name)
        return self._plugins[name]


class _PluginEntry:
    """Internal bookkeeping for a registered plugin."""

    __slots__ = ("metadata", "plugin", "state")

    def __init__(
        self,
        plugin: BasePlugin,
        metadata: PluginMetadata,
        state: PluginState,
    ) -> None:
        self.plugin = plugin
        self.metadata = metadata
        self.state = state
