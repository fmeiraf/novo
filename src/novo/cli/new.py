"""novo new <name> command."""

from typing import Optional

import typer
from rich import print as rprint

from novo.cli import app


@app.command()
def new(
    name: str = typer.Argument(help="Name for the new experiment"),
    seed: Optional[str] = typer.Option(None, "--seed", "-s", help="Seed template to use"),
    python: Optional[str] = typer.Option(None, "--python", "-p", help="Python version"),
    description: str = typer.Option("", "--desc", "-d", help="Description"),
    tags: Optional[list[str]] = typer.Option(None, "--tag", "-t", help="Tags"),
    no_date: bool = typer.Option(False, "--no-date", help="Don't add date prefix to directory"),
) -> None:
    """Create a new experiment."""
    from novo.core.experiment import create

    try:
        exp = create(
            name=name,
            seed_name=seed,
            python=python,
            description=description,
            tags=tags or [],
            no_date=no_date,
        )
        rprint(f"[green]Created experiment:[/green] {exp.dir_name}")
    except FileExistsError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error creating experiment:[/red] {e}")
        raise typer.Exit(1)
