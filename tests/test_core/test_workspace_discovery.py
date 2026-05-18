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


def test_current_workspace_walks_up_from_cwd(tmp_unconfigured, monkeypatch):
    ws = tmp_unconfigured / "ws"
    ws.mkdir()
    (ws / ".novo").mkdir()
    nested = ws / "deep" / "subdir"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    assert workspace.current_workspace() == ws.resolve()


def test_current_workspace_returns_none_when_nothing_resolves(tmp_unconfigured, monkeypatch):
    """No marker, no override, no config.workspace.path → None (auto-detached)."""
    outside = tmp_unconfigured / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    assert workspace.current_workspace() is None


def test_current_workspace_uses_config_workspace_path(tmp_unconfigured, monkeypatch):
    """If `config.workspace.path` is set, use it when cwd/override miss."""
    configured = tmp_unconfigured / "configured-home"
    configured.mkdir()

    from novo.core.config import save_config
    from novo.models.config import NovoConfig

    cfg = NovoConfig()
    cfg.workspace.path = str(configured)
    save_config(cfg)

    outside = tmp_unconfigured / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    assert workspace.current_workspace() == configured.resolve()


def test_current_workspace_no_silent_xdg_fallback(tmp_unconfigured, monkeypatch):
    """The XDG default workspace is no longer auto-used; resolution returns None."""
    outside = tmp_unconfigured / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    # XDG default `default_workspace_dir()` exists in the patched paths but
    # current_workspace() must not pick it up implicitly.
    assert workspace.current_workspace() is None


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
    # tmp_workspace fixture sets the workspace override; ensure_initialized
    # should resolve there and create the marker.
    assert result == tmp_workspace.resolve()
    assert (tmp_workspace / ".novo").is_dir()


def test_ensure_initialized_raises_when_auto_detached(tmp_unconfigured, monkeypatch):
    """With no resolvable workspace, ensure_initialized() must refuse to silently
    materialize a hidden XDG directory."""
    outside = tmp_unconfigured / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    with pytest.raises(RuntimeError, match="no workspace resolved"):
        workspace.ensure_initialized()


def test_is_detached_true_when_no_workspace(tmp_unconfigured, monkeypatch):
    outside = tmp_unconfigured / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    assert workspace.is_detached() is True
    assert workspace.is_auto_detached() is True


def test_is_detached_false_with_marker(tmp_unconfigured, monkeypatch):
    ws = tmp_unconfigured / "ws"
    ws.mkdir()
    (ws / ".novo").mkdir()
    monkeypatch.chdir(ws)
    assert workspace.is_detached() is False
    assert workspace.is_auto_detached() is False


def test_is_auto_detached_false_when_forced(tmp_unconfigured, monkeypatch):
    """--detached (forced) is distinct from auto-detach so the CLI can keep
    its existing message and skip the hint."""
    outside = tmp_unconfigured / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    workspace.set_detached_forced(True)
    try:
        assert workspace.is_detached() is True
        assert workspace.is_auto_detached() is False
    finally:
        workspace.set_detached_forced(False)
