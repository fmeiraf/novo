"""Main screen with two-panel layout: experiment list + detail."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Static

from novo.tui.widgets.experiment_card import ExperimentCard
from novo.tui.widgets.experiment_list import ExperimentList
from novo.tui.widgets.search_bar import SearchBar
from novo.tui.widgets.status_bar import StatusBar


class MainScreen(Screen):
    """The main two-panel screen."""

    BINDINGS = [
        ("n", "new_experiment", "New"),
        ("d", "delete_experiment", "Delete"),
        ("s", "manage_seeds", "Seeds"),
        ("slash", "search", "Search"),
        ("question_mark", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield SearchBar(id="search-bar")
        with Horizontal(id="main-container"):
            with Vertical(id="experiment-list-panel"):
                yield ExperimentList(id="experiment-list")
            with Vertical(id="experiment-detail-panel"):
                yield ExperimentCard(id="experiment-card")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        self._refresh_experiments()

    def _refresh_experiments(self) -> None:
        """Load and display experiments."""
        from novo.core.experiment import list_all

        experiments = list_all()
        exp_list = self.query_one("#experiment-list", ExperimentList)
        exp_list.set_experiments(experiments)

        # Update header
        self.app.title = f"novo - {len(experiments)} experiments"

        # Show welcome screen when no experiments exist
        if not experiments:
            card = self.query_one("#experiment-card", ExperimentCard)
            card.show_welcome()

    def on_experiment_list_selected(self, event: ExperimentList.Selected) -> None:
        """Update detail panel when selection changes."""
        card = self.query_one("#experiment-card", ExperimentCard)
        card.update_experiment(event.experiment)

    def on_experiment_list_activated(self, event: ExperimentList.Activated) -> None:
        """Open a new terminal window at the experiment directory."""
        from novo.core.experiment import get_path
        from novo.utils.terminal import open_terminal_at

        path = get_path(event.experiment.name)
        if path:
            open_terminal_at(path)
            self.notify(f"Opened terminal at {path.name}")

    def on_search_bar_changed(self, event: SearchBar.Changed) -> None:
        """Filter experiment list based on search input."""
        exp_list = self.query_one("#experiment-list", ExperimentList)
        exp_list.filter(event.query)

    def action_search(self) -> None:
        """Focus the search bar."""
        search = self.query_one("#search-bar", SearchBar)
        search.focus_input()
        status = self.query_one("#status-bar", StatusBar)
        status.set_context("search")

    def action_new_experiment(self) -> None:
        """Show the new experiment modal."""
        from novo.tui.screens.new_experiment import NewExperimentScreen

        self.app.push_screen(NewExperimentScreen(), callback=self._on_experiment_created)

    def _on_experiment_created(self, result: bool) -> None:
        """Callback after new experiment screen."""
        if result:
            self._refresh_experiments()

    def action_delete_experiment(self) -> None:
        """Delete the selected experiment."""
        exp_list = self.query_one("#experiment-list", ExperimentList)
        exp = exp_list.get_selected_experiment()
        if exp is None:
            return

        from novo.tui.screens.confirm import ConfirmScreen

        self.app.push_screen(
            ConfirmScreen(f"Delete experiment '{exp.name}'?"),
            callback=lambda confirmed: self._on_delete_confirmed(confirmed, exp.name),
        )

    def _on_delete_confirmed(self, confirmed: bool, name: str) -> None:
        """Callback after delete confirmation."""
        if confirmed:
            from novo.core.experiment import delete

            delete(name)
            self._refresh_experiments()

    def action_manage_seeds(self) -> None:
        """Open the seed manager."""
        from novo.tui.screens.seed_manager import SeedManagerScreen

        self.app.push_screen(SeedManagerScreen())

    def action_help(self) -> None:
        """Show help information."""
        self.notify(
            "[b]n[/]ew  [b]enter[/] open  [b]d[/]elete  [b]s[/]eeds  [b]/[/]search  [b]q[/]uit\n"
            "[b]j/k[/] navigate  [b]?[/] this help",
            title="Keybindings",
            timeout=5,
        )
