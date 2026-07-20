"""CLI command — loop review."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from loopengine.adapters.inbound.cli.formatters import console_formatter as fmt

if TYPE_CHECKING:
    from loopengine.core.ports.inbound.orchestrator_port import OrchestratorPort


def review_command(
    workflow_id: Annotated[str, typer.Argument(help="Workflow ID to review")],
    *,
    orchestrator: OrchestratorPort,
    json_output: bool = False,
) -> None:
    """Review results of a completed workflow."""
    result = orchestrator.review(workflow_id)

    if json_output:
        from loopengine.adapters.inbound.cli.formatters import json_formatter

        json_formatter.emit(
            {
                "workflow_id": result.workflow_id,
                "verdict": result.verdict,
                "issues": result.issues,
                "summary": result.summary,
            }
        )
    else:
        fmt.heading(f"Review — {result.workflow_id}")
        verdict_style = "green" if result.verdict == "converged" else "yellow"
        fmt.info(f"Verdict: [{verdict_style}]{result.verdict}[/]")
        if result.issues:
            fmt.info("Issues:")
            for issue in result.issues:
                fmt.error(f"  - {issue}")
        fmt.panel("Summary", result.summary)
