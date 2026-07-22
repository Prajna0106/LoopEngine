"""Codex agent adapter — wraps the ``codex`` CLI.

Invokes ``codex --quiet <prompt>`` in non-interactive mode.
"""

from __future__ import annotations

from typing import Any

from loopengine.adapters.outbound.agents.base_agent_adapter import (
    BaseAgentAdapter,
    ProcessConfig,
)


class CodexAdapter(BaseAgentAdapter):
    """Adapter for the OpenAI Codex CLI (``codex``).

    Usage::

        agent = CodexAdapter()
        if agent.is_available():
            resp = agent.invoke("Refactor this function")
    """

    _NAME = "codex"

    def __init__(
        self,
        *,
        model: str = "o4-mini",
        config: ProcessConfig | None = None,
    ) -> None:
        super().__init__(model=model, config=config)

    @property
    def name(self) -> str:
        return self._NAME

    @property
    def command(self) -> list[str]:
        return ["codex", "--quiet"]

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
