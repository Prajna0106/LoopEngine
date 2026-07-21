"""Prompt adapters."""

from loopengine.adapters.outbound.prompts.file_prompt_provider import (
    FilePromptProvider,
)
from loopengine.adapters.outbound.prompts.prompt_registry import (
    InMemoryPromptRegistry,
)

__all__ = ["FilePromptProvider", "InMemoryPromptRegistry"]
