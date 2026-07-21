"""Tests for InMemoryPluginRegistry."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from loopengine.adapters.outbound.plugins.plugin_registry import (
    InMemoryPluginRegistry,
)
from loopengine.core.domain.exceptions.plugin_exceptions import (
    PluginDependencyError,
    PluginLoadError,
    PluginNotFoundError,
)
from loopengine.core.ports.outbound.plugin_registry_port import (
    BasePlugin,
    PluginInfo,
    PluginMetadata,
    PluginState,
)


class SimplePlugin(BasePlugin):
    def __init__(self, name: str = "test-plugin", version: str = "1.0.0") -> None:
        self._name = name
        self._version = version
        self.lifecycle_calls: list[str] = []

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self._name,
            version=self._version,
            description="Test plugin",
            author="test",
        )

    def on_register(self) -> None:
        self.lifecycle_calls.append("register")

    def on_enable(self) -> None:
        self.lifecycle_calls.append("enable")

    def on_disable(self) -> None:
        self.lifecycle_calls.append("disable")

    def on_unregister(self) -> None:
        self.lifecycle_calls.append("unregister")


class DepPlugin(BasePlugin):
    def __init__(self, deps: list[str]) -> None:
        self._deps = deps

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dep-plugin",
            version="1.0.0",
            dependencies=self._deps,
        )


class ConcretePlugin(BasePlugin):
    """A non-abstract plugin that can be instantiated."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="concrete", version="1.0.0")


class TestPluginState:
    def test_values(self) -> None:
        assert PluginState.REGISTERED == "registered"
        assert PluginState.ENABLED == "enabled"
        assert PluginState.DISABLED == "disabled"
        assert PluginState.ERROR == "error"


class TestPluginMetadata:
    def test_defaults(self) -> None:
        m = PluginMetadata(name="p")
        assert m.name == "p"
        assert m.version == "0.1.0"
        assert m.dependencies == []

    def test_custom(self) -> None:
        m = PluginMetadata(name="p", version="2.0.0", dependencies=["a", "b"])
        assert m.version == "2.0.0"
        assert m.dependencies == ["a", "b"]


class TestPluginInfo:
    def test_frozen(self) -> None:
        info = PluginInfo(
            name="p", version="1.0.0", description="", author="", state=PluginState.REGISTERED
        )
        assert info.name == "p"
        assert info.state == PluginState.REGISTERED


