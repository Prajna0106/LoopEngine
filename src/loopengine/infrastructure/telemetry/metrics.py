"""In-memory metrics collector adapter.

Records metrics in memory for testing and development. Supports
counters, gauges, histograms, and timing measurements.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

from loopengine.core.ports.outbound.metrics_port import MetricPoint, MetricsCollector

if TYPE_CHECKING:
    from collections.abc import Iterator


class InMemoryMetrics(MetricsCollector):
    """In-memory metrics collector for testing."""

    def __init__(self) -> None:
        self._metrics: list[MetricPoint] = []

    def increment(
        self,
        name: str,
        *,
        value: float = 1.0,
        tags: dict[str, str] | None = None,
    ) -> None:
        self._record(name, value, "counter", tags)

    def gauge(
        self,
        name: str,
        value: float,
        *,
        tags: dict[str, str] | None = None,
    ) -> None:
        self._record(name, value, "gauge", tags)

    def timing(
        self,
        name: str,
        duration_ms: float,
        *,
        tags: dict[str, str] | None = None,
    ) -> None:
        self._record(name, duration_ms, "timing", tags)

    def histogram(
        self,
        name: str,
        value: float,
        *,
        tags: dict[str, str] | None = None,
    ) -> None:
        self._record(name, value, "histogram", tags)

    def flush(self) -> None:
        pass

    def get_metrics(self) -> list[MetricPoint]:
        return list(self._metrics)

    def reset(self) -> None:
        self._metrics.clear()

    def _record(
        self,
        name: str,
        value: float,
        metric_type: str,
        tags: dict[str, str] | None,
    ) -> None:
        self._metrics.append(
            MetricPoint(
                name=name,
                value=value,
                metric_type=metric_type,
                tags=dict(tags or {}),
                timestamp=time.time(),
            )
        )

    def get_counter(self, name: str) -> float:
        """Sum all counter increments for a given name."""
        return sum(m.value for m in self._metrics if m.name == name and m.metric_type == "counter")

    def get_latest_gauge(self, name: str) -> float | None:
        """Return the latest gauge value for a given name."""
        gauges = [m for m in self._metrics if m.name == name and m.metric_type == "gauge"]
        return gauges[-1].value if gauges else None

    def get_timings(self, name: str) -> list[float]:
        """Return all timing values for a given name."""
        return [m.value for m in self._metrics if m.name == name and m.metric_type == "timing"]


@contextmanager
def timed(
    metrics: MetricsCollector,
    name: str,
    *,
    tags: dict[str, str] | None = None,
) -> Iterator[None]:
    """Context manager that records wall-clock timing for a block."""
    start = time.monotonic()
    try:
        yield
    finally:
        duration_ms = (time.monotonic() - start) * 1000
        metrics.timing(name, duration_ms, tags=tags)
