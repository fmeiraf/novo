"""Context-sensitive keybinding status bar."""

from textual.app import ComposeResult
from textual.widgets import Static


def _badge(key: str, label: str) -> str:
    """Format a key badge: teal-highlighted key + dim label."""
    return f"[bold on #1a3a32] {key} [/] [dim]{label}[/]"


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
        self._default_text = "  ".join([
            _badge("n", "new"),
            _badge("enter", "open"),
            _badge("d", "delete"),
            _badge("s", "seeds"),
            _badge("/", "search"),
            _badge("?", "help"),
            _badge("q", "quit"),
        ])

    def on_mount(self) -> None:
        self.update(self._default_text)

    def set_context(self, context: str = "main") -> None:
        """Update keybindings for the current context."""
        if context == "search":
            self.update("  ".join([_badge("esc", "cancel"), _badge("enter", "select")]))
        elif context == "new":
            self.update("  ".join([_badge("esc", "cancel"), _badge("enter", "create")]))
        elif context == "confirm":
            self.update("  ".join([_badge("y", "yes"), _badge("n", "no")]))
        else:
            self.update(self._default_text)