class TestInMemoryPluginRegistry:
    def test_register_and_get(self) -> None:
        reg = InMemoryPluginRegistry()
        plugin = SimplePlugin()
        reg.register(plugin)
        assert reg.get("test-plugin") is plugin

    def test_register_duplicate_raises(self) -> None:
        reg = InMemoryPluginRegistry()
        reg.register(SimplePlugin())
        with pytest.raises(PluginLoadError):
            reg.register(SimplePlugin())

    def test_register_calls_on_register(self) -> None:
        reg = InMemoryPluginRegistry()
        plugin = SimplePlugin()
        reg.register(plugin)
        assert "register" in plugin.lifecycle_calls

    def test_unregister(self) -> None:
        reg = InMemoryPluginRegistry()
        plugin = SimplePlugin()
        reg.register(plugin)
        reg.unregister("test-plugin")
        with pytest.raises(PluginNotFoundError):
            reg.get("test-plugin")

    def test_unregister_calls_lifecycle(self) -> None:
        reg = InMemoryPluginRegistry()
        plugin = SimplePlugin()
        reg.register(plugin)
        reg.unregister("test-plugin")
        assert "unregister" in plugin.lifecycle_calls

    def test_unregister_disabled_plugin(self) -> None:
        reg = InMemoryPluginRegistry()
        plugin = SimplePlugin()
        reg.register(plugin)
        reg.disable("test-plugin")
        reg.unregister("test-plugin")
        assert plugin.lifecycle_calls == ["register", "unregister"]

    def test_unregister_not_found_raises(self) -> None:
        reg = InMemoryPluginRegistry()
        with pytest.raises(PluginNotFoundError):
            reg.unregister("nonexistent")

    def test_get_not_found_raises(self) -> None:
        reg = InMemoryPluginRegistry()
        with pytest.raises(PluginNotFoundError):
            reg.get("nonexistent")

    def test_list_plugins_empty(self) -> None:
        reg = InMemoryPluginRegistry()
        assert reg.list_plugins() == []

    def test_list_plugins(self) -> None:
        reg = InMemoryPluginRegistry()
        reg.register(SimplePlugin("a"))
        reg.register(SimplePlugin("b"))
        plugins = reg.list_plugins()
        assert len(plugins) == 2
        names = {p.name for p in plugins}
        assert names == {"a", "b"}

    def test_enable(self) -> None:
        reg = InMemoryPluginRegistry()
        plugin = SimplePlugin()
        reg.register(plugin)
        reg.enable("test-plugin")
        assert reg.is_enabled("test-plugin")
        assert "enable" in plugin.lifecycle_calls

    def test_enable_idempotent(self) -> None:
        reg = InMemoryPluginRegistry()
        plugin = SimplePlugin()
        reg.register(plugin)
        reg.enable("test-plugin")
        reg.enable("test-plugin")
        assert plugin.lifecycle_calls.count("enable") == 1

    def test_enable_not_found_raises(self) -> None:
        reg = InMemoryPluginRegistry()
        with pytest.raises(PluginNotFoundError):
            reg.enable("nonexistent")

    def test_enable_unmet_dependency_raises(self) -> None:
        reg = InMemoryPluginRegistry()
        reg.register(DepPlugin(["missing"]))
        with pytest.raises(PluginDependencyError) as exc_info:
            reg.enable("dep-plugin")
        assert exc_info.value.missing == ["missing"]

    def test_enable_dependency_not_enabled(self) -> None:
        reg = InMemoryPluginRegistry()
        reg.register(SimplePlugin("dep"))
        reg.register(DepPlugin(["dep"]))
        with pytest.raises(PluginDependencyError):
            reg.enable("dep-plugin")

    def test_enable_satisfied_dependency(self) -> None:
        reg = InMemoryPluginRegistry()
        reg.register(SimplePlugin("dep"))
        reg.register(DepPlugin(["dep"]))
        reg.enable("dep")
        reg.enable("dep-plugin")
        assert reg.is_enabled("dep-plugin")

    def test_disable(self) -> None:
        reg = InMemoryPluginRegistry()
        plugin = SimplePlugin()
        reg.register(plugin)
        reg.enable("test-plugin")
        reg.disable("test-plugin")
        assert not reg.is_enabled("test-plugin")
        assert "disable" in plugin.lifecycle_calls

    def test_disable_idempotent(self) -> None:
        reg = InMemoryPluginRegistry()
        plugin = SimplePlugin()
        reg.register(plugin)
        reg.disable("test-plugin")
        reg.disable("test-plugin")
        assert plugin.lifecycle_calls.count("disable") == 0

    def test_disable_not_found_raises(self) -> None:
        reg = InMemoryPluginRegistry()
        with pytest.raises(PluginNotFoundError):
            reg.disable("nonexistent")

    def test_is_enabled_false_by_default(self) -> None:
        reg = InMemoryPluginRegistry()
        reg.register(SimplePlugin())
        assert not reg.is_enabled("test-plugin")

    def test_is_enabled_not_found_raises(self) -> None:
        reg = InMemoryPluginRegistry()
        with pytest.raises(PluginNotFoundError):
            reg.is_enabled("nonexistent")

    def test_unregister_enabled_calls_disable_then_unregister(self) -> None:
        reg = InMemoryPluginRegistry()
        plugin = SimplePlugin()
        reg.register(plugin)
        reg.enable("test-plugin")
        reg.unregister("test-plugin")
        assert plugin.lifecycle_calls == ["register", "enable", "disable", "unregister"]

    def test_plugin_info_state_reflects_enable(self) -> None:
        reg = InMemoryPluginRegistry()
        reg.register(SimplePlugin("p"))
        reg.enable("p")
        infos = reg.list_plugins()
        assert infos[0].state == PluginState.ENABLED

    def test_plugin_info_dependencies(self) -> None:
        reg = InMemoryPluginRegistry()
        reg.register(DepPlugin(["a", "b"]))
        infos = reg.list_plugins()
        assert infos[0].dependencies == ["a", "b"]

    def test_load_from_directory_nonexistent(self) -> None:
        reg = InMemoryPluginRegistry()
        assert reg.load_from_directory("/nonexistent/path") == []

    def test_load_from_directory_empty(self) -> None:
        reg = InMemoryPluginRegistry()
        with tempfile.TemporaryDirectory() as tmpdir:
            assert reg.load_from_directory(tmpdir) == []

    def test_load_from_directory_with_plugin(self) -> None:
        reg = InMemoryPluginRegistry()
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_code = """
from loopengine.core.ports.outbound.plugin_registry_port import BasePlugin, PluginMetadata

class AutoPlugin(BasePlugin):
    @property
    def metadata(self):
        return PluginMetadata(name="auto-loaded", version="1.0.0")
"""
            Path(tmpdir, "my_plugin.py").write_text(plugin_code)
            loaded = reg.load_from_directory(tmpdir)
            assert "auto-loaded" in loaded
            assert reg.get("auto-loaded") is not None

    def test_load_from_directory_skips_private(self) -> None:
        reg = InMemoryPluginRegistry()
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_code = """
from loopengine.core.ports.outbound.plugin_registry_port import BasePlugin, PluginMetadata

class SkippedPlugin(BasePlugin):
    @property
    def metadata(self):
        return PluginMetadata(name="should-not-load", version="1.0.0")
"""
            Path(tmpdir, "_private.py").write_text(plugin_code)
            loaded = reg.load_from_directory(tmpdir)
            assert loaded == []

    def test_load_from_directory_skips_abstract(self) -> None:
        reg = InMemoryPluginRegistry()
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_code = """
from loopengine.core.ports.outbound.plugin_registry_port import BasePlugin, PluginMetadata

class AbstractPlugin(BasePlugin):
    pass
"""
            Path(tmpdir, "abstract.py").write_text(plugin_code)
            loaded = reg.load_from_directory(tmpdir)
            assert loaded == []
