"""CLI command — loop doctor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loopengine.adapters.inbound.cli.formatters import console_formatter as fmt

if TYPE_CHECKING:
    from loopengine.core.ports.inbound.orchestrator_port import OrchestratorPort


def doctor_command(
    *,
    orchestrator: OrchestratorPort,
    json_output: bool = False,
) -> None:
    """Run health checks on the environment."""
    result = orchestrator.doctor()

    if json_output:
        from loopengine.adapters.inbound.cli.formatters import json_formatter

        json_formatter.emit(
            {"checks": [{"name": c.name, "ok": c.ok, "detail": c.detail} for c in result.checks]}
        )
    else:
        checks = [{"name": c.name, "ok": c.ok, "detail": c.detail} for c in result.checks]
        fmt.check_table(checks)

        failed = [c for c in result.checks if not c.ok]
        if failed:
            fmt.error(f"{len(failed)} check(s) failed")
        else:
            fmt.success("All checks passed")
