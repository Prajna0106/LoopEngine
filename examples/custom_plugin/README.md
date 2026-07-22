# Custom Plugin Example

This example shows how to create a custom LoopEngine plugin.

## Create the Plugin

```python
# my_validator_plugin.py
from loopengine.core.ports.outbound.plugin_registry_port import BasePlugin, PluginMetadata

class CustomValidatorPlugin(BasePlugin):
    """Validates custom coding standards."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="custom-validator",
            version="1.0.0",
            description="Enforces custom coding standards",
        )

    def on_enable(self) -> None:
        print("Custom validator enabled!")
```

## Register the Plugin

```python
from loopengine.adapters.outbound.plugins.plugin_registry import InMemoryPluginRegistry

registry = InMemoryPluginRegistry()
plugin = CustomValidatorPlugin()
registry.register(plugin)
registry.enable("custom-validator")
```

## Load from Directory

```python
# Scans plugins/ directory for BasePlugin subclasses
loaded = registry.load_from_directory("plugins")
```

## See Also

- [Plugin Development Guide](../../docs/plugin_development.md)
- [API Reference](../../docs/api_reference.md)
