"""Main screen with tabbed navigation: experiments + seeds."""

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    DirectoryTree,
    Header,
    OptionList,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)
from textual.widgets.option_list import Option

from novo.models.seed import Seed
from novo.tui.widgets.experiment_card import ExperimentCard
from novo.tui.widgets.experiment_list import ExperimentList
from novo.tui.widgets.file_preview import FilePreview
from novo.tui.widgets.file_tree import FilteredDirectoryTree
from novo.tui.widgets.search_bar import SearchBar
from novo.tui.widgets.status_bar import StatusBar


def _format_seed_detail(seed: Seed) -> str:
    """Format the seed metadata block as Rich-markup text."""
    packages = ", ".join(seed.dependencies.packages) or "none"
    excludes = ", ".join(seed.files.exclude) or "none"

    lines = [
        f"[b]{seed.name}[/]",
        "",
        f"[b]Description:[/] {seed.description or 'none'}",
        f"[b]Type:[/] {'built-in' if seed.builtin else 'user-installed'}",
        f"[b]Packages:[/] {packages}",
        f"[b]Excludes:[/] {excludes}",
    ]

    if seed.post_create.commands:
        lines.append("")
        lines.append("[b]Post-create:[/]")
        for cmd in seed.post_create.commands:
            lines.append(f"  [dim]$[/] {cmd}")
    else:
        lines.append("[b]Post-create:[/] none")

    lines.append("")
    lines.append(f"[b]Path:[/] [dim]{seed.path}[/]")

    return "\n".join(lines)


class MainScreen(Screen):
    """The main screen — tabbed view over experiments and seeds."""

    BINDINGS = [
        ("n", "new_experiment", "New"),
        ("d", "delete_experiment", "Delete"),
        ("e", "show_experiments", "Experiments"),
        ("s", "show_seeds", "Seeds"),
        ("t", "focus_seed_tree", "Focus tree"),
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
                    with Vertical(id="seed-detail-panel"):
                        with VerticalScroll(id="seed-meta-pane"):
                            yield Static("Select a seed", id="seed-detail")
                        yield Static("TEMPLATE", id="seed-template-header")
                        yield Vertical(id="seed-tree-mount")
                        yield Static("PREVIEW", id="seed-preview-header")
                        with VerticalScroll(id="seed-preview-pane"):
                            yield FilePreview(id="seed-preview")
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

        detail.update(_format_seed_detail(seed))

        template_dir = Path(seed.path) / "template"
        self._mount_seed_tree(template_dir if template_dir.is_dir() else None)

        preview = self.query_one("#seed-preview", FilePreview)
        preview.clear()

    def _mount_seed_tree(self, path: Path | None) -> None:
        mount = self.query_one("#seed-tree-mount", Vertical)
        for child in list(mount.children):
            child.remove()
        header = self.query_one("#seed-template-header", Static)
        if path is None:
            header.update("")
            return
        header.update("TEMPLATE  [dim](t to focus, j/k navigate, l/enter expand)[/]")
        tree = FilteredDirectoryTree(path, id="seed-tree")
        mount.mount(tree)
        self.call_after_refresh(tree.root.expand)

    @on(Tree.NodeHighlighted, "#seed-tree")
    def _on_seed_tree_highlight(self, event: Tree.NodeHighlighted) -> None:
        self._preview_tree_node(event.node.data)

    @on(DirectoryTree.FileSelected, "#seed-tree")
    def _on_seed_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        preview = self.query_one("#seed-preview", FilePreview)
        preview.show_path(event.path)

    def _preview_tree_node(self, data) -> None:
        preview = self.query_one("#seed-preview", FilePreview)
        if data is None:
            preview.clear()
            return
        path = Path(data.path)
        if path.is_file():
            preview.show_path(path)
        else:
            preview.clear()

    # ---- Tab switching ----

    def _active_tab(self) -> str:
        return self.query_one(TabbedContent).active

    def action_show_experiments(self) -> None:
        self.query_one(TabbedContent).active = "tab-experiments"

    def action_show_seeds(self) -> None:
        self.query_one(TabbedContent).active = "tab-seeds"

    def action_focus_seed_tree(self) -> None:
        if self._active_tab() != "tab-seeds":
            return
        try:
            tree = self.query_one("#seed-tree")
        except Exception:
            return
        tree.focus()

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
            "Seeds tab: [b]t[/] focus file tree, [b]l/enter[/] expand, [b]j/k[/] navigate",
            title="Keybindings",
            timeout=6,
        )
