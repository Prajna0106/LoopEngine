"""Outbound port — base agent invocation interface.

Defines the contract for all AI agent adapters. Each adapter wraps an
external LLM (Claude, OpenAI, Copilot, etc.) behind this uniform interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentResponse:
    """Uniform response from any agent."""

    content: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Core contract for AI agent adapters.

    Follows ISP: only agent invocation and identity. Planning, execution,
    reflection, and review are separate port interfaces.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent identifier (e.g. 'claude', 'openai')."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier (e.g. 'claude-sonnet-4-20250514')."""

    @abstractmethod
    def invoke(
        self,
        prompt: str,
        *,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> AgentResponse:
        """Send a prompt to the agent and return the response.

        Parameters
        ----------
        prompt:
            The full prompt text to send.
        context:
            Optional key-value context (file contents, prior results, etc.).
        timeout:
            Override the default timeout in seconds.

        Raises
        ------
        AgentTimeoutError
            If the agent does not respond within the timeout.
        AgentRefusedError
            If the agent refuses the request.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the agent can be reached (API key set, service up)."""
