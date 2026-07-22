"""In-memory stub for the logger port."""

from __future__ import annotations

from typing import Any

from loopengine.core.ports.outbound.logger_port import Logger


class StubLogger(Logger):
    """Records all log calls for assertions."""

    def __init__(self) -> None:
        self.entries: list[tuple[str, str, dict[str, Any]]] = []
        self._bound: dict[str, Any] = {}

    def debug(self, message: str, **kwargs: Any) -> None:
        self.entries.append(("debug", message, {**self._bound, **kwargs}))

    def info(self, message: str, **kwargs: Any) -> None:
        self.entries.append(("info", message, {**self._bound, **kwargs}))

    def warning(self, message: str, **kwargs: Any) -> None:
        self.entries.append(("warning", message, {**self._bound, **kwargs}))

    def error(self, message: str, **kwargs: Any) -> None:
        self.entries.append(("error", message, {**self._bound, **kwargs}))

    def critical(self, message: str, **kwargs: Any) -> None:
        self.entries.append(("critical", message, {**self._bound, **kwargs}))

    def bind(self, **kwargs: Any) -> StubLogger:
        new = StubLogger()
        new.entries = self.entries
        new._bound = {**self._bound, **kwargs}
        return new

    def unbind(self, *keys: str) -> StubLogger:
        new = StubLogger()
        new.entries = self.entries
        new._bound = {k: v for k, v in self._bound.items() if k not in keys}
        return new

    def with_trace(self, trace_id: str, span_id: str | None = None) -> StubLogger:
        return self.bind(trace_id=trace_id, span_id=span_id or "")
