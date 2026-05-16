"""novo init [path] command."""

from typing import Optional

import typer
from rich import print as rprint

from novo.cli import app


@app.command()
def init(
    path: Optional[str] = typer.Argument(None, help="Directory to initialize as a workspace (defaults to current directory)"),
) -> None:
    """Initialize a workspace directory by creating its `.novo/` marker."""
    from pathlib import Path

    from novo.core.workspace import ensure_initialized

    resolved = Path(path).resolve() if path else Path.cwd().resolve()
    ensure_initialized(resolved)

    rprint(f"[green]Workspace initialized:[/green] {resolved}")
    rprint(f"[dim]Marker:[/dim] {resolved / '.novo'}")
    rprint(
        f"[dim]To make this your default workspace:[/dim] "
        f"[cyan]novo config set workspace.path {resolved}[/cyan]"
    )
