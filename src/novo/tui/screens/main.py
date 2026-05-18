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

from novo.models.scoped_seed import ScopedSeed
from novo.tui.widgets.experiment_card import ExperimentCard
from novo.tui.widgets.experiment_list import ExperimentList
from novo.tui.widgets.file_preview import FilePreview
from novo.tui.widgets.file_tree import FilteredDirectoryTree
from novo.tui.widgets.search_bar import SearchBar
from novo.tui.widgets.seed_picker import build_picker_rows
from novo.tui.widgets.status_bar import StatusBar


_SCOPE_LABEL = {
    "local": "workspace",
    "user": "user-installed",
    "remote": "remote",
    "builtin": "built-in",
}


def _format_seed_detail(scoped: ScopedSeed) -> str:
    """Format the seed metadata block as Rich-markup text."""
    seed = scoped.seed
    packages = ", ".join(seed.dependencies.packages) or "none"
    excludes = ", ".join(seed.files.exclude) or "none"

    type_label = _SCOPE_LABEL.get(scoped.scope, scoped.scope)
    if scoped.scope == "remote" and scoped.remote:
        type_label = f"remote ({scoped.remote})"

    lines = [
        f"[b]{seed.name}[/]",
        "",
        f"[b]Identifier:[/] [cyan]{scoped.identifier}[/]",
        f"[b]Description:[/] {seed.description or 'none'}",
        f"[b]Type:[/] {type_label}",
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
        # Seeds-tab actions (no-op elsewhere).
        ("N", "new_seed", "New seed"),
        ("l", "link_remote", "Link remote"),
        ("u", "unlink_remote", "Unlink remote"),
        ("r", "sync_remotes", "Sync remotes"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._seeds: list = []
        self._seeds_by_id: dict[str, ScopedSeed] = {}

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
        self._update_mode_chip()

    def _update_mode_chip(self) -> None:
        from novo.core.workspace import current_workspace

        try:
            workspace = current_workspace()
            status = self.query_one("#status-bar", StatusBar)
            status.set_mode(f"WORKSPACE: {workspace.name}", detached=False)
        except Exception:
            pass

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
        from novo.core.config import load_config
        from novo.core.seed import list_seeds, resolve_seed

        self._seeds = list_seeds()
        self._seeds_by_id = {s.identifier: s for s in self._seeds}

        default_id: str | None = None
        try:
            default_id = resolve_seed(load_config().defaults.seed).identifier
        except ValueError:
            default_id = None

        rows = build_picker_rows(self._seeds, default_identifier=default_id, compact=True)

        seed_list = self.query_one("#seed-list", OptionList)
        seed_list.clear_options()
        for row in rows:
            seed_list.add_option(Option(row.label, id=row.id, disabled=row.disabled))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id != "seed-list":
            return

        opt = event.option
        if opt is None or opt.disabled or opt.id is None:
            return

        scoped = self._seeds_by_id.get(opt.id)
        if scoped is None:
            return

        detail = self.query_one("#seed-detail", Static)
        detail.update(_format_seed_detail(scoped))

        template_dir = Path(scoped.seed.path) / "template"
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
        self.query_one("#status-bar", StatusBar).set_context("seeds")

    @on(TabbedContent.TabActivated)
    def _on_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        status = self.query_one("#status-bar", StatusBar)
        if event.pane.id == "tab-seeds":
            status.set_context("seeds")
        else:
            status.set_context("main")

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
            "Seeds tab: [b]N[/]ew seed  [b]l[/]ink remote  [b]u[/]nlink  "
            "[b]r[/] sync (highlighted remote, or all)  "
            "[b]t[/] focus tree  [b]l/enter[/] expand",
            title="Keybindings",
            timeout=8,
        )

    # ---- Seeds-tab actions (no-ops outside the seeds tab) ----

    def action_link_remote(self) -> None:
        if self._active_tab() != "tab-seeds":
            return
        from novo.tui.screens.remote_link import RemoteLinkScreen

        self.app.push_screen(RemoteLinkScreen(), callback=self._on_remote_linked)

    def _on_remote_linked(self, ok: bool) -> None:
        if not ok:
            return
        self._refresh_seeds()
        self._run_sync(None)

    def action_unlink_remote(self) -> None:
        if self._active_tab() != "tab-seeds":
            return

        seed_list = self.query_one("#seed-list", OptionList)
        if seed_list.highlighted is None:
            self.notify("Highlight a remote seed first", severity="warning")
            return
        try:
            opt = seed_list.get_option_at_index(seed_list.highlighted)
        except IndexError:
            return
        if opt is None or opt.disabled or opt.id is None:
            return
        scoped = self._seeds_by_id.get(opt.id)
        if scoped is None or scoped.scope != "remote" or not scoped.remote:
            self.notify("Pick a remote seed to unlink its registry", severity="warning")
            return

        remote_name = scoped.remote
        from novo.tui.screens.confirm import ConfirmScreen

        self.app.push_screen(
            ConfirmScreen(f"Unlink remote '{remote_name}' (drops all its seeds)?"),
            callback=lambda ok: self._on_unlink_confirmed(ok, remote_name),
        )

    def _on_unlink_confirmed(self, confirmed: bool, name: str) -> None:
        if not confirmed:
            return
        from novo.core.seed import unlink_remote

        if unlink_remote(name):
            self.notify(f"Unlinked remote: {name}")
            self._refresh_seeds()
        else:
            self.notify(f"Unknown remote: {name}", severity="error")

    def action_sync_remotes(self) -> None:
        if self._active_tab() != "tab-seeds":
            return
        self._run_sync(self._highlighted_remote_name())

    def _highlighted_remote_name(self) -> str | None:
        """Registry name of the highlighted remote seed, or None for everything else."""
        try:
            seed_list = self.query_one("#seed-list", OptionList)
        except Exception:
            return None
        if seed_list.highlighted is None:
            return None
        try:
            opt = seed_list.get_option_at_index(seed_list.highlighted)
        except IndexError:
            return None
        if opt is None or opt.disabled or opt.id is None:
            return None
        scoped = self._seeds_by_id.get(opt.id)
        if scoped is None or scoped.scope != "remote":
            return None
        return scoped.remote

    def _run_sync(self, name: str | None) -> None:
        from novo.core.seed import sync_remote

        try:
            results = sync_remote(name)
        except ValueError as err:
            self.notify(str(err), severity="error")
            return

        if not results:
            self.notify("No linked remotes — press l to link one", severity="information")
            self.query_one("#status-bar", StatusBar).set_sync_note(None)
            return

        ok_count = sum(1 for _, ok, _ in results if ok)
        summary = " · ".join(f"{n} {'✓' if ok else '⚠'}" for n, ok, _ in results)
        self.query_one("#status-bar", StatusBar).set_sync_note(
            f"sync: {ok_count}/{len(results)}  {summary}"
        )
        if ok_count == len(results):
            self.notify(f"Synced {ok_count} remote{'s' if ok_count != 1 else ''}")
        else:
            failures = [f"{n}: {msg}" for n, ok, msg in results if not ok]
            self.notify("\n".join(failures), severity="error", title="Sync failures")
        self._refresh_seeds()

    def action_new_seed(self) -> None:
        if self._active_tab() != "tab-seeds":
            return
        from novo.tui.screens.new_seed import NewSeedScreen

        self.app.push_screen(NewSeedScreen(), callback=self._on_seed_created)

    def _on_seed_created(self, ok: bool) -> None:
        if ok:
            self._refresh_seeds()
