"""novo init [path] command."""

from typing import Optional

import typer
from rich import print as rprint

from novo.cli import app


@app.command()
def init(
    path: Optional[str] = typer.Argument(None, help="Directory to use as workspace (defaults to current directory)"),
) -> None:
    """Initialize a workspace directory."""
    from pathlib import Path

    from novo.core.config import load_config, save_config
    from novo.core.workspace import ensure_initialized
    from novo.utils.paths import config_file

    resolved = Path(path).resolve() if path else Path.cwd()

    config = load_config()
    config.workspace.path = str(resolved)
    save_config(config)

    ensure_initialized()

    rprint(f"[green]Workspace initialized:[/green] {resolved}")
    rprint(f"[dim]Config saved to {config_file()}[/dim]")
