"""In-memory stub agent adapter for testing."""

from __future__ import annotations

from typing import Any

from loopengine.core.ports.outbound.agent_port import AgentResponse, BaseAgent


class StubAgent(BaseAgent):
    """A stub agent that returns configurable responses."""

    def __init__(
        self,
        content: str = "Task completed successfully",
        model: str = "stub-model",
    ) -> None:
        self._content = content
        self._model = model
        self.call_count = 0
        self.last_prompt: str = ""
        self.last_context: dict[str, Any] | None = None

    @property
    def name(self) -> str:
        return "stub-agent"

    @property
    def model(self) -> str:
        return self._model

    def invoke(
        self,
        prompt: str,
        *,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> AgentResponse:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_context = context
        return AgentResponse(content=self._content, model=self._model)

    def is_available(self) -> bool:
        return True
