"""OpenCode agent adapter — wraps the ``opencode`` CLI.

Invokes ``opencode run --non-interactive <prompt>``.
"""

from __future__ import annotations

from typing import Any

from loopengine.adapters.outbound.agents.base_agent_adapter import (
    BaseAgentAdapter,
    ProcessConfig,
)


class OpenCodeAdapter(BaseAgentAdapter):
    """Adapter for the OpenCode CLI (``opencode``).

    Usage::

        agent = OpenCodeAdapter()
        if agent.is_available():
            resp = agent.invoke("Add type hints to this module")
    """

    _NAME = "opencode"

    def __init__(
        self,
        *,
        model: str = "",
        config: ProcessConfig | None = None,
    ) -> None:
        super().__init__(model=model or "default", config=config)

    @property
    def name(self) -> str:
        return self._NAME

    @property
    def command(self) -> list[str]:
        return ["opencode", "run", "--non-interactive"]

    def build_args(
        self,
        prompt: str,
        *,
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> list[str]:
        args = [*self.command]
        if self._model and self._model != "default":
            args.extend(["--model", self._model])
        args.append(prompt)
        return args
