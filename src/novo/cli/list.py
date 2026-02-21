"""novo list command."""

import json
from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from novo.cli import app


@app.command("list")
def list_experiments(
    sort: str = typer.Option("created", "--sort", help="Sort by: name, created, modified"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all experiments."""
    from novo.core.experiment import list_all

    experiments = list_all(sort_by=sort, tag=tag)

    if output_json:
        data = [exp.model_dump(mode="json") for exp in experiments]
        typer.echo(json.dumps(data, indent=2, default=str))
        return

    if not experiments:
        rprint("[dim]No experiments found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Directory")
    table.add_column("Seed", style="dim")
    table.add_column("Tags", style="green")
    table.add_column("Created", style="dim")

    for exp in experiments:
        tags = ", ".join(exp.tags) if exp.tags else ""
        created = exp.created_at.strftime("%Y-%m-%d %H:%M")
        table.add_row(exp.name, exp.dir_name, exp.seed, tags, created)

    rprint(table)
