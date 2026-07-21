"""Outbound port — logger interface.

Defines the contract for structured logging. Implementations wrap
logging backends (structlog, stdlib, external services) behind this
uniform interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


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
