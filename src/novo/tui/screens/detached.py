"""Minimal-mode screen shown when novo is launched in detached mode.

There is no workspace registry to browse, so this screen offers a handful
of direct actions: create an experiment in cwd, browse seeds, manage
remotes, or initialize the cwd as a workspace.
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Static

from novo.tui.widgets.status_bar import StatusBar


class DetachedScreen(Screen):
    """Minimal mode for `novo --detached`."""

    DEFAULT_CSS = """
    DetachedScreen #detached-body {
        padding: 1 2;
        height: 1fr;
    }
    DetachedScreen #detached-actions Button {
        margin-bottom: 1;
        width: 100%;
    }
    DetachedScreen .info {
        color: $text-muted;
        margin-bottom: 1;
    }
    """

    # Order matters: this is the cycle order for up/down navigation.
    _BUTTON_IDS = ("btn-new", "btn-seeds", "btn-link", "btn-init")

    BINDINGS = [
        ("n", "new_experiment", "New experiment here"),
        ("s", "browse_seeds", "Browse seeds"),
        ("l", "link_remote", "Link remote"),
        ("i", "init_workspace", "Init workspace here"),
        # priority=True so arrow keys move focus between buttons regardless
        # of which widget currently holds focus. Use an explicit action that
        # cycles a known list of button IDs instead of relying on Textual's
        # focus_chain / action_focus_next — the chain-based fallback was
        # observed not to move focus in practice (likely because containers
        # in the tree shadowed the action), so this is the bulletproof path.
        Binding("up", "cycle_focus(-1)", "Up", show=False, priority=True),
        Binding("down", "cycle_focus(1)", "Down", show=False, priority=True),
        Binding("k", "cycle_focus(-1)", "Up", show=False, priority=True),
        Binding("j", "cycle_focus(1)", "Down", show=False, priority=True),
    ]

    def action_cycle_focus(self, direction: int) -> None:
        """Cycle focus through the action buttons in `_BUTTON_IDS` order."""
        ids = self._BUTTON_IDS
        focused = self.focused
        if focused is None or focused.id not in ids:
            target_id = ids[0] if direction > 0 else ids[-1]
        else:
            i = ids.index(focused.id)
            target_id = ids[(i + direction) % len(ids)]
        try:
            self.query_one(f"#{target_id}", Button).focus()
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Header()
        cwd = Path.cwd().resolve()
        # Use plain Vertical (not VerticalScroll) so the container does not
        # claim up/down for scrolling — those go to focus_previous/next.
        with Vertical(id="detached-body"):
            yield Static(f"[b]DETACHED[/]  [dim]{cwd}[/]", id="detached-title")
            yield Static(
                "No workspace was discovered. Pick an action below or run "
                "[cyan]novo init[/] to turn this directory into a workspace.",
                classes="info",
            )
            with Vertical(id="detached-actions"):
                yield Button("[b]N[/]ew experiment here", id="btn-new", variant="primary")
                yield Button("Browse [b]s[/]eeds", id="btn-seeds")
                yield Button("[b]L[/]ink remote registry", id="btn-link")
                yield Button("[b]I[/]nitialize workspace here", id="btn-init")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        status = self.query_one("#status-bar", StatusBar)
        status.set_mode(f"DETACHED — {Path.cwd().name}", detached=True)
        status.set_context("main")
        # Focus the primary button so arrows/Enter work without a prior Tab.
        try:
            self.query_one("#btn-new", Button).focus()
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        handler = {
            "btn-new": self.action_new_experiment,
            "btn-seeds": self.action_browse_seeds,
            "btn-link": self.action_link_remote,
            "btn-init": self.action_init_workspace,
        }.get(event.button.id)
        if handler is not None:
            handler()

    # --- actions ---

    def action_new_experiment(self) -> None:
        from novo.tui.screens.new_experiment import NewExperimentScreen

        self.app.push_screen(NewExperimentScreen())

    def action_browse_seeds(self) -> None:
        # No workspace registry in detached mode; route to the CLI listing.
        self.notify(
            "Detached mode has no workspace. Run [cyan]novo seed list[/] in "
            "your shell to browse, or [b]i[/]nitialize this folder first.",
            title="Browse seeds",
            timeout=8,
        )

    def action_link_remote(self) -> None:
        from novo.tui.screens.remote_link import RemoteLinkScreen

        self.app.push_screen(RemoteLinkScreen())

    def action_init_workspace(self) -> None:
        from novo.core.workspace import (
            ensure_initialized,
            set_detached_forced,
            set_workspace_override,
        )
        from novo.tui.screens.main import MainScreen

        cwd = Path.cwd().resolve()
        try:
            ensure_initialized(cwd)
        except Exception as err:  # noqa: BLE001
            self.notify(f"Init failed: {err}", severity="error")
            return

        # Switch into workspace mode and hand off to the main screen.
        set_detached_forced(False)
        set_workspace_override(cwd)
        self.notify(f"Initialized workspace at {cwd}")
        self.app.switch_screen(MainScreen())
