"""Main Textual TUI application."""

from pathlib import Path

from textual.app import App
from textual.binding import Binding

from novo.tui.screens.main import MainScreen


class NovoApp(App):
    """The novo TUI application."""

    TITLE = "novo"
    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
    ]

    def on_mount(self) -> None:
        self.push_screen(MainScreen())
