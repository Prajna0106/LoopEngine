"""Tests for StructuredLogger, StructuredTracer, LocalSpan, InMemoryErrorReporter."""

from __future__ import annotations

from loopengine.infrastructure.logging.structured_logger import (
    InMemoryErrorReporter,
    LocalSpan,
    StructuredLogger,
    StructuredTracer,
)


class TestStructuredLogger:
    def test_debug(self) -> None:
        logger = StructuredLogger("test")
        logger.debug("debug msg", key="val")
        assert True

    def test_info(self) -> None:
        logger = StructuredLogger("test")
        logger.info("info msg")
        assert True

    def test_warning(self) -> None:
        logger = StructuredLogger("test")
        logger.warning("warn msg")
        assert True

    def test_error(self) -> None:
        logger = StructuredLogger("test")
        logger.error("error msg")
        assert True

    def test_critical(self) -> None:
        logger = StructuredLogger("test")
        logger.critical("critical msg")
        assert True

    def test_bind(self) -> None:
        logger = StructuredLogger("test")
        bound = logger.bind(workflow_id="w1")
        assert bound._bound_fields["workflow_id"] == "w1"
        bound.info("test")
        assert True

    def test_unbind(self) -> None:
        logger = StructuredLogger("test").bind(a="1", b="2")
        unbound = logger.unbind("a")
        assert "a" not in unbound._bound_fields
        assert "b" in unbound._bound_fields

    def test_with_trace(self) -> None:
        logger = StructuredLogger("test")
        traced = logger.with_trace("trace123", "span456")
        assert traced._bound_fields["trace_id"] == "trace123"
        assert traced._bound_fields["span_id"] == "span456"

    def test_with_trace_auto_span(self) -> None:
        logger = StructuredLogger("test")
        traced = logger.with_trace("trace123")
        assert traced._bound_fields["trace_id"] == "trace123"
        assert "span_id" in traced._bound_fields

    def test_chained_bind(self) -> None:
        logger = StructuredLogger("test")
        result = logger.bind(a="1").bind(b="2")
        assert result._bound_fields == {"a": "1", "b": "2"}


class TestStructuredTracer:
    def test_start_span(self) -> None:
        tracer = StructuredTracer()
        span = tracer.start_span("op1")
        assert span.name == "op1"
        assert span.trace_id
        assert span.span_id

    def test_start_span_with_attributes(self) -> None:
        tracer = StructuredTracer()
        span = tracer.start_span("op1", service="auth", version="1.0")
        assert span.attributes["service"] == "auth"
        assert span.attributes["version"] == "1.0"


class TestLocalSpan:
    def test_finish(self) -> None:
        span = LocalSpan("op1")
        assert not span._finished
        span.finish()
        assert span._finished
        assert span.duration_ms >= 0

    def test_duration_before_finish(self) -> None:
        span = LocalSpan("op1")
        d = span.duration_ms
        assert d >= 0

    def test_set_attribute(self) -> None:
        span = LocalSpan("op1")
        span.set_attribute("key", "value")
        assert span.attributes["key"] == "value"

    def test_add_event(self) -> None:
        span = LocalSpan("op1")
        span.add_event("event1", detail="test")
        assert len(span.events) == 1
        assert span.events[0]["name"] == "event1"
        assert span.events[0]["detail"] == "test"

    def test_unique_ids(self) -> None:
        s1 = LocalSpan("a")
        s2 = LocalSpan("b")
        assert s1.trace_id != s2.trace_id or s1.span_id != s2.span_id

    def test_multiple_events(self) -> None:
        span = LocalSpan("op")
        span.add_event("start")
        span.add_event("end")
        assert len(span.events) == 2

    def test_name(self) -> None:
        span = LocalSpan("my-op")
        assert span.name == "my-op"


class TestInMemoryErrorReporter:
    def test_capture_exception(self) -> None:
        reporter = InMemoryErrorReporter()
        try:
            raise ValueError("bad value")
        except ValueError as exc:
            error_id = reporter.capture_exception(exc)
        assert error_id
        assert len(reporter.errors) == 1
        assert reporter.errors[0]["exception_type"] == "ValueError"
        assert reporter.errors[0]["message"] == "bad value"

    def test_capture_exception_with_tags(self) -> None:
        reporter = InMemoryErrorReporter()
        try:
            raise RuntimeError("fail")
        except RuntimeError as exc:
            reporter.capture_exception(exc, tags={"env": "test"}, extra={"attempt": 3})
        assert reporter.errors[0]["tags"]["env"] == "test"
        assert reporter.errors[0]["extra"]["attempt"] == 3

    def test_capture_message(self) -> None:
        reporter = InMemoryErrorReporter()
        error_id = reporter.capture_message("something happened")
        assert error_id
        assert reporter.errors[0]["message"] == "something happened"
        assert reporter.errors[0]["type"] == "message"

    def test_capture_message_with_tags(self) -> None:
        reporter = InMemoryErrorReporter()
        reporter.capture_message("msg", level="warning", tags={"src": "test"})
        assert reporter.errors[0]["level"] == "warning"
        assert reporter.errors[0]["tags"]["src"] == "test"

    def test_add_breadcrumb(self) -> None:
        reporter = InMemoryErrorReporter()
        reporter.add_breadcrumb("step1", category="auth")
        reporter.add_breadcrumb("step2")
        assert len(reporter.breadcrumbs) == 2
        assert reporter.breadcrumbs[0]["message"] == "step1"
        assert reporter.breadcrumbs[0]["category"] == "auth"

    def test_breadcrumbs_attached_to_exception(self) -> None:
        reporter = InMemoryErrorReporter()
        reporter.add_breadcrumb("step1")
        reporter.add_breadcrumb("step2")
        try:
            raise ValueError("oops")
        except ValueError as exc:
            reporter.capture_exception(exc)
        assert len(reporter.errors[0]["breadcrumbs"]) == 2

    def test_clear(self) -> None:
        reporter = InMemoryErrorReporter()
        reporter.capture_message("msg")
        reporter.add_breadcrumb("bc")
        reporter.clear()
        assert reporter.errors == []
        assert reporter.breadcrumbs == []

    def test_multiple_exceptions(self) -> None:
        reporter = InMemoryErrorReporter()
        for i in range(5):
            try:
                raise ValueError(f"err{i}")
            except ValueError as exc:
                reporter.capture_exception(exc)
        assert len(reporter.errors) == 5
