"""Claude agent adapter — wraps the ``claude`` CLI.

Invokes ``claude -p <prompt>`` in non-interactive (print) mode.
"""

from __future__ import annotations

from typing import Any

from loopengine.adapters.outbound.agents.base_agent_adapter import (
    BaseAgentAdapter,
    ProcessConfig,
)


class ClaudeAdapter(BaseAgentAdapter):
    """Adapter for the Anthropic Claude CLI (``claude``).

    Usage::

        agent = ClaudeAdapter()
        if agent.is_available():
            resp = agent.invoke("Write a hello-world function")
    """

    _NAME = "claude"

    def __init__(
        self,
        *,
        model: str = "claude-sonnet-5-20260514",
        config: ProcessConfig | None = None,
    ) -> None:
        super().__init__(model=model, config=config)

    @property
    def name(self) -> str:
        return self._NAME

    @property
    def command(self) -> list[str]:
        return ["claude", "-p"]

    def build_args(
        self,
        prompt: str,
        *,
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[str]:
        args = [*self.command]
        args.extend(["--model", self._model])
        args.append(prompt)
        return args
