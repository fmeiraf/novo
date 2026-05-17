"""Smoke tests: every TUI screen module imports cleanly and instantiates."""


def test_detached_screen_importable():
    from novo.tui.screens.detached import DetachedScreen

    assert DetachedScreen is not None


def test_remote_link_screen_importable():
    from novo.tui.screens.remote_link import RemoteLinkScreen

    assert RemoteLinkScreen is not None


def test_new_seed_screen_importable():
    from novo.tui.screens.new_seed import NewSeedScreen

    assert NewSeedScreen is not None


def test_app_dispatches_detached_when_flag_set(tmp_workspace):
    """NovoApp.on_mount must select DetachedScreen iff is_detached_forced()."""
    from unittest.mock import MagicMock, patch

    from novo.core.workspace import set_detached_forced
    from novo.tui.app import NovoApp
    from novo.tui.screens.detached import DetachedScreen
    from novo.tui.screens.main import MainScreen

    app = NovoApp()
    pushed = []

    def fake_push(screen):
        pushed.append(screen)

    # `register_theme` / `theme` writes require an active app context; stub
    # them out to focus the test on the screen-selection branch.
    with patch.object(NovoApp, "register_theme", MagicMock()):
        with patch.object(NovoApp, "push_screen", side_effect=fake_push):
            app.__class__.theme = property(lambda self: "novo-dark", lambda s, v: None)

            set_detached_forced(False)
            app.on_mount()
            assert isinstance(pushed[-1], MainScreen)

            set_detached_forced(True)
            app.on_mount()
            assert isinstance(pushed[-1], DetachedScreen)
            set_detached_forced(False)
