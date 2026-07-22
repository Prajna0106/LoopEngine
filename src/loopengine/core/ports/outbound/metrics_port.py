"""Outbound port — metrics collector interface.

Defines the contract for metrics and telemetry collection. Implementations
emit metrics to various backends (Prometheus, Datadog, stdout, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MetricPoint:
    """A single recorded metric data point."""

    name: str
    value: float
    metric_type: str
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: float = 0.0


class MetricsCollector(ABC):
    """Contract for metrics collection.

    Follows ISP: only metric emission. Aggregation, dashboarding, and
    alerting are external concerns.
    """

    @abstractmethod
    def increment(
        self,
        name: str,
        *,
        value: float = 1.0,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter by *value*."""

    @abstractmethod
    def gauge(
        self,
        name: str,
        value: float,
        *,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge to *value*."""

    @abstractmethod
    def timing(
        self,
        name: str,
        duration_ms: float,
        *,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Record a timing measurement in milliseconds."""

    @abstractmethod
    def histogram(
        self,
        name: str,
        value: float,
        *,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Record a value in a histogram distribution."""

    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered metrics to the backend."""

    @abstractmethod
    def get_metrics(self) -> list[MetricPoint]:
        """Return all recorded metrics (for testing/introspection)."""

    @abstractmethod
    def reset(self) -> None:
        """Clear all recorded metrics."""
