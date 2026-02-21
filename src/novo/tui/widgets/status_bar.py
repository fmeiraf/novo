"""Context-sensitive keybinding status bar."""

from textual.app import ComposeResult
from textual.widgets import Static


class StatusBar(Static):
    """Shows available keybindings."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._default_text = (
            "[b]n[/]ew  [b]enter[/] open  [b]d[/]elete  [b]s[/]eeds  [b]/[/]search  [b]?[/]help  [b]q[/]uit"
        )

    def on_mount(self) -> None:
        self.update(self._default_text)

    def set_context(self, context: str = "main") -> None:
        """Update keybindings for the current context."""
        if context == "search":
            self.update("[b]esc[/] cancel  [b]enter[/] select")
        elif context == "new":
            self.update("[b]esc[/] cancel  [b]enter[/] create")
        elif context == "confirm":
            self.update("[b]y[/]es  [b]n[/]o")
        else:
            self.update(self._default_text)
