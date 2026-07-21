"""Sample plugin demonstrating the LoopEngine plugin framework.

This plugin registers itself with the plugin registry and provides
a simple hook that logs when enabled/disabled.
"""

from __future__ import annotations

from loopengine.core.ports.outbound.plugin_registry_port import (
    BasePlugin,
    PluginMetadata,
)


class SamplePlugin(BasePlugin):
    """A minimal sample plugin for demonstration purposes."""

    def __init__(self) -> None:
        self.registered = False
        self.enabled = False
        self.disabled = False

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="sample",
            version="1.0.0",
            author="LoopEngine Team",
            description="A sample plugin for demonstration",
            dependencies=[],
        )

    def on_register(self) -> None:
        self.registered = True

    def on_enable(self) -> None:
        self.enabled = True
        self.disabled = False

    def on_disable(self) -> None:
        self.disabled = True
        self.enabled = False

    def on_unregister(self) -> None:
        self.registered = False
        self.enabled = False
        self.disabled = False
