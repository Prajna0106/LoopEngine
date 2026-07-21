"""Generic CLI agent adapter — wraps any arbitrary CLI tool.

Invokes ``<command> <args...> <prompt>`` and captures stdout.
Use this for custom or experimental agent CLIs.
"""

from __future__ import annotations

from typing import Any

from loopengine.adapters.outbound.agents.base_agent_adapter import (
    BaseAgentAdapter,
    ProcessConfig,
)
from loopengine.core.ports.outbound.agent_port import AgentResponse


class GenericCLIAdapter(BaseAgentAdapter):
    """Adapter for arbitrary CLI-based agents.

    Usage::

        agent = GenericCLIAdapter(
            name="my-agent",
            command=["my-agent-cli", "--quiet"],
            model="custom-v1",
        )
        resp = agent.invoke("Do something")
    """

    def __init__(
        self,
        *,
        name: str = "generic",
        command: list[str] | None = None,
        model: str = "unknown",
        config: ProcessConfig | None = None,
    ) -> None:
        super().__init__(config=config)
        self._name = name
        self._command = command or [name]
        self._model = model

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model

    @property
    def command(self) -> list[str]:
        return self._command

    def build_args(
        self,
        prompt: str,
        *,
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[str]:
        return [*self._command, prompt]

    def parse_response(self, stdout: str, stderr: str) -> AgentResponse:
        return AgentResponse(
            content=stdout.strip(),
            model=self._model,
            metadata={"agent": self._name, "stderr": stderr.strip()},
        )
