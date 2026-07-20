"""CLI command — loop plan."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from loopengine.adapters.inbound.cli.formatters import console_formatter as fmt

if TYPE_CHECKING:
    from loopengine.core.ports.inbound.orchestrator_port import OrchestratorPort


def plan_command(
    config: Annotated[str | None, typer.Option("--config", "-c", help="Config file path")] = None,
    *,
    orchestrator: OrchestratorPort,
    json_output: bool = False,
) -> None:
    """Plan a workflow without executing it."""
    result = orchestrator.plan(config)

    if json_output:
        from loopengine.adapters.inbound.cli.formatters import json_formatter

        json_formatter.emit(
            {
                "workflow_id": result.workflow_id,
                "phases": result.phases,
                "summary": result.summary,
            }
        )
    else:
        fmt.heading("Workflow Plan")
        fmt.info(f"ID:     {result.workflow_id}")
        fmt.info(f"Phases: {', '.join(result.phases)}")
        fmt.panel("Summary", result.summary)
