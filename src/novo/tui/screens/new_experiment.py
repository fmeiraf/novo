"""Create experiment modal screen."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

from novo.utils.uv import list_python_versions


class NewExperimentScreen(ModalScreen[bool]):
    """Modal for creating a new experiment."""

    DEFAULT_CSS = """
    NewExperimentScreen {
        align: center middle;
    }
    #new-experiment-modal {
        width: 60;
        height: auto;
        max-height: 80%;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    #new-experiment-modal Label {
        margin-top: 1;
    }
    #new-experiment-modal Input {
        margin-bottom: 0;
    }
    #new-experiment-modal .buttons {
        margin-top: 1;
        layout: horizontal;
        height: 3;
    }
    #new-experiment-modal .buttons Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="new-experiment-modal"):
            yield Static("[b]New Experiment[/]", id="modal-title")

            yield Label("Name")
            yield Input(placeholder="my-experiment", id="name-input")

            yield Label("Description")
            yield Input(placeholder="What are you experimenting with?", id="desc-input")

            yield Label("Tags (comma-separated)")
            yield Input(placeholder="web, async, ml", id="tags-input")

            yield Label("Seed")
            yield Select(
                self._get_seed_options(),
                value="default",
                id="seed-select",
            )

            yield Label("Python version")
            yield Select(
                self._get_python_options(),
                value="",
                id="python-select",
                allow_blank=True,
            )

            with Vertical(classes="buttons"):
                yield Button("Create", variant="primary", id="create-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def _get_seed_options(self) -> list[tuple[str, str]]:
        from novo.core.seed import list_seeds

        seeds = list_seeds()
        if not seeds:
            return [("default", "default")]
        return [(s.name, s.name) for s in seeds]

    def _get_python_options(self) -> list[tuple[str, str]]:
        versions = list_python_versions()
        options = [("System default", "")]
        options.extend([(v, v) for v in versions])
        return options

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-btn":
            self._create_experiment()
        elif event.button.id == "cancel-btn":
            self.dismiss(False)

    def _create_experiment(self) -> None:
        name = self.query_one("#name-input", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return

        desc = self.query_one("#desc-input", Input).value.strip()
        tags_str = self.query_one("#tags-input", Input).value.strip()
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
        seed = self.query_one("#seed-select", Select).value
        python = self.query_one("#python-select", Select).value

        from novo.core.experiment import create

        try:
            exp = create(
                name=name,
                seed_name=seed if seed else None,
                python=python if python else None,
                description=desc,
                tags=tags,
            )
            self.notify(f"Created: {exp.dir_name}", severity="information")
            self.dismiss(True)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def action_cancel(self) -> None:
        self.dismiss(False)
