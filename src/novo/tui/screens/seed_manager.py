"""Seed management screen."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static
from textual.widgets.option_list import Option

from textual.widgets import OptionList


class SeedManagerScreen(Screen):
    """Screen for managing seed templates."""

    DEFAULT_CSS = """
    SeedManagerScreen {
        layout: vertical;
    }
    #seed-container {
        layout: horizontal;
        height: 1fr;
    }
    #seed-list-panel {
        width: 1fr;
        border-right: solid $primary-lighten-2;
    }
    #seed-detail-panel {
        width: 1fr;
        padding: 1 2;
    }
    #seed-actions {
        dock: bottom;
        height: 3;
        padding: 0 1;
        layout: horizontal;
    }
    #seed-actions Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("q", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="seed-container"):
            with Vertical(id="seed-list-panel"):
                yield OptionList(id="seed-list")
            with Vertical(id="seed-detail-panel"):
                yield Static("Select a seed", id="seed-detail")
        with Horizontal(id="seed-actions"):
            yield Button("Back", variant="default", id="back-btn")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_seeds()
        self.app.title = "novo - Seeds"

    def _refresh_seeds(self) -> None:
        from novo.core.seed import list_seeds

        self._seeds = list_seeds()
        seed_list = self.query_one("#seed-list", OptionList)
        seed_list.clear_options()
        for seed in self._seeds:
            label = f"{'[built-in] ' if seed.builtin else ''}{seed.name}"
            seed_list.add_option(Option(label, id=seed.name))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_index < len(self._seeds):
            seed = self._seeds[event.option_index]
            detail = self.query_one("#seed-detail", Static)

            packages = ", ".join(seed.dependencies.packages) if seed.dependencies.packages else "none"
            detail.update(
                f"[b]{seed.name}[/]\n\n"
                f"[b]Description:[/] {seed.description or 'none'}\n"
                f"[b]Type:[/] {'built-in' if seed.builtin else 'user-installed'}\n"
                f"[b]Packages:[/] {packages}\n"
                f"[b]Path:[/] {seed.path}"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
