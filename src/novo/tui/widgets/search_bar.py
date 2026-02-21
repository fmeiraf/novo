"""Fuzzy search input widget."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Input, Static


class SearchBar(Horizontal):
    """A search bar for filtering experiments."""

    DEFAULT_CSS = """
    SearchBar {
        height: 3;
        padding: 0 1;
        dock: top;
    }
    SearchBar #search-prefix {
        width: 2;
        height: 1;
        margin-top: 1;
        color: $accent;
    }
    SearchBar Input {
        width: 1fr;
    }
    """

    class Changed(Message):
        """Posted when the search query changes."""

        def __init__(self, query: str) -> None:
            self.query = query
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Static("> ", id="search-prefix")
        yield Input(placeholder="Search experiments...", id="search-input")

    def on_input_changed(self, event: Input.Changed) -> None:
        self.post_message(self.Changed(event.value))

    def focus_input(self) -> None:
        self.query_one("#search-input", Input).focus()

    def clear(self) -> None:
        self.query_one("#search-input", Input).value = ""
