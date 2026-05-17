"""Minimal-mode screen shown when novo is launched in detached mode.

There is no workspace registry to browse, so this screen offers a handful
of direct actions: create an experiment in cwd, browse seeds, manage
remotes, or initialize the cwd as a workspace.
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
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

    BINDINGS = [
        ("n", "new_experiment", "New experiment here"),
        ("s", "browse_seeds", "Browse seeds"),
        ("l", "link_remote", "Link remote"),
        ("i", "init_workspace", "Init workspace here"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        cwd = Path.cwd().resolve()
        with VerticalScroll(id="detached-body"):
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
