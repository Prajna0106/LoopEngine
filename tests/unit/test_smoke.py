"""Smoke test — confirms the project scaffolding imports cleanly."""

from __future__ import annotations


def test_package_imports() -> None:
    """Root package is importable and has a version."""
    import loopengine

    assert hasattr(loopengine, "__version__")
    assert loopengine.__version__ == "0.1.0"
