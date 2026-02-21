"""novo search <query> command."""

import json

import typer
from rich import print as rprint
from rich.table import Table

from novo.cli import app


@app.command()
def search(
    query: str = typer.Argument(help="Search query"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Search experiments by name, description, or tags."""
    from novo.core.experiment import search as search_experiments

    results = search_experiments(query)

    if output_json:
        data = [exp.model_dump(mode="json") for exp in results]
        typer.echo(json.dumps(data, indent=2, default=str))
        return

    if not results:
        rprint(f"[dim]No experiments matching '{query}'.[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Directory")
    table.add_column("Tags", style="green")
    table.add_column("Description", style="dim")

    for exp in results:
        tags = ", ".join(exp.tags) if exp.tags else ""
        table.add_row(exp.name, exp.dir_name, tags, exp.description[:50])

    rprint(table)
