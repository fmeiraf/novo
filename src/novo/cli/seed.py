"""novo seed subcommands."""

from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from novo.cli import app

seed_app = typer.Typer(help="Manage seed templates.")
app.add_typer(seed_app, name="seed")


@seed_app.command("list")
def seed_list() -> None:
    """List available seeds."""
    from novo.core.seed import list_seeds

    seeds = list_seeds()

    if not seeds:
        rprint("[dim]No seeds found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Type", style="dim")
    table.add_column("Packages", style="green")

    for seed in seeds:
        seed_type = "built-in" if seed.builtin else "user"
        packages = ", ".join(seed.dependencies.packages) if seed.dependencies.packages else ""
        table.add_row(seed.name, seed.description, seed_type, packages)

    rprint(table)


@seed_app.command("add")
def seed_add(
    url: str = typer.Argument(help="Git URL of the seed repository"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Custom name for the seed"),
) -> None:
    """Install a seed from a git repository."""
    from novo.core.seed import add_from_git

    try:
        seed = add_from_git(url, name)
        rprint(f"[green]Installed seed:[/green] {seed.name}")
    except FileExistsError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error installing seed:[/red] {e}")
        raise typer.Exit(1)


@seed_app.command("create")
def seed_create(
    name: str = typer.Argument(help="Name for the new seed"),
    experiment: str = typer.Option(..., "--from", "-f", help="Experiment to create seed from"),
    description: str = typer.Option("", "--desc", "-d", help="Seed description"),
) -> None:
    """Create a new seed from an existing experiment."""
    from novo.core.experiment import get_path
    from novo.core.seed import create_from_experiment

    exp_path = get_path(experiment)
    if exp_path is None:
        rprint(f"[red]Experiment not found:[/red] {experiment}")
        raise typer.Exit(1)

    try:
        seed = create_from_experiment(exp_path, name, description)
        rprint(f"[green]Created seed:[/green] {seed.name}")
    except FileExistsError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@seed_app.command("remove")
def seed_remove(
    name: str = typer.Argument(help="Name of the seed to remove"),
) -> None:
    """Remove a user-installed seed."""
    from novo.core.seed import get_seed, remove_seed

    seed = get_seed(name)
    if seed is None:
        rprint(f"[red]Seed not found:[/red] {name}")
        raise typer.Exit(1)

    if seed.builtin:
        rprint(f"[red]Cannot remove built-in seed:[/red] {name}")
        raise typer.Exit(1)

    if remove_seed(name):
        rprint(f"[green]Removed seed:[/green] {name}")
    else:
        rprint(f"[red]Failed to remove seed:[/red] {name}")
        raise typer.Exit(1)
