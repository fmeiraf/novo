"""Context-sensitive keybinding + mode status bar."""

from textual.widgets import Static


def _badge(key: str, label: str) -> str:
    """Format a key badge: teal-highlighted key + dim label."""
    return f"[bold on #1a3a32] {key} [/] [dim]{label}[/]"


def _mode_chip(text: str, detached: bool) -> str:
    """Format the leading mode chip (workspace vs detached)."""
    color = "#3a1a32" if detached else "#1a323a"
    return f"[bold on {color}] {text} [/]"


class StatusBar(Static):
    """Shows the current mode + available keybindings."""

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
            _badge("e", "experiments"),
            _badge("s", "seeds"),
            _badge("n", "new"),
            _badge("enter", "open"),
            _badge("d", "delete"),
            _badge("/", "search"),
            _badge("?", "help"),
            _badge("q", "quit"),
        ])
        self._mode: str | None = None
        self._mode_detached = False
        self._suffix = self._default_text
        self._sync_note: str | None = None

    def on_mount(self) -> None:
        self._repaint()

    def set_mode(self, text: str, *, detached: bool = False) -> None:
        """Set the leading mode chip (e.g. `WORKSPACE: foo` or `DETACHED`)."""
        self._mode = text
        self._mode_detached = detached
        self._repaint()

    def set_sync_note(self, text: str | None) -> None:
        """Set a transient note (sync results) appended after the bindings."""
        self._sync_note = text
        self._repaint()

    def set_context(self, context: str = "main") -> None:
        """Update keybindings for the current context."""
        if context == "search":
            self._suffix = "  ".join([_badge("esc", "cancel"), _badge("enter", "select")])
        elif context == "new":
            self._suffix = "  ".join([_badge("esc", "cancel"), _badge("enter", "create")])
        elif context == "confirm":
            self._suffix = "  ".join([_badge("y", "yes"), _badge("n", "no")])
        elif context == "seeds":
            self._suffix = "  ".join([
                _badge("e", "experiments"),
                _badge("N", "new seed"),
                _badge("l", "link"),
                _badge("u", "unlink"),
                _badge("r", "sync"),
                _badge("?", "help"),
                _badge("q", "quit"),
            ])
        else:
            self._suffix = self._default_text
        self._repaint()

    def compose_text(self) -> str:
        """Return the rendered markup string (testable without mounting)."""
        parts: list[str] = []
        if self._mode:
            parts.append(_mode_chip(self._mode, self._mode_detached))
        parts.append(self._suffix)
        if self._sync_note:
            parts.append(f"[dim]{self._sync_note}[/]")
        return "  ".join(parts)

    def _repaint(self) -> None:
        # NOTE: do not name this `_render` — Textual's Widget._render() is the
        # framework hook that returns the Visual to draw. Overriding it (even
        # to call self.update) shadows the base implementation and the widget
        # renders as None.
        self.update(self.compose_text())
