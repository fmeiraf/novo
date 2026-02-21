"""Detail panel for the selected experiment."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from novo.models.experiment import Experiment


class ExperimentCard(Vertical):
    """Shows details for a selected experiment."""

    DEFAULT_CSS = """
    ExperimentCard {
        padding: 1 2;
    }
    ExperimentCard .card-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    ExperimentCard .card-field {
        margin-bottom: 0;
    }
    ExperimentCard .card-label {
        text-style: bold;
        color: $text-muted;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._experiment: Experiment | None = None

    def compose(self) -> ComposeResult:
        yield Static("Select an experiment", id="card-content")

    def update_experiment(self, experiment: Experiment | None) -> None:
        """Update the displayed experiment details."""
        self._experiment = experiment
        content = self.query_one("#card-content", Static)

        if experiment is None:
            content.update("Select an experiment")
            return

        from novo.core.experiment import get_path

        path = get_path(experiment.name)

        has_claude = "yes" if path and (path / ".claude").exists() else "no"
        has_agents = "yes" if path and (path / ".agents").exists() else "no"

        tags = ", ".join(experiment.tags) if experiment.tags else "none"
        created = experiment.created_at.strftime("%b %d, %Y %H:%M")

        lines = [
            f"[bold $accent]{experiment.name}[/]",
            "",
            f"[bold]Created:[/]    {created}",
            f"[bold]Seed:[/]       {experiment.seed}",
            f"[bold]Python:[/]     {experiment.python or 'system default'}",
            f"[bold]Tags:[/]       {tags}",
            f"[bold]Description:[/] {experiment.description or 'none'}",
            "",
            f"[bold]Directory:[/]  {experiment.dir_name}",
            f"[bold].claude:[/]    {has_claude}",
            f"[bold].agents:[/]    {has_agents}",
        ]

        content.update("\n".join(lines))
