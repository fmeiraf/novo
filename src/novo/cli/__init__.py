"""Main Typer app and root callback."""

from typing import Optional

import typer

from novo.utils.shell import get_shell_init

app = typer.Typer(
    name="novo",
    help="A terminal tool for managing experimental Python projects.",
    no_args_is_help=False,
    invoke_without_command=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    shell_init: bool = typer.Option(False, "--shell-init", help="Print shell function for `novo open`"),
) -> None:
    """Novo — manage experimental Python projects."""
    if shell_init:
        typer.echo(get_shell_init())
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        # Launch TUI when no subcommand
        from novo.tui.app import NovoApp

        tui_app = NovoApp()
        tui_app.run()


# Import and register subcommands
from novo.cli import delete, info, list, new, open, search, seed  # noqa: E402, F401
