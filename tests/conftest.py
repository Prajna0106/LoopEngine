"""Root shared test fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from loopengine.adapters.outbound.persistence.in_memory_store import (
    InMemoryExecutionHistory,
    InMemoryProjectMetaStore,
    InMemoryReflectionStore,
    InMemoryReviewStore,
    InMemoryStore,
)


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with a basic structure."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "main.py").write_text('"""Main module."""\n\nx = 1\n')
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-proj"\nversion = "0.1.0"\n')
    return tmp_path


@pytest.fixture()
def tmp_plugins_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with a sample plugin."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "my_plugin.py").write_text(
        "from loopengine.core.ports.outbound.plugin_registry_port "
        "import BasePlugin, PluginMetadata\n\n"
        "class MyPlugin(BasePlugin):\n"
        "    @property\n"
        "    def metadata(self):\n"
        '        return PluginMetadata(name="my-plugin", version="1.0.0")\n'
    )
    return plugin_dir


@pytest.fixture()
def tmp_prompts_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with sample prompts."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "plan.md").write_text(
        '---\nversion: "1.0.0"\nvariables: [goal]\ntags: [planning]\n---\n'
        "Create a plan for: {goal}"
    )
    (prompts_dir / "review.md").write_text("Review the implementation of {goal}")
    return prompts_dir


@pytest.fixture()
def memory_store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture()
def execution_history() -> InMemoryExecutionHistory:
    return InMemoryExecutionHistory()


@pytest.fixture()
def reflection_store() -> InMemoryReflectionStore:
    return InMemoryReflectionStore()


@pytest.fixture()
def review_store() -> InMemoryReviewStore:
    return InMemoryReviewStore()


@pytest.fixture()
def project_meta_store() -> InMemoryProjectMetaStore:
    return InMemoryProjectMetaStore()
