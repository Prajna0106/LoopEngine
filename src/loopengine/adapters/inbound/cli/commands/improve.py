"""CLI command — loop improve."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from loopengine.adapters.inbound.cli.formatters import console_formatter as fmt

if TYPE_CHECKING:
    from loopengine.core.ports.inbound.orchestrator_port import OrchestratorPort


def improve_command(
    workflow_id: Annotated[str, typer.Argument(help="Workflow ID to improve")],
    *,
    orchestrator: OrchestratorPort,
    json_output: bool = False,
) -> None:
    """Trigger an improvement iteration."""
    result = orchestrator.improve(workflow_id)

    if json_output:
        from loopengine.adapters.inbound.cli.formatters import json_formatter

        json_formatter.emit(
            {
                "workflow_id": result.workflow_id,
                "iteration": result.iteration,
                "changes": result.changes,
                "summary": result.summary,
            }
        )
    else:
        fmt.heading(f"Iteration {result.iteration} — {result.workflow_id}")
        if result.changes:
            for change in result.changes:
                fmt.info(f"  - {change}")
        fmt.panel("Summary", result.summary)
