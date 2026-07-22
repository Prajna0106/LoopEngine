"""Tests for DI Container and ServiceRegistry."""

from __future__ import annotations

import abc

from loopengine.infrastructure.container.di_container import Container
from loopengine.infrastructure.container.registry import (
    RegistrationKind,
    ServiceDescriptor,
    ServiceRegistry,
)


class FakeService:
    """A concrete service for testing."""

    def __init__(self) -> None:
        self.value = 42


class AnotherService:
    """Another concrete service."""

    def __init__(self) -> None:
        self.name = "another"


class AbstractService(abc.ABC):
    """An abstract service."""

    @abc.abstractmethod
    def do(self) -> None: ...


class ConcreteService(AbstractService):
    def do(self) -> None:
        pass


def _make_fake() -> FakeService:
    return FakeService()


class TestServiceRegistry:
    """Tests for ServiceRegistry."""

    def test_register_class(self) -> None:
        reg = ServiceRegistry()
        reg.register(FakeService)
        assert reg.has(FakeService)
        desc = reg.get(FakeService)
        assert desc is not None
        assert desc.kind == RegistrationKind.CLASS
        assert desc.implementation is FakeService

    def test_register_with_implementation(self) -> None:
        reg = ServiceRegistry()
        reg.register(AbstractService, ConcreteService)
        desc = reg.get(AbstractService)
        assert desc is not None
        assert desc.implementation is ConcreteService

    def test_register_factory(self) -> None:
        reg = ServiceRegistry()
        reg.register_factory(FakeService, _make_fake)
        desc = reg.get(FakeService)
        assert desc is not None
        assert desc.kind == RegistrationKind.FACTORY

    def test_register_instance(self) -> None:
        inst = FakeService()
        reg = ServiceRegistry()
        reg.register_instance(FakeService, inst)
        desc = reg.get(FakeService)
        assert desc is not None
        assert desc.kind == RegistrationKind.INSTANCE
        assert desc.instance is inst

    def test_interfaces_property(self) -> None:
        reg = ServiceRegistry()
        reg.register(FakeService)
        reg.register(AnotherService)
        assert FakeService in reg.interfaces
        assert AnotherService in reg.interfaces

    def test_copy(self) -> None:
        reg = ServiceRegistry()
        reg.register(FakeService)
        clone = reg.copy()
        assert clone.has(FakeService)
        assert clone is not reg

    def test_clear(self) -> None:
        reg = ServiceRegistry()
        reg.register(FakeService)
        reg.clear()
        assert not reg.has(FakeService)

    def test_get_nonexistent(self) -> None:
        reg = ServiceRegistry()
        assert reg.get(FakeService) is None


class TestContainer:
    """Tests for Container."""

    def test_resolve_instance(self) -> None:
        c = Container()
        inst = FakeService()
        c.register_instance(FakeService, inst)
        assert c.resolve(FakeService) is inst

    def test_resolve_class_singleton(self) -> None:
        c = Container()
        c.register(FakeService)
        a = c.resolve(FakeService)
        b = c.resolve(FakeService)
        assert a is b  # singleton cached

    def test_resolve_class_nonsingleton(self) -> None:
        c = Container()
        c.register(FakeService, singleton=False)
        a = c.resolve(FakeService)
        b = c.resolve(FakeService)
        assert a is not b  # new instance each time

    def test_resolve_factory(self) -> None:
        c = Container()
        c.register_factory(FakeService, _make_fake)
        inst = c.resolve(FakeService)
        assert isinstance(inst, FakeService)

    def test_resolve_default(self) -> None:
        c = Container()
        sentinel = object()
        result = c.resolve(FakeService, sentinel)
        assert result is sentinel

    def test_resolve_raises_key_error(self) -> None:
        c = Container()
        try:
            c.resolve(FakeService)
            raise AssertionError("Should have raised")
        except KeyError:
            pass

    def test_has(self) -> None:
        c = Container()
        assert not c.has(FakeService)
        c.register(FakeService)
        assert c.has(FakeService)

    def test_has_cached(self) -> None:
        c = Container()
        c.cache(FakeService, FakeService())
        assert c.has(FakeService)

    def test_resolve_all(self) -> None:
        c = Container()
        c.register_instance(FakeService, FakeService())
        c.register_instance(AnotherService, AnotherService())
        results = c.resolve_all(FakeService, AnotherService)
        assert len(results) == 2
        assert isinstance(results[0], FakeService)
        assert isinstance(results[1], AnotherService)

    def test_cache_and_invalidate(self) -> None:
        c = Container()
        inst = FakeService()
        c.cache(FakeService, inst)
        assert c.invalidate(FakeService) is True
        assert c.invalidate(FakeService) is False

    def test_reset(self) -> None:
        c = Container()
        c.cache(FakeService, FakeService())
        c.reset()
        assert not c.has(FakeService)

    def test_teardown(self) -> None:
        c = Container()
        c.register(FakeService)
        c.cache(FakeService, FakeService())
        c.teardown()
        assert not c.has(FakeService)

    def test_registry_property(self) -> None:
        c = Container()
        assert isinstance(c.registry, ServiceRegistry)

    def test_wire_with_orchestrator(self) -> None:
        from loopengine.core.ports.inbound.orchestrator_port import (
            OrchestratorPort,
        )

        c = Container()
        fake_orch = object()
        c.wire(orchestrator=fake_orch)
        assert c.resolve(OrchestratorPort) is fake_orch

    def test_orchestrator_not_wired(self) -> None:
        c = Container()
        try:
            _ = c.orchestrator
            raise AssertionError("Should have raised")
        except RuntimeError:
            pass

    def test_set_orchestrator(self) -> None:
        from loopengine.core.ports.inbound.orchestrator_port import (
            OrchestratorPort,
        )

        c = Container()
        fake_orch = object()
        c.set_orchestrator(fake_orch)
        assert c.resolve(OrchestratorPort) is fake_orch

    def test_create_class_no_implementation(self) -> None:
        c = Container()
        c._registry._descriptors[FakeService] = ServiceDescriptor(
            interface=FakeService,
            kind=RegistrationKind.CLASS,
            implementation=None,
        )
        try:
            c.resolve(FakeService)
            raise AssertionError("Should have raised")
        except RuntimeError:
            pass
