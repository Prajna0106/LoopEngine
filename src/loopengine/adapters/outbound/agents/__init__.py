"""Agent adapters — CLI-based AI agent wrappers."""

from loopengine.adapters.outbound.agents.base_agent_adapter import (
    BaseAgentAdapter,
    ProcessConfig,
)
from loopengine.adapters.outbound.agents.claude_adapter import ClaudeAdapter
from loopengine.adapters.outbound.agents.codex_adapter import CodexAdapter
from loopengine.adapters.outbound.agents.generic_cli_adapter import GenericCLIAdapter
from loopengine.adapters.outbound.agents.opencode_adapter import OpenCodeAdapter

__all__ = [
    "BaseAgentAdapter",
    "ClaudeAdapter",
    "CodexAdapter",
    "GenericCLIAdapter",
    "OpenCodeAdapter",
    "ProcessConfig",
]
