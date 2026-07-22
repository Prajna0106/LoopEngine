"""Outbound port — logger interface.

Defines the contract for structured logging. Implementations wrap
logging backends (structlog, stdlib, external services) behind this
uniform interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LogContext:
    """Bound context fields attached to a logger."""

    fields: dict[str, Any] = field(default_factory=dict)


class Logger(ABC):
    """Contract for structured loggers.

    Follows ISP: only log emission. Log formatting, transport, and
    sampling are implementation concerns.
    """

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log at DEBUG level."""

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log at INFO level."""

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log at WARNING level."""

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """Log at ERROR level."""

    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log at CRITICAL level."""

    @abstractmethod
    def bind(self, **kwargs: Any) -> Logger:
        """Return a new logger with bound context fields.

        The returned logger should include *kwargs* in every subsequent
        log entry without repeating them in each call.
        """

    @abstractmethod
    def unbind(self, *keys: str) -> Logger:
        """Return a new logger with the specified keys removed."""

    @abstractmethod
    def with_trace(self, trace_id: str, span_id: str | None = None) -> Logger:
        """Return a new logger with trace context bound."""


class Tracer(ABC):
    """Contract for distributed tracing.

    Manages spans representing units of work.
    """

    @abstractmethod
    def start_span(self, name: str, **attributes: Any) -> Span:
        """Start a new span and return it."""


class Span(ABC):
    """Contract for a single trace span."""

    @abstractmethod
    def finish(self) -> None:
        """Finish the span and record its duration."""

    @abstractmethod
    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""

    @abstractmethod
    def add_event(self, name: str, **attributes: Any) -> None:
        """Add a timed event to the span."""

    @property
    @abstractmethod
    def trace_id(self) -> str:
        """Return the trace ID for this span."""

    @property
    @abstractmethod
    def span_id(self) -> str:
        """Return the span ID."""


class ErrorReporter(ABC):
    """Contract for structured error reporting.

    Captures exception context, stack traces, and breadcrumbs.
    """

    @abstractmethod
    def capture_exception(
        self,
        exc: BaseException,
        *,
        level: str = "error",
        tags: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> str:
        """Report an exception. Returns an error ID."""

    @abstractmethod
    def capture_message(
        self,
        message: str,
        *,
        level: str = "info",
        tags: dict[str, str] | None = None,
    ) -> str:
        """Report a plain message. Returns an error ID."""

    @abstractmethod
    def add_breadcrumb(self, message: str, **kwargs: Any) -> None:
        """Add a breadcrumb to the current error context."""
