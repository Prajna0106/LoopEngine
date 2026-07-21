"""Service registry — stores service descriptors for lazy resolution.

The registry holds *how* to create services (class, factory callable,
or pre-built instance) without actually creating them. Resolution and
caching is handled by the Container.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeVar

T = TypeVar("T")


class RegistrationKind(StrEnum):
    """How a service should be instantiated."""

    CLASS = "class"
    FACTORY = "factory"
    INSTANCE = "instance"


@dataclass
class ServiceDescriptor:
    """Describes how to create a single service."""

    interface: type
    kind: RegistrationKind
    implementation: type | None = None
    factory: Any = None  # Callable[..., T]
    instance: Any = None
    singleton: bool = True


class ServiceRegistry:
    """Mutable registry of service descriptors.

    The registry is a plain data store — it does not create or cache
    instances. That responsibility belongs to the Container.
    """

    def __init__(self) -> None:
        self._descriptors: dict[type, ServiceDescriptor] = {}

    # ── Registration API ──────────────────────────────────────────────

    def register(
        self,
        interface: type[T],
        implementation: type[T] | None = None,
        *,
        singleton: bool = True,
    ) -> None:
        """Register a class that implements *interface*.

        If *implementation* is ``None``, *interface* itself is used as
        the concrete class (self-binding).
        """
        self._descriptors[interface] = ServiceDescriptor(
            interface=interface,
            kind=RegistrationKind.CLASS,
            implementation=implementation or interface,
            singleton=singleton,
        )

    def register_factory(
        self,
        interface: type[T],
        factory: Any,
        *,
        singleton: bool = True,
    ) -> None:
        """Register a factory callable for *interface*.

        *factory* will be called with no arguments each time the
        service is resolved (unless *singleton=True*, in which case
        it is called only once).
        """
        self._descriptors[interface] = ServiceDescriptor(
            interface=interface,
            kind=RegistrationKind.FACTORY,
            factory=factory,
            singleton=singleton,
        )

    def register_instance(
        self,
        interface: type[T],
        instance: T,
    ) -> None:
        """Register a pre-built instance for *interface*.

        The instance is always treated as a singleton.
        """
        self._descriptors[interface] = ServiceDescriptor(
            interface=interface,
            kind=RegistrationKind.INSTANCE,
            instance=instance,
            singleton=True,
        )

    # ── Query API ─────────────────────────────────────────────────────

    def has(self, interface: type) -> bool:
        """Return True if *interface* has a registered descriptor."""
        return interface in self._descriptors

    def get(self, interface: type) -> ServiceDescriptor | None:
        """Return the descriptor for *interface*, or ``None``."""
        return self._descriptors.get(interface)

    @property
    def interfaces(self) -> list[type]:
        """Return all registered interface types."""
        return list(self._descriptors.keys())

    def copy(self) -> ServiceRegistry:
        """Return a shallow copy of this registry."""
        clone = ServiceRegistry()
        clone._descriptors = dict(self._descriptors)
        return clone

    def clear(self) -> None:
        """Remove all registrations."""
        self._descriptors.clear()
