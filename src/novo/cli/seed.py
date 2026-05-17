"""novo seed subcommands."""

import json as _json
from typing import Optional

import typer
from rich import print as rprint

from novo.cli import app

seed_app = typer.Typer(help="Manage seed templates.")
app.add_typer(seed_app, name="seed")


def _scope_header(scope: str, remote: str | None, remote_urls: dict[str, str]) -> str:
    if scope == "local":
        return "[bold cyan]WORKSPACE[/]  [dim](./.novo/seeds/)[/]"
    if scope == "user":
        return "[bold blue]USER[/]  [dim](~/.local/share/novo/seeds/)[/]"
    if scope == "remote":
        url = remote_urls.get(remote or "", f"~/.local/share/novo/remotes/{remote}/")
        return f"[bold yellow]REMOTE: {remote}[/]  [dim]({url})[/]"
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
    from novo.core.seed import list_remotes, list_seeds
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

    remote_urls = {r.name: r.url for r in list_remotes()}

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
        rprint(_scope_header(scope_name, remote_name, remote_urls))
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


@seed_app.command("link")
def seed_link(
    url: str = typer.Argument(help="Git URL of the remote seed registry"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Local name for the remote (defaults to repo name)"),
    ref: Optional[str] = typer.Option(None, "--ref", "-r", help="Branch/tag/SHA to track (default: main)"),
) -> None:
    """Link a remote seed registry. Idempotent: re-running updates the link."""
    from novo.core.seed import link_remote

    try:
        remote = link_remote(url, name=name, ref=ref)
        rprint(f"[green]Linked remote:[/green] {remote.name}  [dim]({remote.url})[/]")
        rprint(f"  [dim]ref:[/] {remote.ref}")
        rprint(f"  [dim]use `novo seed sync {remote.name}` to refresh[/]")
    except Exception as e:
        rprint(f"[red]Error linking remote:[/red] {e}")
        raise typer.Exit(1)


@seed_app.command("sync")
def seed_sync(
    name: Optional[str] = typer.Argument(None, help="Remote name to sync (defaults to all)"),
) -> None:
    """Pull updates for one or all linked remotes."""
    from novo.core.seed import sync_remote

    try:
        results = sync_remote(name)
    except ValueError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    if not results:
        rprint("[dim]No linked remotes.[/dim] Add one with [cyan]novo seed link <url>[/]")
        return

    exit_code = 0
    for remote_name, ok, msg in results:
        icon = "[green]✓[/]" if ok else "[red]✗[/]"
        rprint(f"{icon} [bold]{remote_name}[/]  {msg}")
        if not ok:
            exit_code = 1
    raise typer.Exit(exit_code)


@seed_app.command("unlink")
def seed_unlink(
    name: str = typer.Argument(help="Name of the remote to unlink"),
) -> None:
    """Remove a linked remote (config entry and local clone)."""
    from novo.core.seed import unlink_remote

    if unlink_remote(name):
        rprint(f"[green]Unlinked remote:[/green] {name}")
    else:
        rprint(f"[red]Unknown remote:[/red] {name}")
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
