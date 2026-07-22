"""Tests for InMemoryMetrics and timed context manager."""

from __future__ import annotations

import time

from loopengine.infrastructure.telemetry.metrics import InMemoryMetrics, timed


class TestInMemoryMetrics:
    def test_increment(self) -> None:
        m = InMemoryMetrics()
        m.increment("requests")
        m.increment("requests", value=3)
        assert m.get_counter("requests") == 4

    def test_gauge(self) -> None:
        m = InMemoryMetrics()
        m.gauge("connections", 5.0)
        m.gauge("connections", 8.0)
        assert m.get_latest_gauge("connections") == 8.0

    def test_timing(self) -> None:
        m = InMemoryMetrics()
        m.timing("latency", 42.5)
        m.timing("latency", 100.0)
        assert m.get_timings("latency") == [42.5, 100.0]

    def test_histogram(self) -> None:
        m = InMemoryMetrics()
        m.histogram("response_size", 1024.0)
        metrics = m.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].metric_type == "histogram"
        assert metrics[0].value == 1024.0

    def test_flush(self) -> None:
        m = InMemoryMetrics()
        m.increment("x")
        m.flush()
        assert len(m.get_metrics()) == 1

    def test_reset(self) -> None:
        m = InMemoryMetrics()
        m.increment("a")
        m.gauge("b", 1.0)
        m.reset()
        assert m.get_metrics() == []

    def test_tags(self) -> None:
        m = InMemoryMetrics()
        m.increment("req", tags={"method": "GET"})
        metric = m.get_metrics()[0]
        assert metric.tags["method"] == "GET"

    def test_get_counter_nonexistent(self) -> None:
        m = InMemoryMetrics()
        assert m.get_counter("missing") == 0

    def test_get_latest_gauge_nonexistent(self) -> None:
        m = InMemoryMetrics()
        assert m.get_latest_gauge("missing") is None

    def test_get_timings_nonexistent(self) -> None:
        m = InMemoryMetrics()
        assert m.get_timings("missing") == []

    def test_metric_timestamp(self) -> None:
        m = InMemoryMetrics()
        before = time.time()
        m.increment("x")
        after = time.time()
        ts = m.get_metrics()[0].timestamp
        assert before <= ts <= after

    def test_multiple_metric_types(self) -> None:
        m = InMemoryMetrics()
        m.increment("counter1")
        m.gauge("gauge1", 10.0)
        m.timing("timing1", 5.0)
        m.histogram("hist1", 100.0)
        assert len(m.get_metrics()) == 4
        types = {m.metric_type for m in m.get_metrics()}
        assert types == {"counter", "gauge", "timing", "histogram"}


class TestTimed:
    def test_records_timing(self) -> None:
        m = InMemoryMetrics()
        with timed(m, "op"):
            time.sleep(0.01)
        timings = m.get_timings("op")
        assert len(timings) == 1
        assert timings[0] > 5

    def test_records_on_exception(self) -> None:
        m = InMemoryMetrics()
        try:
            with timed(m, "op"):
                raise ValueError("boom")
        except ValueError:
            pass
        timings = m.get_timings("op")
        assert len(timings) == 1

    def test_with_tags(self) -> None:
        m = InMemoryMetrics()
        with timed(m, "op", tags={"service": "auth"}):
            pass
        assert m.get_metrics()[0].tags["service"] == "auth"

    def test_multiple_timed(self) -> None:
        m = InMemoryMetrics()
        with timed(m, "a"):
            time.sleep(0.005)
        with timed(m, "b"):
            time.sleep(0.005)
        assert len(m.get_timings("a")) == 1
        assert len(m.get_timings("b")) == 1


class TestMetricPoint:
    def test_creation(self) -> None:
        from loopengine.core.ports.outbound.metrics_port import MetricPoint

        mp = MetricPoint(name="x", value=1.0, metric_type="counter")
        assert mp.name == "x"
        assert mp.tags == {}

    def test_with_tags(self) -> None:
        from loopengine.core.ports.outbound.metrics_port import MetricPoint

        mp = MetricPoint(
            name="x",
            value=1.0,
            metric_type="gauge",
            tags={"a": "b"},
            timestamp=123.0,
        )
        assert mp.tags["a"] == "b"
        assert mp.timestamp == 123.0
