"""Dependency injection container."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loopengine.core.ports.inbound.orchestrator_port import OrchestratorPort
    from loopengine.infrastructure.config.settings import Settings


class Container:
    """Lightweight DI container — wires ports to adapters.

    This is the single composition root for the CLI application.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._orchestrator: OrchestratorPort | None = None

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def orchestrator(self) -> OrchestratorPort:
        if self._orchestrator is None:
            raise RuntimeError(
                "OrchestratorPort not wired. Call container.wire() or set orchestrator explicitly."
            )
        return self._orchestrator

    def wire(self, *, orchestrator: OrchestratorPort | None = None) -> None:
        """Wire all port implementations."""
        if orchestrator is not None:
            self._orchestrator = orchestrator
        # Future: wire persistence, event bus, agent adapters, etc.

    def set_orchestrator(self, orchestrator: OrchestratorPort) -> None:
        """Override the orchestrator (useful in tests)."""
        self._orchestrator = orchestrator
