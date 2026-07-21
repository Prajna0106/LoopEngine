"""Prompt-related exceptions."""

from __future__ import annotations

from loopengine.core.domain.exceptions.base import LoopEngineError


class PromptError(LoopEngineError):
    """Base for prompt errors."""

    def __init__(self, message: str = "", *, prompt: str = "") -> None:
        super().__init__(message, code="PROMPT_ERROR")
        self.prompt = prompt


class PromptNotFoundError(PromptError):
    """Requested prompt is not registered."""

    def __init__(self, prompt: str, version: str = "") -> None:
        msg = f"Prompt not found: {prompt!r}"
        if version:
            msg += f" v{version}"
        super().__init__(msg, prompt=prompt)
        self.code = "PROMPT_NOT_FOUND"
        self.version = version


class PromptValidationError(PromptError):
    """Prompt template has invalid syntax or missing variables."""

    def __init__(self, prompt: str, errors: list[str]) -> None:
        detail = "; ".join(errors)
        super().__init__(f"Prompt {prompt!r} validation failed: {detail}", prompt=prompt)
        self.code = "PROMPT_VALIDATION_ERROR"
        self.errors = errors


class PromptLoadError(PromptError):
    """Failed to load a prompt from a provider."""

    def __init__(self, prompt: str, reason: str = "") -> None:
        msg = f"Failed to load prompt {prompt!r}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, prompt=prompt)
        self.code = "PROMPT_LOAD_ERROR"
        self.reason = reason
