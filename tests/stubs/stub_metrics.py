"""In-memory stub for the metrics collector port."""

from __future__ import annotations

from loopengine.core.ports.outbound.metrics_port import MetricPoint, MetricsCollector


class StubMetrics(MetricsCollector):
    """Records all metric calls for assertions."""

    def __init__(self) -> None:
        self._metrics: list[MetricPoint] = []

    def increment(
        self, name: str, *, value: float = 1.0, tags: dict[str, str] | None = None
    ) -> None:
        self._metrics.append(
            MetricPoint(name=name, value=value, metric_type="counter", tags=tags or {})
        )

    def gauge(self, name: str, value: float, *, tags: dict[str, str] | None = None) -> None:
        self._metrics.append(
            MetricPoint(name=name, value=value, metric_type="gauge", tags=tags or {})
        )

    def timing(self, name: str, duration_ms: float, *, tags: dict[str, str] | None = None) -> None:
        self._metrics.append(
            MetricPoint(name=name, value=duration_ms, metric_type="timing", tags=tags or {})
        )

    def histogram(self, name: str, value: float, *, tags: dict[str, str] | None = None) -> None:
        self._metrics.append(
            MetricPoint(name=name, value=value, metric_type="histogram", tags=tags or {})
        )

    def flush(self) -> None:
        pass

    def get_metrics(self) -> list[MetricPoint]:
        return list(self._metrics)

    def reset(self) -> None:
        self._metrics.clear()
