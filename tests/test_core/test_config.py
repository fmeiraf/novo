"""Tests for config module."""

from novo.core.config import load_config, save_config
from novo.models.config import NovoConfig


def test_load_default_config(tmp_workspace):
    """Loading config when no file exists returns defaults."""
    config = load_config()
    assert config.defaults.seed == "default"
    assert config.naming.date_prefix is True
    assert config.workspace.path == ""


def test_save_and_load_config(tmp_workspace):
    """Saving and loading config roundtrips correctly."""
    config = NovoConfig()
    config.defaults.seed = "custom"
    config.defaults.python = "3.12"
    save_config(config)

    loaded = load_config()
    assert loaded.defaults.seed == "custom"
    assert loaded.defaults.python == "3.12"
