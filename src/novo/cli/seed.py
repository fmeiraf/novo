"""novo seed subcommands."""

import json as _json
from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from novo.cli import app

seed_app = typer.Typer(help="Manage seed templates.")
app.add_typer(seed_app, name="seed")


_SCOPE_BADGE = {
    "local": "[bold cyan]\\[local][/]",
    "user": "[bold blue]\\[user][/]",
    "remote": "[bold yellow]\\[remote][/]",
    "builtin": "[dim]\\[builtin][/]",
}


def _scope_header(scope: str, remote: str | None) -> str:
    if scope == "local":
        return "[bold cyan]WORKSPACE[/]  [dim](./.novo/seeds/)[/]"
    if scope == "user":
        return "[bold blue]USER[/]  [dim](~/.local/share/novo/seeds/)[/]"
    if scope == "remote":
        return f"[bold yellow]REMOTE: {remote}[/]  [dim](~/.local/share/novo/remotes/{remote}/)[/]"
    if scope == "builtin":
        return "[dim bold]BUILTIN[/]"
    return scope


@seed_app.command("list")
def seed_list(
    scope: Optional[str] = typer.Option(
        None,
        "--scope",
        help="Filter by scope: local, user, remote, builtin.",
    ),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List available seeds, grouped by scope."""
    from novo.core.seed import list_seeds
    from novo.models.scoped_seed import VALID_SCOPES

    if scope is not None and scope not in VALID_SCOPES:
        rprint(f"[red]Unknown scope:[/red] {scope}")
        rprint(f"[dim]Expected one of: {', '.join(VALID_SCOPES)}[/dim]")
        raise typer.Exit(1)

    seeds = list_seeds()
    if scope is not None:
        seeds = [s for s in seeds if s.scope == scope]

    if output_json:
        data = [
            {
                "name": s.seed.name,
                "description": s.seed.description,
                "scope": s.scope,
                "remote": s.remote,
                "identifier": s.identifier,
                "path": s.seed.path,
                "packages": s.seed.dependencies.packages,
            }
            for s in seeds
        ]
        typer.echo(_json.dumps(data, indent=2))
        return

    if not seeds:
        rprint("[dim]No seeds found.[/dim]")
        return

    # Group while preserving the resolution order (local, user, remote, builtin).
    groups: list[tuple[tuple[str, str | None], list]] = []
    for s in seeds:
        key = (s.scope, s.remote)
        if not groups or groups[-1][0] != key:
            groups.append((key, []))
        groups[-1][1].append(s)

    first = True
    for (scope_name, remote_name), items in groups:
        if not first:
            rprint("")
        first = False
        rprint(_scope_header(scope_name, remote_name))
        for s in items:
            desc = s.seed.description or ""
            rprint(f"  [cyan]{s.seed.name:<20}[/]  {desc}")


@seed_app.command("init")
def seed_init(
    name: str = typer.Argument(help="Name for the new seed"),
    description: str = typer.Option("", "--desc", "-d", help="Seed description"),
    scope: Optional[str] = typer.Option(
        None,
        "--scope",
        help="Where to create the seed: local (workspace) or user (~/.local/share/novo/seeds/). "
        "Default: local if inside a workspace, else user.",
    ),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Custom directory for the seed (overrides --scope)"),
) -> None:
    """Scaffold a new empty seed (seed.toml + template/)."""
    from pathlib import Path

    from novo.core.seed import init_seed
    from novo.core.workspace import discover

    explicit_path = Path(path) if path else None

    if scope is None:
        scope = "local" if discover() is not None else "user"
    if scope not in ("local", "user"):
        rprint(f"[red]Cannot init a {scope!r} seed; use local or user.[/red]")
        raise typer.Exit(1)

    try:
        scoped = init_seed(name, description, explicit_path, scope=scope)
        rprint(f"[green]Created seed:[/green] {scoped.identifier}")
        rprint(f"  [dim]Path:[/dim] {scoped.seed.path}")
        rprint(f"  [dim]Next steps:[/dim] add template files to [cyan]template/[/cyan], edit [cyan]seed.toml[/cyan]")
    except FileExistsError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@seed_app.command("add")
def seed_add(
    url: str = typer.Argument(help="Git URL of the seed repository"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Custom name for the seed"),
) -> None:
    """Install a single-seed repo from a git URL (user scope).

    Deprecated: prefer `novo seed link` (phase 4) for multi-seed repos.
    """
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
