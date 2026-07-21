"""Plugin-related exceptions."""

from __future__ import annotations

from loopengine.core.domain.exceptions.base import LoopEngineError


class PluginError(LoopEngineError):
    """Base for plugin errors."""

    def __init__(self, message: str = "", *, plugin: str = "") -> None:
        super().__init__(message, code="PLUGIN_ERROR")
        self.plugin = plugin


class PluginLoadError(PluginError):
    """Failed to load a plugin."""

    def __init__(self, plugin: str, reason: str = "") -> None:
        msg = f"Failed to load plugin {plugin!r}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, plugin=plugin)
        self.code = "PLUGIN_LOAD_ERROR"
        self.reason = reason


class PluginNotFoundError(PluginError):
    """Requested plugin is not registered."""

    def __init__(self, plugin: str) -> None:
        super().__init__(f"Plugin not found: {plugin!r}", plugin=plugin)
        self.code = "PLUGIN_NOT_FOUND"


class PluginDependencyError(PluginError):
    """A required plugin dependency is not satisfied."""

    def __init__(self, plugin: str, missing: list[str]) -> None:
        deps = ", ".join(missing)
        super().__init__(
            f"Plugin {plugin!r} has unmet dependencies: {deps}",
            plugin=plugin,
        )
        self.code = "PLUGIN_DEPENDENCY_ERROR"
        self.missing = missing


class HookNotFoundError(PluginError):
    """Requested hook does not exist."""

    def __init__(self, hook_name: str) -> None:
        super().__init__(f"Hook not found: {hook_name}")
        self.code = "HOOK_NOT_FOUND"
        self.hook_name = hook_name
