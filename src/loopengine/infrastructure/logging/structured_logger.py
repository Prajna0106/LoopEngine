"""Structured logging adapter.

Wraps structlog with Rich console rendering and JSON output.
Supports tracing via bound context fields.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog

from loopengine.core.ports.outbound.logger_port import (
    ErrorReporter,
    Logger,
    Span,
    Tracer,
)


class StructuredLogger(Logger):
    """structlog-backed structured logger with Rich/JSON rendering."""

    def __init__(self, name: str = "loopengine") -> None:
        self._logger = structlog.get_logger(name)
        self._bound_fields: dict[str, Any] = {}

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log("debug", message, kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log("info", message, kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log("warning", message, kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log("error", message, kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._log("critical", message, kwargs)

    def bind(self, **kwargs: Any) -> StructuredLogger:
        new = StructuredLogger.__new__(StructuredLogger)
        new._logger = self._logger.bind(**kwargs)
        new._bound_fields = {**self._bound_fields, **kwargs}
        return new

    def unbind(self, *keys: str) -> StructuredLogger:
        new = StructuredLogger.__new__(StructuredLogger)
        new._logger = self._logger.unbind(*keys)
        new._bound_fields = {k: v for k, v in self._bound_fields.items() if k not in keys}
        return new

    def with_trace(self, trace_id: str, span_id: str | None = None) -> StructuredLogger:
        return self.bind(trace_id=trace_id, span_id=span_id or _short_id())

    def _log(self, level: str, message: str, kwargs: dict[str, Any]) -> None:
        log_fn = getattr(self._logger, level)
        log_fn(message, **kwargs)


class StructuredTracer(Tracer):
    """In-memory tracer that creates LocalSpan instances."""

    def start_span(self, name: str, **attributes: Any) -> LocalSpan:
        return LocalSpan(name=name, attributes=attributes)


class LocalSpan(Span):
    """A single trace span that records timing."""

    def __init__(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self._name = name
        self._trace_id = _trace_id()
        self._span_id = _short_id()
        self._start_time = time.monotonic()
        self._end_time: float | None = None
        self._attributes: dict[str, Any] = dict(attributes or {})
        self._events: list[dict[str, Any]] = []
        self._finished = False

    def finish(self) -> None:
        if not self._finished:
            self._end_time = time.monotonic()
            self._finished = True

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def add_event(self, name: str, **attributes: Any) -> None:
        self._events.append(
            {
                "name": name,
                "timestamp": time.monotonic(),
                **attributes,
            }
        )

    @property
    def trace_id(self) -> str:
        return self._trace_id

    @property
    def span_id(self) -> str:
        return self._span_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def duration_ms(self) -> float:
        if self._end_time is None:
            return (time.monotonic() - self._start_time) * 1000
        return (self._end_time - self._start_time) * 1000

    @property
    def attributes(self) -> dict[str, Any]:
        return dict(self._attributes)

    @property
    def events(self) -> list[dict[str, Any]]:
        return list(self._events)


class InMemoryErrorReporter(ErrorReporter):
    """In-memory error reporter for testing and development."""

    def __init__(self) -> None:
        self._errors: list[dict[str, Any]] = []
        self._breadcrumbs: list[dict[str, Any]] = []

    def capture_exception(
        self,
        exc: BaseException,
        *,
        level: str = "error",
        tags: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> str:
        error_id = _error_id()
        self._errors.append(
            {
                "id": error_id,
                "type": "exception",
                "level": level,
                "exception_type": type(exc).__name__,
                "message": str(exc),
                "tags": tags or {},
                "extra": extra or {},
                "breadcrumbs": list(self._breadcrumbs),
            }
        )
        return error_id

    def capture_message(
        self,
        message: str,
        *,
        level: str = "info",
        tags: dict[str, str] | None = None,
    ) -> str:
        error_id = _error_id()
        self._errors.append(
            {
                "id": error_id,
                "type": "message",
                "level": level,
                "message": message,
                "tags": tags or {},
            }
        )
        return error_id

    def add_breadcrumb(self, message: str, **kwargs: Any) -> None:
        self._breadcrumbs.append({"message": message, **kwargs})

    @property
    def errors(self) -> list[dict[str, Any]]:
        return list(self._errors)

    @property
    def breadcrumbs(self) -> list[dict[str, Any]]:
        return list(self._breadcrumbs)

    def clear(self) -> None:
        self._errors.clear()
        self._breadcrumbs.clear()


def _trace_id() -> str:
    return uuid.uuid4().hex[:16]


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


def _error_id() -> str:
    return uuid.uuid4().hex[:12]


def setup_logging(level: str = "INFO", *, json_format: bool = False) -> None:
    """Configure structlog + stdlib logging."""
    import logging
    import sys

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
