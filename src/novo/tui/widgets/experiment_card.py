"""Detail panel for the selected experiment."""

from datetime import datetime

from rich.console import Group
from rich.text import Text

from textual.containers import Vertical
from textual.widgets import Static

from novo.models.experiment import Experiment

# Tag badge colors: amber, cyan, teal, pink, purple (shared with experiment_list)
TAG_COLORS = ["#FAC898", "#89DDFF", "#5DE4C7", "#D0679D", "#C792EA"]
TAG_BG_COLORS = ["#3a2e1a", "#1a2e3a", "#1a3a32", "#3a1a2e", "#2e1a3a"]

WELCOME_ART = r"""
                          ___
   ____  ____ _   _____  / _ \
  / __ \/ __ \ | / / __ \/ // /
 / / / / /_/ / |/ / /_/ /\__, /
/_/ /_/\____/|___/\____/  /_/
"""


def _relative_time(dt: datetime) -> str:
    """Format a datetime as relative time (e.g., '3d ago')."""
    now = datetime.now()
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    if months < 12:
        return f"{months}mo ago"
    years = days // 365
    return f"{years}y ago"


def _section_header(label: str) -> Text:
    """Render a dim section header."""
    t = Text()
    t.append(f"  {label}", style="dim bold")
    return t


def _field(icon: str, label: str, value: str) -> Text:
    """Render a metadata field with icon."""
    t = Text()
    t.append(f"  {icon} ", style="#89DDFF")
    t.append(f"{label}  ", style="dim")
    t.append(value)
    return t


def _tag_badges(tags: list[str]) -> Text:
    """Render tags as colored badges."""
    t = Text()
    t.append("  ")
    for i, tag in enumerate(tags):
        color = TAG_COLORS[i % len(TAG_COLORS)]
        bg = TAG_BG_COLORS[i % len(TAG_BG_COLORS)]
        t.append(f" {tag} ", style=f"{color} on {bg}")
        t.append(" ")
    return t


def _tooling_indicator(label: str, present: bool) -> Text:
    """Render a tooling indicator with green/empty dot."""
    t = Text()
    if present:
        t.append("  \u25cf ", style="green")
    else:
        t.append("  \u25cb ", style="dim")
    t.append(label, style="" if present else "dim")
    return t


class ExperimentCard(Vertical):
    """Shows details for a selected experiment."""

    DEFAULT_CSS = """
    ExperimentCard {
        padding: 1 2;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._experiment: Experiment | None = None

    def compose(self):
        yield Static("", id="card-content")

    def show_welcome(self) -> None:
        """Show the welcome screen when no experiments exist."""
        content = self.query_one("#card-content", Static)

        parts: list[Text] = []

        # ASCII art
        art = Text()
        for line in WELCOME_ART.strip().splitlines():
            art.append(line + "\n", style="#5DE4C7 bold")
        parts.append(art)

        parts.append(Text(""))

        # Tagline
        tagline = Text()
        tagline.append("  Welcome to novo!", style="bold")
        parts.append(tagline)

        parts.append(Text(""))

        # Quick-start hints
        hints = [
            ("n", "Create first experiment"),
            ("s", "Browse seeds"),
            ("/", "Search experiments"),
            ("?", "Show help"),
        ]
        for key, desc in hints:
            h = Text()
            h.append("  ")
            h.append(f" {key} ", style="bold on #1a3a32")
            h.append(f"  {desc}", style="dim")
            parts.append(h)

        parts.append(Text(""))

        # Workspace path
        from novo.core.config import load_config

        config = load_config()
        ws = Text()
        ws.append("  Workspace: ", style="dim")
        ws.append(str(config.workspace_dir), style="dim italic")
        parts.append(ws)

        content.update(Group(*parts))

    def update_experiment(self, experiment: Experiment | None) -> None:
        """Update the displayed experiment details."""
        self._experiment = experiment
        content = self.query_one("#card-content", Static)

        if experiment is None:
            self.show_welcome()
            return

        from novo.core.experiment import get_path

        path = get_path(experiment.name)

        has_claude = bool(path and (path / ".claude").exists())
        has_agents = bool(path and (path / ".agents").exists())

        parts: list[Text] = []

        # Title
        title = Text()
        title.append(f"  {experiment.name}", style="#5DE4C7 bold")
        parts.append(title)

        # Description
        if experiment.description:
            desc = Text()
            desc.append(f"  {experiment.description}", style="dim italic")
            parts.append(desc)

        parts.append(Text(""))

        # METADATA section
        parts.append(_section_header("METADATA"))

        created_abs = experiment.created_at.strftime("%b %d, %Y %H:%M")
        created_rel = _relative_time(experiment.created_at)
        parts.append(_field("\u25f7", "Created", f"{created_abs}  ({created_rel})"))
        parts.append(_field("\u2736", "Seed", experiment.seed))
        parts.append(_field("\u2666", "Python", experiment.python or "system default"))
        parts.append(_field("\u2192", "Directory", experiment.dir_name))

        parts.append(Text(""))

        # TAGS section
        parts.append(_section_header("TAGS"))
        if experiment.tags:
            parts.append(_tag_badges(experiment.tags))
        else:
            none_text = Text()
            none_text.append("  none", style="dim")
            parts.append(none_text)

        parts.append(Text(""))

        # TOOLING section
        parts.append(_section_header("TOOLING"))
        parts.append(_tooling_indicator("Claude Code", has_claude))
        parts.append(_tooling_indicator("Agents", has_agents))

        content.update(Group(*parts))
