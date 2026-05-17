"""Modal for linking (and immediately syncing) a remote seed registry."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class RemoteLinkScreen(ModalScreen[bool]):
    """Inputs for URL / name / ref. Links + syncs the remote on submit."""

    DEFAULT_CSS = """
    RemoteLinkScreen {
        align: center middle;
    }
    #remote-link-modal {
        width: 70;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    #remote-link-modal Label {
        margin-top: 1;
    }
    #remote-link-modal Input {
        margin-bottom: 0;
    }
    #remote-link-modal .buttons {
        margin-top: 1;
        layout: horizontal;
        height: 3;
    }
    #remote-link-modal .buttons Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="remote-link-modal"):
            yield Static("[b]Link Remote Seed Registry[/]")

            yield Label("Git URL (required)")
            yield Input(placeholder="git@github.com:team/seeds.git", id="url-input")

            yield Label("Local name (optional — defaults to repo name)")
            yield Input(placeholder="team", id="name-input")

            yield Label("Ref (optional — branch/tag/sha; default: cloned branch)")
            yield Input(placeholder="main", id="ref-input")

            with Vertical(classes="buttons"):
                yield Button("Link", variant="primary", id="link-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "link-btn":
            self._link()
        elif event.button.id == "cancel-btn":
            self.dismiss(False)

    def _link(self) -> None:
        url = self.query_one("#url-input", Input).value.strip()
        name = self.query_one("#name-input", Input).value.strip() or None
        ref = self.query_one("#ref-input", Input).value.strip() or None

        if not url:
            self.notify("URL is required", severity="error")
            return

        from novo.core.seed import link_remote

        try:
            remote = link_remote(url, name=name, ref=ref)
            self.notify(f"Linked remote: {remote.name}", severity="information")
            self.dismiss(True)
        except Exception as err:  # noqa: BLE001
            self.notify(f"Link failed: {err}", severity="error")

    def action_cancel(self) -> None:
        self.dismiss(False)
