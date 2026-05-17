"""Tests for the StatusBar mode chip + context switching."""

from novo.tui.widgets.status_bar import StatusBar


def test_status_bar_default_text_contains_bindings():
    bar = StatusBar()
    assert "experiments" in bar.compose_text()
    assert "seeds" in bar.compose_text()


def test_status_bar_set_mode_workspace_prefix():
    bar = StatusBar()
    bar.set_mode("WORKSPACE: foo", detached=False)
    assert "WORKSPACE: foo" in bar.compose_text()


def test_status_bar_set_mode_detached_prefix():
    bar = StatusBar()
    bar.set_mode("DETACHED", detached=True)
    assert "DETACHED" in bar.compose_text()


def test_status_bar_seeds_context_lists_remote_actions():
    bar = StatusBar()
    bar.set_context("seeds")
    rendered = bar.compose_text()
    assert "link" in rendered
    assert "unlink" in rendered
    assert "sync" in rendered
    assert "new seed" in rendered


def test_status_bar_sync_note_appears_in_render():
    bar = StatusBar()
    bar.set_sync_note("team ✓ ok")
    assert "team" in bar.compose_text()


def test_status_bar_clears_sync_note():
    bar = StatusBar()
    bar.set_sync_note("noisy")
    bar.set_sync_note(None)
    assert "noisy" not in bar.compose_text()
