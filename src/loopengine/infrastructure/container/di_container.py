"""Dependency injection container.

Provides lazy resolution, singleton caching, factory support, and a
backward-compatible ``wire()`` API for the CLI layer.  No business
implementations are registered here — this is pure DI infrastructure.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, TypeVar, overload

from loopengine.infrastructure.container.registry import RegistrationKind, ServiceRegistry

if TYPE_CHECKING:
    from loopengine.infrastructure.config.settings import Settings

T = TypeVar("T")

# Sentinel for distinguishing "no default" from ``None`` default.
_SENTINEL = object()


class Container:
    """DI container with lazy resolution and singleton caching.

    Features
    --------
    * **Lazy loading** — instances are created on first ``resolve()``, not
      at registration time.
    * **Singleton support** — services registered with ``singleton=True``
      (the default) are cached after first creation.
    * **Factory support** — arbitrary callables can serve as factories.
    * **Instance registration** — pre-built objects can be injected directly.
    * **Thread-safe** — resolution is guarded by a lock.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings
        self._registry = ServiceRegistry()
        self._cache: dict[type, object] = {}
        self._lock = threading.Lock()

    # ── Settings ──────────────────────────────────────────────────────

    @property
    def settings(self) -> Settings | None:
        return self._settings

    # ── Registration (delegates to registry) ──────────────────────────

    def register(
        self,
        interface: type[T],
        implementation: type[T] | None = None,
        *,
        singleton: bool = True,
    ) -> None:
        """Register a class for *interface*."""
        self._registry.register(interface, implementation, singleton=singleton)

    def register_factory(
        self,
        interface: type[T],
        factory: object,
        *,
        singleton: bool = True,
    ) -> None:
        """Register a factory callable for *interface*."""
        self._registry.register_factory(interface, factory, singleton=singleton)

    def register_instance(
        self,
        interface: type[T],
        instance: T,
    ) -> None:
        """Register a pre-built instance for *interface*."""
        self._registry.register_instance(interface, instance)

    # ── Resolution ────────────────────────────────────────────────────

    @overload
    def resolve(self, interface: type[T]) -> T: ...
    @overload
    def resolve(self, interface: type[T], default: T) -> T: ...

    def resolve(
        self,
        interface: type[T],
        default: object = _SENTINEL,
    ) -> T:
        """Resolve *interface* to an instance.

        1. If an instance is cached, return it immediately.
        2. If a descriptor exists, create the instance (lazily).
        3. If *default* is provided, return it instead of raising.
        4. Otherwise raise ``KeyError``.
        """
        # Fast path: already cached
        if interface in self._cache:
            return self._cache[interface]  # type: ignore[return-value]

        descriptor = self._registry.get(interface)

        if descriptor is None:
            if default is not _SENTINEL:
                return default  # type: ignore[return-value]
            raise KeyError(f"No registration for {interface.__qualname__}")

        with self._lock:
            # Double-check after acquiring lock
            if interface in self._cache:
                return self._cache[interface]  # type: ignore[return-value]

            instance = self._create(descriptor)

            if descriptor.singleton:
                self._cache[interface] = instance

            return instance  # type: ignore[return-value]

    def has(self, interface: type) -> bool:
        """Return True if *interface* can be resolved."""
        return self._registry.has(interface) or interface in self._cache

    def resolve_all(self, *interfaces: type) -> tuple[object, ...]:
        """Resolve multiple interfaces in order."""
        return tuple(self.resolve(iface) for iface in interfaces)

    # ── Cache management ──────────────────────────────────────────────

    def cache(self, interface: type[T], instance: T) -> None:
        """Manually cache an instance (useful in tests)."""
        self._cache[interface] = instance

    def invalidate(self, interface: type) -> bool:
        """Remove a cached instance. Returns True if it was present."""
        return self._cache.pop(interface, None) is not None

    def reset(self) -> None:
        """Clear all cached instances. Registrations are preserved."""
        self._cache.clear()

    def teardown(self) -> None:
        """Clear cache and all registrations."""
        self._cache.clear()
        self._registry.clear()

    # ── Registry access ───────────────────────────────────────────────

    @property
    def registry(self) -> ServiceRegistry:
        """Direct access to the underlying registry (for inspection)."""
        return self._registry

    # ── Backward-compatible wire / orchestrator API ───────────────────

    def wire(self, *, orchestrator: object | None = None) -> None:
        """Wire port implementations (backward-compatible shortcut).

        Callers can still pass explicit implementations; the container
        stores them via ``register_instance``.
        """
        if orchestrator is not None:
            from loopengine.core.ports.inbound.orchestrator_port import OrchestratorPort

            self.register_instance(OrchestratorPort, orchestrator)

    @property
    def orchestrator(self) -> object:
        """Resolve the OrchestratorPort (backward-compatible)."""
        from loopengine.core.ports.inbound.orchestrator_port import OrchestratorPort

        try:
            return self.resolve(OrchestratorPort)  # type: ignore[type-abstract]
        except KeyError:
            raise RuntimeError(
                "OrchestratorPort not wired. Call container.wire() or register it explicitly."
            ) from None

    def set_orchestrator(self, orchestrator: object) -> None:
        """Override the orchestrator (useful in tests)."""
        from loopengine.core.ports.inbound.orchestrator_port import OrchestratorPort

        self.register_instance(OrchestratorPort, orchestrator)

    # ── Private helpers ───────────────────────────────────────────────

    def _create(self, descriptor: object) -> object:
        """Instantiate a service from its descriptor."""
        from loopengine.infrastructure.container.registry import ServiceDescriptor

        desc: ServiceDescriptor = descriptor  # type: ignore[assignment]

        if desc.kind == RegistrationKind.INSTANCE:
            return desc.instance

        if desc.kind == RegistrationKind.FACTORY:
            return desc.factory()

        # RegistrationKind.CLASS
        if desc.implementation is None:
            msg = f"No implementation registered for {desc.interface.__qualname__}"
            raise RuntimeError(msg)
        return desc.implementation()
