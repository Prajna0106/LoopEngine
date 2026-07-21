"""Dependency injection container and service registry."""

from loopengine.infrastructure.container.di_container import Container
from loopengine.infrastructure.container.registry import (
    RegistrationKind,
    ServiceDescriptor,
    ServiceRegistry,
)

__all__ = [
    "Container",
    "RegistrationKind",
    "ServiceDescriptor",
    "ServiceRegistry",
]
