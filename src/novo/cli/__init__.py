"""Main Typer app and root callback."""

import os
from typing import Optional

import typer

from novo import __version__
from novo.utils.shell import get_shell_init

app = typer.Typer(
    name="novo",
    help="A terminal tool for managing experimental Python projects.",
    no_args_is_help=False,
    invoke_without_command=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"novo {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-W",
        help="Workspace to operate on. Overrides cwd discovery and NOVO_WORKSPACE.",
    ),
    shell_init: bool = typer.Option(False, "--shell-init", help="Print shell function for `novo open`"),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the novo version and exit.",
    ),
) -> None:
    """Novo — manage experimental Python projects."""
    from novo.core.workspace import set_workspace_override

    explicit = workspace or os.environ.get("NOVO_WORKSPACE") or None
    set_workspace_override(explicit)

    if shell_init:
        typer.echo(get_shell_init())
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        # Launch TUI when no subcommand
        from novo.tui.app import NovoApp

        tui_app = NovoApp()
        tui_app.run()


# Import and register subcommands
from novo.cli import config, delete, info, init, list, new, open, search, seed  # noqa: E402, F401
