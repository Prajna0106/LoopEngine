"""Console output formatter — Rich-based terminal rendering."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

_console = Console(stderr=True)


def success(message: str) -> None:
    """Print a success message."""
    _console.print(Text(f"  {message}", style="green"))


def error(message: str) -> None:
    """Print an error message."""
    _console.print(Text(f"  {message}", style="red"))


def info(message: str) -> None:
    """Print an informational message."""
    _console.print(Text(f"  {message}", style="dim"))


def heading(title: str) -> None:
    """Print a section heading."""
    _console.print()
    _console.print(Text(title, style="bold cyan"))


def panel(title: str, content: str, *, style: str = "blue") -> None:
    """Render content inside a Rich panel."""
    _console.print(Panel(content, title=title, border_style=style))


def check_table(checks: list[dict[str, Any]]) -> None:
    """Render a health-check table."""
    table = Table(title="Health Checks", show_header=True)
    table.add_column("Check", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Detail", style="dim")

    for item in checks:
        status = Text("PASS", style="green") if item["ok"] else Text("FAIL", style="red")
        table.add_row(item["name"], status, item.get("detail", ""))

    _console.print(table)


def workflow_summary(data: dict[str, Any]) -> None:
    """Render a workflow summary panel."""
    lines = [
        f"[bold]ID:[/]       {data.get('workflow_id', '-')}",
        f"[bold]Status:[/]   {data.get('status', '-')}",
        f"[bold]Iterations:[/] {data.get('iterations', '-')}",
    ]
    if summary := data.get("summary"):
        lines.append(f"\n{summary}")
    panel("Workflow", "\n".join(lines))
