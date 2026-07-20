"""CLI application entry point (Typer + Rich)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

if TYPE_CHECKING:
    from collections.abc import Callable

import structlog
import typer

from loopengine.adapters.inbound.cli.formatters import console_formatter as fmt
from loopengine.core.domain.exceptions.base import LoopEngineError
from loopengine.infrastructure.config.settings import Settings
from loopengine.infrastructure.container.di_container import Container
from loopengine.infrastructure.logging.structured_logger import setup_logging

log = structlog.get_logger()

app = typer.Typer(
    name="loop",
    help="LoopEngine — engineering orchestration for AI coding agents.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)

# ── Shared state ────────────────────────────────────────────────────────

_container: Container | None = None


def _get_container() -> Container:
    """Retrieve the DI container (set during bootstrap)."""
    if _container is None:
        raise RuntimeError("Container not initialised")
    return _container


def _json_flag(ctx: typer.Context) -> bool:
    """Check if --json was passed on the parent group."""
    return ctx.obj.get("json_output", False) if ctx.obj else False


# ── Callback (group-level options) ─────────────────────────────────────


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    json_output: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    log_level: Annotated[str, typer.Option("--log-level", "-l", help="Log level")] = "INFO",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable debug logging")] = False,
) -> None:
    """LoopEngine CLI."""
    level = "DEBUG" if verbose else log_level
    setup_logging(level)

    ctx.ensure_object(dict)
    ctx.obj["json_output"] = json_output
    ctx.obj["log_level"] = level

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


# ── Commands ────────────────────────────────────────────────────────────


@app.command()
def init(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Project directory")] = ".",
) -> None:
    """Initialise a LoopEngine project."""
    from loopengine.adapters.inbound.cli.commands.init_cmd import init_command

    json = _json_flag(ctx)
    _run_command(
        ctx,
        lambda orch: init_command(
            path,
            orchestrator=orch,
            json_output=json,
        ),
    )


@app.command()
def doctor(ctx: typer.Context) -> None:
    """Run environment health checks."""
    from loopengine.adapters.inbound.cli.commands.doctor import doctor_command

    json = _json_flag(ctx)
    _run_command(
        ctx,
        lambda orch: doctor_command(
            orchestrator=orch,
            json_output=json,
        ),
    )


@app.command()
def plan(
    ctx: typer.Context,
    config: Annotated[str | None, typer.Option("--config", "-c", help="Config file")] = None,
) -> None:
    """Plan a workflow without executing."""
    from loopengine.adapters.inbound.cli.commands.plan import plan_command

    json = _json_flag(ctx)
    _run_command(
        ctx,
        lambda orch: plan_command(
            config,
            orchestrator=orch,
            json_output=json,
        ),
    )


@app.command(name="run")
def run_cmd(
    ctx: typer.Context,
    config: Annotated[str | None, typer.Option("--config", "-c", help="Config file")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan only")] = False,
) -> None:
    """Execute a workflow."""
    from loopengine.adapters.inbound.cli.commands.run import run_command

    json = _json_flag(ctx)
    _run_command(
        ctx,
        lambda orch: run_command(
            config,
            dry_run=dry_run,
            orchestrator=orch,
            json_output=json,
        ),
    )


@app.command()
def review(
    ctx: typer.Context,
    workflow_id: Annotated[str, typer.Argument(help="Workflow ID")],
) -> None:
    """Review a completed workflow."""
    from loopengine.adapters.inbound.cli.commands.review import review_command

    json = _json_flag(ctx)
    _run_command(
        ctx,
        lambda orch: review_command(
            workflow_id,
            orchestrator=orch,
            json_output=json,
        ),
    )


@app.command()
def improve(
    ctx: typer.Context,
    workflow_id: Annotated[str, typer.Argument(help="Workflow ID")],
) -> None:
    """Trigger an improvement iteration."""
    from loopengine.adapters.inbound.cli.commands.improve import improve_command

    json = _json_flag(ctx)
    _run_command(
        ctx,
        lambda orch: improve_command(
            workflow_id,
            orchestrator=orch,
            json_output=json,
        ),
    )


# ── Error handling / command runner ─────────────────────────────────────


def _run_command(
    ctx: typer.Context,
    fn: Callable[..., None],
) -> None:
    """Execute a command function with error handling."""
    try:
        container = _get_container()
        fn(container.orchestrator)
    except LoopEngineError as exc:
        _handle_error(ctx, exc.code, str(exc))
        raise typer.Exit(code=1) from exc
    except KeyboardInterrupt:
        fmt.error("Interrupted")
        raise typer.Exit(code=130) from None
    except Exception as exc:
        _handle_error(ctx, "UNEXPECTED", str(exc))
        raise typer.Exit(code=1) from exc


def _handle_error(ctx: typer.Context, code: str, message: str) -> None:
    """Format and emit an error."""
    log.error("command_failed", error_code=code, message=message)

    if ctx.obj and ctx.obj.get("json_output"):
        from loopengine.adapters.inbound.cli.formatters import json_formatter

        json_formatter.emit_error(code, message)
    else:
        fmt.error(f"[{code}] {message}")


# ── Bootstrap ───────────────────────────────────────────────────────────


def create_app(*, settings: Settings | None = None) -> typer.Typer:
    """Factory — build a fully-wired Typer app.

    Separated from the module-level ``app`` so tests can inject custom
    settings or mock ports without touching globals.
    """
    global _container  # noqa: PLW0603

    if settings is None:
        settings = Settings()

    _container = Container(settings)
    return app


def bootstrap() -> None:
    """CLI entry-point: create app and run."""
    typer_app = create_app()
    typer_app()
