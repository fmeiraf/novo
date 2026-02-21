"""novo info [name] command."""

from typing import Optional

import typer
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table

from novo.cli import app


@app.command()
def info(
    name: Optional[str] = typer.Argument(None, help="Experiment name (omit for workspace info)"),
) -> None:
    """Show experiment or workspace details."""
    if name:
        _show_experiment_info(name)
    else:
        _show_workspace_info()


def _show_experiment_info(name: str) -> None:
    from novo.core.experiment import get, get_path

    exp = get(name)
    if exp is None:
        rprint(f"[red]Experiment not found:[/red] {name}")
        raise typer.Exit(1)

    path = get_path(name)

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Name", exp.name)
    table.add_row("Directory", exp.dir_name)
    table.add_row("Seed", exp.seed)
    table.add_row("Python", exp.python or "system default")
    table.add_row("Tags", ", ".join(exp.tags) if exp.tags else "none")
    table.add_row("Description", exp.description or "none")
    table.add_row("Created", exp.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("Path", str(path) if path else "unknown")

    # Check for .claude and .agents
    if path:
        has_claude = (path / ".claude").exists()
        has_agents = (path / ".agents").exists()
        table.add_row(".claude", "yes" if has_claude else "no")
        table.add_row(".agents", "yes" if has_agents else "no")

    rprint(Panel(table, title=f"Experiment: {exp.name}", border_style="cyan"))


def _show_workspace_info() -> None:
    from novo.core.config import get_workspace_path, load_config
    from novo.core.experiment import list_all

    config = load_config()
    workspace = get_workspace_path(config)
    experiments = list_all()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Workspace", str(workspace))
    table.add_row("Experiments", str(len(experiments)))
    table.add_row("Default seed", config.defaults.seed)
    table.add_row("Default python", config.defaults.python or "system default")
    table.add_row("Date prefix", "yes" if config.naming.date_prefix else "no")
    table.add_row("Auto commit", "yes" if config.defaults.auto_commit else "no")

    if experiments:
        tags = set()
        for exp in experiments:
            tags.update(exp.tags)
        table.add_row("All tags", ", ".join(sorted(tags)) if tags else "none")

    rprint(Panel(table, title="Novo Workspace", border_style="cyan"))
