"""Shared test fixtures."""

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _reset_workspace_override():
    """Workspace override + detached flag are process-scoped; reset between tests."""
    from novo.core.workspace import set_detached_forced, set_workspace_override

    set_workspace_override(None)
    set_detached_forced(False)
    yield
    set_workspace_override(None)
    set_detached_forced(False)


@pytest.fixture
def tmp_workspace(tmp_path, monkeypatch):
    """Create a temporary workspace for testing.

    Routes every `novo` invocation in the test at this workspace via the
    `NOVO_WORKSPACE` env var. Per-invocation `--workspace` flags or `env=`
    overrides on `runner.invoke` still take precedence, matching real usage.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    config_dir = tmp_path / "config"
    config_dir.mkdir()

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Patch paths to use temp directories
    monkeypatch.setattr("novo.utils.paths.config_dir", lambda: config_dir)
    monkeypatch.setattr("novo.utils.paths.data_dir", lambda: data_dir)
    monkeypatch.setattr("novo.utils.paths.config_file", lambda: config_dir / "config.toml")
    monkeypatch.setattr("novo.utils.paths.default_workspace_dir", lambda: workspace)
    monkeypatch.setattr("novo.utils.paths.seeds_dir", lambda: data_dir / "seeds")
    monkeypatch.setattr("novo.core.seed.seeds_dir", lambda: data_dir / "seeds")
    monkeypatch.setattr("novo.utils.paths.remotes_dir", lambda: data_dir / "remotes")
    monkeypatch.setattr("novo.core.seed.remotes_dir", lambda: data_dir / "remotes")

    # Stand in for the old silent XDG fallback: tell novo which workspace to use.
    # Set both the env var (consumed by the CLI callback) and the process-scoped
    # override (consumed by direct core calls in unit tests).
    from novo.core.workspace import set_workspace_override

    monkeypatch.setenv("NOVO_WORKSPACE", str(workspace))
    set_workspace_override(workspace)

    return workspace


@pytest.fixture
def tmp_unconfigured(tmp_path, monkeypatch):
    """Like `tmp_workspace` but leaves novo unconfigured.

    Useful for auto-detach tests: no workspace marker discoverable from cwd,
    no `workspace.path` set, no `NOVO_WORKSPACE` env. Yields the temp path
    you can `chdir` into.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    default_ws = tmp_path / "unused-default-workspace"

    monkeypatch.setattr("novo.utils.paths.config_dir", lambda: config_dir)
    monkeypatch.setattr("novo.utils.paths.data_dir", lambda: data_dir)
    monkeypatch.setattr("novo.utils.paths.config_file", lambda: config_dir / "config.toml")
    monkeypatch.setattr("novo.utils.paths.default_workspace_dir", lambda: default_ws)
    monkeypatch.setattr("novo.utils.paths.seeds_dir", lambda: data_dir / "seeds")
    monkeypatch.setattr("novo.core.seed.seeds_dir", lambda: data_dir / "seeds")
    monkeypatch.setattr("novo.utils.paths.remotes_dir", lambda: data_dir / "remotes")
    monkeypatch.setattr("novo.core.seed.remotes_dir", lambda: data_dir / "remotes")
    monkeypatch.delenv("NOVO_WORKSPACE", raising=False)

    return tmp_path


@pytest.fixture
def tmp_config(tmp_workspace, tmp_path):
    """Create a temporary config."""
    from novo.models.config import NovoConfig

    config = NovoConfig()
    config.workspace.path = str(tmp_workspace)
    return config
