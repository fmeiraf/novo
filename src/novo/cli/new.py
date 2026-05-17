"""novo new <name> command."""

from typing import Optional

import typer
from rich import print as rprint

from novo.cli import app


@app.command()
def new(
    name: str = typer.Argument(help="Name for the new experiment"),
    seed: Optional[str] = typer.Option(
        None,
        "--seed",
        "-s",
        help="Seed template. Accepts scoped forms: local:foo, user:foo, remote:team/foo, builtin:foo.",
    ),
    python: Optional[str] = typer.Option(None, "--python", "-p", help="Python version"),
    description: str = typer.Option("", "--desc", "-d", help="Description"),
    tags: Optional[list[str]] = typer.Option(None, "--tag", "-t", help="Tags"),
    no_date: bool = typer.Option(False, "--no-date", help="Don't add date prefix to directory"),
    at: Optional[str] = typer.Option(
        None,
        "--at",
        help="(Detached only) Parent directory for the experiment. Defaults to cwd.",
    ),
) -> None:
    """Create a new experiment."""
    from pathlib import Path

    from novo.core.experiment import create
    from novo.core.workspace import is_detached_forced

    detached = is_detached_forced()
    at_path = Path(at).resolve() if at else None
    if at_path is not None and not detached:
        rprint("[red]Error:[/red] --at requires --detached.")
        raise typer.Exit(1)

    try:
        exp = create(
            name=name,
            seed_name=seed,
            python=python,
            description=description,
            tags=tags or [],
            no_date=no_date,
            detached=detached,
            at=at_path,
        )
        rprint(f"[green]Created experiment:[/green] {exp.dir_name}")
        rprint(f"[dim]Seed:[/dim] {exp.seed}")
        if detached:
            location = (at_path or Path.cwd()) / exp.dir_name
            rprint(f"[dim]Detached at:[/dim] {location}")
    except FileExistsError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except ValueError as e:
        rprint(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error creating experiment:[/red] {e}")
        raise typer.Exit(1)
