"""Delete confirmation modal."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmScreen(ModalScreen[bool]):
    """A confirmation dialog."""

    DEFAULT_CSS = """
    ConfirmScreen {
        align: center middle;
    }
    #confirm-modal {
        width: 50;
        height: auto;
        border: solid $error;
        background: $surface;
        padding: 1 2;
    }
    #confirm-modal .buttons {
        margin-top: 1;
        layout: horizontal;
        height: 3;
    }
    #confirm-modal .buttons Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-modal"):
            yield Static(f"[b]{self._message}[/]")
            with Horizontal(classes="buttons"):
                yield Button("Yes", variant="error", id="yes-btn")
                yield Button("No", variant="default", id="no-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes-btn":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
