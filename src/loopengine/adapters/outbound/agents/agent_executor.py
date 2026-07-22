"""Agent executor — wraps a BaseAgentAdapter as an Executor port.

Bridges the agent invocation interface with the execution engine's
Executor port, allowing any CLI-based agent to drive task execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from loopengine.core.ports.outbound.executor_port import ExecutionResult, Executor

if TYPE_CHECKING:
    from loopengine.adapters.outbound.agents.base_agent_adapter import BaseAgentAdapter

log = structlog.get_logger()


class AgentExecutor(Executor):
    """Adapts a BaseAgentAdapter into the Executor port.

    Each task description is sent as a prompt to the underlying agent.
    The agent's response becomes the execution result.
    """

    def __init__(self, agent: BaseAgentAdapter) -> None:
        self._agent = agent

    @property
    def agent(self) -> BaseAgentAdapter:
        return self._agent

    def execute(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        """Send the task to the agent and return the result."""
        log.debug("agent_execute", agent=self._agent.name, task=task[:80])

        try:
            response = self._agent.invoke(task, context=context, timeout=timeout)
            return ExecutionResult(
                output=response.content,
                success=True,
                artifacts=[],
                duration_ms=0.0,
                metadata={
                    "agent": self._agent.name,
                    "model": getattr(self._agent, "model", ""),
                    **response.metadata,
                },
            )
        except Exception as exc:
            log.warning("agent_execute_failed", agent=self._agent.name, error=str(exc))
            return ExecutionResult(
                output=f"Agent error: {exc}",
                success=False,
                artifacts=[],
                duration_ms=0.0,
                metadata={"agent": self._agent.name, "error": str(exc)},
            )

    def can_execute(self, task_type: str) -> bool:  # noqa: ARG002
        """Agent executor can handle any task type."""
        return True
