"""In-memory stub for the executor port."""

from __future__ import annotations

from typing import Any

from loopengine.core.ports.outbound.executor_port import ExecutionResult, Executor


class StubExecutor(Executor):
    """A stub executor that returns configurable results."""

    def __init__(
        self,
        output: str = "Task completed",
        success: bool = True,
    ) -> None:
        self._output = output
        self._success = success
        self.call_count = 0
        self.last_task: str = ""

    def execute(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        self.call_count += 1
        self.last_task = task
        return ExecutionResult(output=self._output, success=self._success)

    def can_execute(self, task_type: str) -> bool:
        return True
