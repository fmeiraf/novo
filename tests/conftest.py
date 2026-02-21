"""Shared test fixtures."""

import os
from pathlib import Path

import pytest


@pytest.fixture
def tmp_workspace(tmp_path, monkeypatch):
    """Create a temporary workspace for testing."""
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

    return workspace


@pytest.fixture
def tmp_config(tmp_workspace, tmp_path):
    """Create a temporary config."""
    from novo.models.config import NovoConfig

    config = NovoConfig()
    config.workspace.path = str(tmp_workspace)
    return config
