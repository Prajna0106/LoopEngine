"""CLI command — loop init."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from loopengine.adapters.inbound.cli.formatters import console_formatter as fmt

if TYPE_CHECKING:
    from loopengine.core.ports.inbound.orchestrator_port import OrchestratorPort


def init_command(
    path: Annotated[str, typer.Argument(help="Project directory")] = ".",
    *,
    orchestrator: OrchestratorPort,
    json_output: bool = False,
) -> None:
    """Initialise a LoopEngine project."""
    result = orchestrator.init(path)

    if json_output:
        from loopengine.adapters.inbound.cli.formatters import json_formatter

        json_formatter.emit(
            {
                "project_path": result.project_path,
                "config_path": result.config_path,
            }
        )
    else:
        fmt.success(f"Project initialised at {result.project_path}")
        fmt.info(f"Config written to {result.config_path}")
