"""Base LoopEngine exception."""

from __future__ import annotations


class LoopEngineError(Exception):
    """Base exception for all LoopEngine errors."""

    def __init__(self, message: str = "", *, code: str = "UNKNOWN") -> None:
        super().__init__(message)
        self.code = code
