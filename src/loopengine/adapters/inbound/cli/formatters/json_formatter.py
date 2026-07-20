"""JSON output formatter — machine-readable output."""

from __future__ import annotations

import json
import sys
from typing import Any


def emit(data: dict[str, Any]) -> None:
    """Write a JSON object to stdout."""
    print(json.dumps(data, indent=2), file=sys.stdout)


def emit_error(code: str, message: str) -> None:
    """Write a JSON error object to stderr."""
    print(json.dumps({"error": code, "message": message}, indent=2), file=sys.stderr)
