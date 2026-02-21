"""Main Textual TUI application."""

from pathlib import Path

from textual.app import App
from textual.binding import Binding
from textual.theme import Theme

from novo.tui.screens.main import MainScreen

NOVO_DARK = Theme(
    name="novo-dark",
    primary="#5DE4C7",
    secondary="#89DDFF",
    accent="#FAC898",
    background="#1B1E28",
    surface="#232736",
    panel="#2A2F3E",
    error="#D0679D",
    dark=True,
)


class NovoApp(App):
    """The novo TUI application."""

    TITLE = "novo"
    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
    ]

    def on_mount(self) -> None:
        self.register_theme(NOVO_DARK)
        self.theme = "novo-dark"
        self.push_screen(MainScreen())
