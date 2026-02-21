"""novo open <name> command (+ hidden _open-path)."""

import typer
from rich import print as rprint

from novo.cli import app


@app.command()
def open(
    name: str = typer.Argument(help="Name of the experiment to open"),
) -> None:
    """Open an experiment directory (requires shell integration)."""
    rprint(
        "[yellow]Note:[/yellow] `novo open` requires shell integration.\n"
        'Add this to your shell rc: [cyan]eval "$(novo --shell-init)"[/cyan]'
    )
    from novo.core.experiment import get_path

    path = get_path(name)
    if path is None:
        rprint(f"[red]Experiment not found:[/red] {name}")
        raise typer.Exit(1)
    rprint(f"[dim]Path:[/dim] {path}")


@app.command(hidden=True)
def _open_path(
    name: str = typer.Argument(help="Name of the experiment"),
) -> None:
    """Print the path to an experiment (used by shell function)."""
    from novo.core.experiment import get_path

    path = get_path(name)
    if path is None:
        raise typer.Exit(1)
    typer.echo(str(path))
