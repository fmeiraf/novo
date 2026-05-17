"""Modal for scaffolding a new seed (local or user scope)."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static


class NewSeedScreen(ModalScreen[bool]):
    """Inputs for name / description / scope. Calls `init_seed` on submit."""

    DEFAULT_CSS = """
    NewSeedScreen {
        align: center middle;
    }
    #new-seed-modal {
        width: 60;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    #new-seed-modal Label {
        margin-top: 1;
    }
    #new-seed-modal Input {
        margin-bottom: 0;
    }
    #new-seed-modal .buttons {
        margin-top: 1;
        layout: horizontal;
        height: 3;
    }
    #new-seed-modal .buttons Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        from novo.core.workspace import discover

        # Default scope mirrors the CLI: local if cwd is inside a workspace.
        default_scope = "local" if discover() is not None else "user"

        with Vertical(id="new-seed-modal"):
            yield Static("[b]New Seed[/]")

            yield Label("Name (required)")
            yield Input(placeholder="my-seed", id="name-input")

            yield Label("Description")
            yield Input(placeholder="What does this seed scaffold?", id="desc-input")

            yield Label("Scope")
            yield Select(
                [("local (workspace)", "local"), ("user (~/.local/share/novo/seeds)", "user")],
                value=default_scope,
                id="scope-select",
                allow_blank=False,
            )

            with Vertical(classes="buttons"):
                yield Button("Create", variant="primary", id="create-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-btn":
            self._create()
        elif event.button.id == "cancel-btn":
            self.dismiss(False)

    def _create(self) -> None:
        name = self.query_one("#name-input", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return
        desc = self.query_one("#desc-input", Input).value.strip()
        scope = self.query_one("#scope-select", Select).value

        from novo.core.seed import init_seed

        try:
            scoped = init_seed(name, desc, scope=scope)
            self.notify(f"Created seed: {scoped.identifier}", severity="information")
            self.dismiss(True)
        except FileExistsError as err:
            self.notify(str(err), severity="error")
        except Exception as err:  # noqa: BLE001
            self.notify(f"Create failed: {err}", severity="error")

    def action_cancel(self) -> None:
        self.dismiss(False)
