"""CLI command — loop run."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from loopengine.adapters.inbound.cli.formatters import console_formatter as fmt

if TYPE_CHECKING:
    from loopengine.core.ports.inbound.orchestrator_port import OrchestratorPort


def run_command(
    goal: Annotated[str, typer.Argument(help="Workflow goal")] = "",
    config: Annotated[str | None, typer.Option("--config", "-c", help="Config file path")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan only, do not execute")] = False,
    *,
    orchestrator: OrchestratorPort,
    json_output: bool = False,
) -> None:
    """Execute a workflow."""
    effective_goal = goal if goal else None
    result = orchestrator.run(config, dry_run=dry_run, goal=effective_goal)

    if json_output:
        from loopengine.adapters.inbound.cli.formatters import json_formatter

        json_formatter.emit(
            {
                "workflow_id": result.workflow_id,
                "status": result.status,
                "iterations": result.iterations,
                "summary": result.summary,
            }
        )
    else:
        fmt.workflow_summary(
            {
                "workflow_id": result.workflow_id,
                "status": result.status,
                "iterations": result.iterations,
                "summary": result.summary,
            }
        )
