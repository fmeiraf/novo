"""novo delete <name> command."""

import typer
from rich import print as rprint

from novo.cli import app


@app.command()
def delete(
    name: str = typer.Argument(help="Name of the experiment to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an experiment."""
    from novo.core.experiment import delete as delete_experiment
    from novo.core.experiment import get

    exp = get(name)
    if exp is None:
        rprint(f"[red]Experiment not found:[/red] {name}")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Delete experiment '{exp.name}' ({exp.dir_name})?")
        if not confirm:
            rprint("[dim]Cancelled.[/dim]")
            raise typer.Exit()

    if delete_experiment(name):
        rprint(f"[green]Deleted:[/green] {exp.name}")
    else:
        rprint(f"[red]Failed to delete:[/red] {name}")
        raise typer.Exit(1)
