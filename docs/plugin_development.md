# Plugin Development Guide

LoopEngine's plugin system allows you to extend the framework with custom
validators, reviewers, agents, and lifecycle hooks.

## Overview

Plugins are Python modules that contain a class extending `BasePlugin`.
They are discovered from a directory or registered programmatically.

## Creating a Plugin

### 1. Create the plugin module

```python
# my_plugin.py
from loopengine.core.ports.outbound.plugin_registry_port import BasePlugin, PluginMetadata

class MyPlugin(BasePlugin):
    """My custom plugin."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-plugin",
            version="1.0.0",
            author="Your Name",
            description="Does something useful",
            dependencies=[],  # other plugin names required
        )

    def on_register(self) -> None:
        """Called when the plugin is first registered."""
        print("Plugin registered!")

    def on_enable(self) -> None:
        """Called when the plugin is enabled."""
        print("Plugin enabled!")

    def on_disable(self) -> None:
        """Called when the plugin is disabled."""
        print("Plugin disabled!")
```

### 2. Plugin Metadata

The `PluginMetadata` dataclass requires:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Unique plugin name (required) |
| `version` | `str` | Semantic version (default: `"0.1.0"`) |
| `author` | `str` | Plugin author |
| `description` | `str` | Short description |
| `dependencies` | `list[str]` | Names of required plugins |
| `min_loopengine_version` | `str` | Minimum LoopEngine version |

### 3. Lifecycle Hooks

| Hook | When Called |
|------|-----------|
| `on_register()` | Plugin is registered with the registry |
| `on_enable()` | Plugin transitions to enabled state |
| `on_disable()` | Plugin transitions to disabled state |
| `on_unregister()` | Plugin is removed from the registry |

All hooks are optional -- default implementations are no-ops.

## Registering a Plugin

### Programmatically

```python
from loopengine.adapters.outbound.plugins.plugin_registry import InMemoryPluginRegistry

registry = InMemoryPluginRegistry()
plugin = MyPlugin()
registry.register(plugin)
registry.enable("my-plugin")
```

### From a Directory

```python
# Scans for .py files with BasePlugin subclasses
loaded = registry.load_from_directory("/path/to/plugins")
```

### Using the Sample Plugin

LoopEngine includes a sample plugin at
`src/loopengine/adapters/outbound/plugins/sample_plugin.py` for reference.

## Plugin States

| State | Description |
|-------|-------------|
| `REGISTERED` | Plugin is registered but not yet enabled |
| `ENABLED` | Plugin is active and its hooks are called |
| `DISABLED` | Plugin was enabled but is now disabled |
| `ERROR` | Plugin encountered an error during lifecycle |

## Dependencies

Plugins can declare dependencies on other plugins:

```python
class ChildPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="child-plugin",
            dependencies=["parent-plugin"],  # must be enabled first
        )
```

The registry validates that all dependencies are registered and enabled
before enabling a plugin.

## Error Handling

| Exception | When |
|-----------|------|
| `PluginNotFoundError` | Plugin name not in registry |
| `PluginLoadError` | Duplicate plugin name or load failure |
| `PluginDependencyError` | Required dependency not available |
| `HookNotFoundError` | Lifecycle hook not found |
