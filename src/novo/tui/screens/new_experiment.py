"""Create experiment modal screen."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Select, Static

from novo.tui.widgets.seed_picker import SeedPicker
from novo.utils.uv import list_python_versions


class NewExperimentScreen(ModalScreen[bool]):
    """Modal for creating a new experiment."""

    # Layout note: the form body lives inside a VerticalScroll sized at 1fr,
    # with the title pinned above and the action buttons pinned below at a
    # fixed height. On short terminals (≲ 24 rows) the modal hits
    # `max-height: 90%`, the form scrolls internally, and Create/Cancel
    # stay visible — previously the form was a plain Vertical, so the
    # bottom of the modal (checkbox + buttons) was clipped invisibly.
    DEFAULT_CSS = """
    NewExperimentScreen {
        align: center middle;
    }
    #new-experiment-modal {
        width: 100;
        max-width: 95%;
        height: auto;
        max-height: 90%;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    #new-experiment-modal #modal-title {
        height: 1;
    }
    #new-experiment-modal #new-experiment-form {
        height: 1fr;
        padding-right: 1;
    }
    #new-experiment-modal Label {
        margin-top: 1;
    }
    #new-experiment-modal Input {
        margin-bottom: 0;
    }
    #new-experiment-modal .buttons {
        layout: horizontal;
        height: 3;
        margin-top: 1;
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

            with VerticalScroll(id="new-experiment-form"):
                yield Label("Name")
                yield Input(placeholder="my-experiment", id="name-input")

                yield Label("Description")
                yield Input(placeholder="What are you experimenting with?", id="desc-input")

                yield Label("Tags (comma-separated)")
                yield Input(placeholder="web, async, ml", id="tags-input")

                yield Label("Seed")
                # Show WORKSPACE seeds whenever they exist (even on
                # `--detached` launches with a discoverable workspace).
                # `list_seeds()` already returns nothing under `local` when
                # the cwd has no workspace context, so the WORKSPACE section
                # auto-hides on truly detached runs.
                yield SeedPicker(id="seed-picker")

                yield Label("Python version")
                yield Select(
                    self._get_python_options(),
                    value="",
                    id="python-select",
                    allow_blank=True,
                )

                yield Checkbox(
                    "Skip date prefix in directory name",
                    id="no-date-check",
                )

            with Horizontal(classes="buttons"):
                yield Button("Create", variant="primary", id="create-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

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
        seed = self.query_one("#seed-picker", SeedPicker).selected_identifier
        python = self.query_one("#python-select", Select).value
        no_date = self.query_one("#no-date-check", Checkbox).value

        from pathlib import Path

        from novo.core.experiment import create
        from novo.core.workspace import is_detached

        detached = is_detached()

        try:
            exp = create(
                name=name,
                seed_name=seed if seed else None,
                python=python if python else None,
                description=desc,
                tags=tags,
                no_date=no_date,
                detached=detached,
            )
            if detached:
                location = Path.cwd() / exp.dir_name
                self.notify(f"Created (detached): {location}", severity="information")
            else:
                self.notify(f"Created: {exp.dir_name}", severity="information")
            self.dismiss(True)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def action_cancel(self) -> None:
        self.dismiss(False)
