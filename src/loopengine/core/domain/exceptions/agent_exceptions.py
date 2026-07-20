"""Agent-related exceptions."""

from __future__ import annotations

from loopengine.core.domain.exceptions.base import LoopEngineError


class AgentError(LoopEngineError):
    """Base for agent errors."""

    def __init__(self, message: str = "", *, agent: str = "") -> None:
        super().__init__(message, code="AGENT_ERROR")
        self.agent = agent


class AgentTimeoutError(AgentError):
    """Agent did not respond in time."""

    def __init__(self, agent: str, timeout: float) -> None:
        super().__init__(f"Agent {agent!r} timed out after {timeout}s", agent=agent)
        self.code = "AGENT_TIMEOUT"
        self.timeout = timeout


class AgentRefusedError(AgentError):
    """Agent refused the request."""

    def __init__(self, agent: str, reason: str = "") -> None:
        msg = f"Agent {agent!r} refused"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, agent=agent)
        self.code = "AGENT_REFUSED"
        self.reason = reason
