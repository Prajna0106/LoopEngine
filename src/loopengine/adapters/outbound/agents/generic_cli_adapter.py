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
        super().__init__(model=model, config=config)
        self._name = name
        self._command = command or [name]

    @property
    def name(self) -> str:
        return self._name

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
