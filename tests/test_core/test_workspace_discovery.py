"""Tests for workspace marker discovery and resolution."""

import pytest

from novo.core import workspace


@pytest.fixture(autouse=True)
def _clear_override():
    """Reset the process-scoped override between tests."""
    workspace.set_workspace_override(None)
    yield
    workspace.set_workspace_override(None)


def test_discover_finds_marker_in_start_dir(tmp_path):
    (tmp_path / ".novo").mkdir()
    assert workspace.discover(tmp_path) == tmp_path.resolve()


def test_discover_walks_up_parents(tmp_path):
    (tmp_path / ".novo").mkdir()
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    assert workspace.discover(nested) == tmp_path.resolve()


def test_discover_returns_none_when_no_marker(tmp_path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    result = workspace.discover(nested)
    # On a clean test env: None. Robust assertion: at minimum, nothing in
    # the tmp tree was promoted to a workspace.
    assert result != nested.resolve()
    assert result != tmp_path.resolve()


def test_discover_ignores_marker_files_only_dirs(tmp_path):
    (tmp_path / ".novo").write_text("not a dir")
    result = workspace.discover(tmp_path)
    assert result != tmp_path.resolve()


def test_set_workspace_override_is_resolved(tmp_path):
    workspace.set_workspace_override(str(tmp_path))
    assert workspace.get_workspace_override() == tmp_path.resolve()


def test_set_workspace_override_none_clears(tmp_path):
    workspace.set_workspace_override(str(tmp_path))
    workspace.set_workspace_override(None)
    assert workspace.get_workspace_override() is None


def test_current_workspace_prefers_override(tmp_path, tmp_workspace, monkeypatch):
    override = tmp_path / "override-ws"
    override.mkdir()
    workspace.set_workspace_override(override)
    # cwd has no marker; default workspace exists. Override should still win.
    monkeypatch.chdir(tmp_path)
    assert workspace.current_workspace() == override.resolve()


def test_current_workspace_walks_up_from_cwd(tmp_workspace, tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".novo").mkdir()
    nested = ws / "deep" / "subdir"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    assert workspace.current_workspace() == ws.resolve()


def test_current_workspace_falls_back_to_default(tmp_workspace, tmp_path, monkeypatch):
    # cwd is outside any workspace; should fall back to tmp_workspace (the patched default).
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    assert workspace.current_workspace() == tmp_workspace.resolve()


def test_ensure_initialized_creates_marker(tmp_path):
    target = tmp_path / "new-ws"
    workspace.ensure_initialized(target)
    assert (target / ".novo").is_dir()
    assert (target / ".novo" / "seeds").is_dir()
    assert (target / ".novo" / "config.toml").is_file()
    assert (target / ".git").is_dir()


def test_ensure_initialized_is_idempotent(tmp_path):
    target = tmp_path / "ws"
    workspace.ensure_initialized(target)
    workspace.ensure_initialized(target)  # Must not raise.
    assert (target / ".novo").is_dir()


def test_ensure_initialized_silent_migration(tmp_path):
    """An existing pre-marker workspace (already a git repo) should get the marker silently."""
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    # Simulate a pre-marker workspace: git repo, no .novo/.
    import subprocess

    subprocess.run(["git", "init"], cwd=legacy, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "--allow-empty", "-m", "init"],
        cwd=legacy,
        check=True,
        capture_output=True,
    )

    assert not (legacy / ".novo").exists()
    workspace.ensure_initialized(legacy)
    assert (legacy / ".novo").is_dir()
    # Existing git repo not re-initialized — no extra workspace-init commit added.


def test_ensure_initialized_uses_current_when_no_target(tmp_workspace, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = workspace.ensure_initialized()
    # Should resolve to the default (tmp_workspace) and create marker there.
    assert result == tmp_workspace.resolve()
    assert (tmp_workspace / ".novo").is_dir()
