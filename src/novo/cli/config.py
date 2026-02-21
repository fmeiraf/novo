"""novo config subcommands."""

import typer
from rich import print as rprint
from rich.table import Table

from novo.cli import app

config_app = typer.Typer(help="View and modify configuration.")
app.add_typer(config_app, name="config")

CONFIG_KEYS: dict[str, type] = {
    "workspace.path": str,
    "defaults.seed": str,
    "defaults.auto_commit": bool,
    "defaults.python": str,
    "naming.date_prefix": bool,
}


def _get_nested(obj: object, dotted_key: str) -> object:
    """Get a value from a two-level dotted key like 'workspace.path'."""
    section, field = dotted_key.split(".")
    return getattr(getattr(obj, section), field)


def _set_nested(obj: object, dotted_key: str, value: object) -> None:
    """Set a value on a two-level dotted key like 'workspace.path'."""
    section, field = dotted_key.split(".")
    setattr(getattr(obj, section), field, value)


def _parse_bool(value: str) -> bool:
    """Parse a boolean string, accepting common truthy/falsy values."""
    if value.lower() in ("true", "yes", "1", "on"):
        return True
    if value.lower() in ("false", "no", "0", "off"):
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


@config_app.command("show")
def config_show() -> None:
    """Show all configuration values."""
    from novo.core.config import load_config

    config = load_config()

    table = Table(show_header=True, header_style="bold")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    table.add_column("Type", style="dim")

    for key, key_type in CONFIG_KEYS.items():
        value = _get_nested(config, key)
        table.add_row(key, str(value), key_type.__name__)

    rprint(table)


@config_app.command("get")
def config_get(
    key: str = typer.Argument(help="Config key (e.g. workspace.path)"),
) -> None:
    """Get a configuration value."""
    from novo.core.config import load_config

    if key not in CONFIG_KEYS:
        rprint(f"[red]Unknown config key:[/red] {key}")
        rprint(f"[dim]Valid keys: {', '.join(CONFIG_KEYS)}[/dim]")
        raise typer.Exit(1)

    config = load_config()
    typer.echo(_get_nested(config, key))


@config_app.command("set")
def config_set(
    key: str = typer.Argument(help="Config key (e.g. workspace.path)"),
    value: str = typer.Argument(help="New value"),
) -> None:
    """Set a configuration value."""
    from novo.core.config import load_config, save_config

    if key not in CONFIG_KEYS:
        rprint(f"[red]Unknown config key:[/red] {key}")
        rprint(f"[dim]Valid keys: {', '.join(CONFIG_KEYS)}[/dim]")
        raise typer.Exit(1)

    key_type = CONFIG_KEYS[key]
    try:
        if key_type is bool:
            parsed = _parse_bool(value)
        else:
            parsed = key_type(value)
    except ValueError as e:
        rprint(f"[red]Invalid value:[/red] {e}")
        raise typer.Exit(1)

    config = load_config()
    _set_nested(config, key, parsed)
    save_config(config)

    rprint(f"[green]Set[/green] {key} = {parsed}")
