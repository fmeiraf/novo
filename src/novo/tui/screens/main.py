"""Main screen with tabbed navigation: experiments + seeds."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, OptionList, Static, TabbedContent, TabPane
from textual.widgets.option_list import Option

from novo.tui.widgets.experiment_card import ExperimentCard
from novo.tui.widgets.experiment_list import ExperimentList
from novo.tui.widgets.file_tree import FileTreeWidget
from novo.tui.widgets.search_bar import SearchBar
from novo.tui.widgets.status_bar import StatusBar


class MainScreen(Screen):
    """The main screen — tabbed view over experiments and seeds."""

    BINDINGS = [
        ("n", "new_experiment", "New"),
        ("d", "delete_experiment", "Delete"),
        ("e", "show_experiments", "Experiments"),
        ("s", "show_seeds", "Seeds"),
        ("slash", "search", "Search"),
        ("question_mark", "help", "Help"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._seeds: list = []

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="tab-experiments", id="main-tabs"):
            with TabPane("Experiments", id="tab-experiments"):
                yield SearchBar(id="search-bar")
                with Horizontal(id="main-container"):
                    with Vertical(id="experiment-list-panel"):
                        yield ExperimentList(id="experiment-list")
                    with Vertical(id="experiment-detail-panel"):
                        yield ExperimentCard(id="experiment-card")
            with TabPane("Seeds", id="tab-seeds"):
                with Horizontal(id="seed-container"):
                    with Vertical(id="seed-list-panel"):
                        yield OptionList(id="seed-list")
                    with VerticalScroll(id="seed-detail-panel"):
                        yield Static("Select a seed", id="seed-detail")
                        yield Static("", id="seed-template-header")
                        yield FileTreeWidget(id="seed-template-tree")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        self._refresh_experiments()
        self._refresh_seeds()

    # ---- Experiments tab ----

    def _refresh_experiments(self) -> None:
        from novo.core.experiment import list_all

        experiments = list_all()
        exp_list = self.query_one("#experiment-list", ExperimentList)
        exp_list.set_experiments(experiments)

        self.app.title = f"novo - {len(experiments)} experiments"

        if not experiments:
            card = self.query_one("#experiment-card", ExperimentCard)
            card.show_welcome()

    def on_experiment_list_selected(self, event: ExperimentList.Selected) -> None:
        card = self.query_one("#experiment-card", ExperimentCard)
        card.update_experiment(event.experiment)

    def on_experiment_list_activated(self, event: ExperimentList.Activated) -> None:
        from novo.core.experiment import get_path
        from novo.utils.terminal import open_terminal_at

        path = get_path(event.experiment.name)
        if path:
            open_terminal_at(path)
            self.notify(f"Opened terminal at {path.name}")

    def on_search_bar_changed(self, event: SearchBar.Changed) -> None:
        exp_list = self.query_one("#experiment-list", ExperimentList)
        exp_list.filter(event.query)

    # ---- Seeds tab ----

    def _refresh_seeds(self) -> None:
        from novo.core.seed import list_seeds

        self._seeds = list_seeds()
        seed_list = self.query_one("#seed-list", OptionList)
        seed_list.clear_options()
        for seed in self._seeds:
            label = f"{'[built-in] ' if seed.builtin else ''}{seed.name}"
            seed_list.add_option(Option(label, id=seed.name))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id != "seed-list":
            return
        if event.option_index >= len(self._seeds):
            return

        seed = self._seeds[event.option_index]
        detail = self.query_one("#seed-detail", Static)
        header = self.query_one("#seed-template-header", Static)
        tree = self.query_one("#seed-template-tree", FileTreeWidget)

        packages = ", ".join(seed.dependencies.packages) if seed.dependencies.packages else "none"
        detail.update(
            f"[b]{seed.name}[/]\n\n"
            f"[b]Description:[/] {seed.description or 'none'}\n"
            f"[b]Type:[/] {'built-in' if seed.builtin else 'user-installed'}\n"
            f"[b]Packages:[/] {packages}\n"
            f"[b]Path:[/] {seed.path}"
        )

        template_dir = Path(seed.path) / "template"
        if template_dir.is_dir():
            header.update("TEMPLATE")
            tree.show_path(template_dir)
        else:
            header.update("")
            tree.clear()

    # ---- Tab switching ----

    def _active_tab(self) -> str:
        return self.query_one(TabbedContent).active

    def action_show_experiments(self) -> None:
        self.query_one(TabbedContent).active = "tab-experiments"

    def action_show_seeds(self) -> None:
        self.query_one(TabbedContent).active = "tab-seeds"

    # ---- Actions ----

    def action_search(self) -> None:
        self.action_show_experiments()
        search = self.query_one("#search-bar", SearchBar)
        search.focus_input()
        status = self.query_one("#status-bar", StatusBar)
        status.set_context("search")

    def action_new_experiment(self) -> None:
        from novo.tui.screens.new_experiment import NewExperimentScreen

        self.action_show_experiments()
        self.app.push_screen(NewExperimentScreen(), callback=self._on_experiment_created)

    def _on_experiment_created(self, result: bool) -> None:
        if result:
            self._refresh_experiments()

    def action_delete_experiment(self) -> None:
        if self._active_tab() != "tab-experiments":
            return

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
        if confirmed:
            from novo.core.experiment import delete

            delete(name)
            self._refresh_experiments()

    def action_help(self) -> None:
        self.notify(
            "[b]e[/]xperiments  [b]s[/]eeds  [b]n[/]ew  [b]enter[/] open  "
            "[b]d[/]elete  [b]/[/]search  [b]q[/]uit\n"
            "[b]j/k[/] navigate  [b]?[/] this help",
            title="Keybindings",
            timeout=5,
        )
