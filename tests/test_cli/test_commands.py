"""Tests for CLI commands."""

from unittest.mock import patch

from typer.testing import CliRunner

from novo.cli import app

runner = CliRunner()


def test_shell_init():
    """--shell-init prints the shell function."""
    result = runner.invoke(app, ["--shell-init"])
    assert result.exit_code == 0
    assert "novo()" in result.output


@patch("novo.core.experiment.uv.uv_init")
def test_new_command(mock_uv, tmp_workspace):
    result = runner.invoke(app, ["new", "test-proj", "--no-date"])
    assert result.exit_code == 0
    assert "test-proj" in result.output


@patch("novo.core.experiment.uv.uv_init")
def test_list_command(mock_uv, tmp_workspace):
    runner.invoke(app, ["new", "list-test", "--no-date"])
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "list-test" in result.output


@patch("novo.core.experiment.uv.uv_init")
def test_info_command(mock_uv, tmp_workspace):
    runner.invoke(app, ["new", "info-test", "--no-date"])
    result = runner.invoke(app, ["info", "info-test"])
    assert result.exit_code == 0
    assert "info-test" in result.output


@patch("novo.core.experiment.uv.uv_init")
def test_search_command(mock_uv, tmp_workspace):
    runner.invoke(app, ["new", "searchable", "--no-date", "--desc", "finding things"])
    result = runner.invoke(app, ["search", "finding"])
    assert result.exit_code == 0
    assert "searchable" in result.output


@patch("novo.core.experiment.uv.uv_init")
def test_delete_command(mock_uv, tmp_workspace):
    runner.invoke(app, ["new", "delete-test", "--no-date"])
    result = runner.invoke(app, ["delete", "delete-test", "--force"])
    assert result.exit_code == 0
    assert "Deleted" in result.output


def test_info_workspace(tmp_workspace):
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "Workspace" in result.output


def test_init_with_path(tmp_workspace, tmp_path):
    target = tmp_path / "my-workspace"
    result = runner.invoke(app, ["init", str(target)])
    assert result.exit_code == 0
    assert target.exists()
    assert "Workspace initialized" in result.output


def test_init_default_cwd(tmp_workspace, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Workspace initialized" in result.output
    # Verify config was saved with cwd path
    get_result = runner.invoke(app, ["config", "get", "workspace.path"])
    assert str(tmp_path) in get_result.output


def test_config_show(tmp_workspace):
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "workspace.path" in result.output
    assert "defaults.seed" in result.output


def test_config_get(tmp_workspace):
    result = runner.invoke(app, ["config", "get", "defaults.seed"])
    assert result.exit_code == 0
    assert "default" in result.output


def test_config_get_unknown_key(tmp_workspace):
    result = runner.invoke(app, ["config", "get", "bad.key"])
    assert result.exit_code == 1
    assert "Unknown config key" in result.output


def test_config_set_string(tmp_workspace, tmp_path):
    target = str(tmp_path / "new-workspace")
    runner.invoke(app, ["config", "set", "workspace.path", target])
    result = runner.invoke(app, ["config", "get", "workspace.path"])
    assert result.exit_code == 0
    assert target in result.output


def test_config_set_bool(tmp_workspace):
    runner.invoke(app, ["config", "set", "defaults.auto_commit", "false"])
    result = runner.invoke(app, ["config", "get", "defaults.auto_commit"])
    assert result.exit_code == 0
    assert "False" in result.output


def test_config_set_bool_invalid(tmp_workspace):
    result = runner.invoke(app, ["config", "set", "defaults.auto_commit", "maybe"])
    assert result.exit_code == 1
    assert "Invalid value" in result.output


# --- seed init tests ---


def test_seed_init(tmp_workspace):
    result = runner.invoke(app, ["seed", "init", "my-seed"])
    assert result.exit_code == 0
    assert "my-seed" in result.output
    seed_dir = tmp_workspace.parent / "data" / "seeds" / "my-seed"
    assert seed_dir.exists()
    assert (seed_dir / "seed.toml").exists()
    assert (seed_dir / "template").is_dir()


def test_seed_init_with_description(tmp_workspace):
    result = runner.invoke(app, ["seed", "init", "desc-seed", "--desc", "A test seed"])
    assert result.exit_code == 0
    toml_content = (tmp_workspace.parent / "data" / "seeds" / "desc-seed" / "seed.toml").read_text()
    assert "A test seed" in toml_content


def test_seed_init_with_path(tmp_workspace, tmp_path):
    target = tmp_path / "custom-location"
    result = runner.invoke(app, ["seed", "init", "path-seed", "--path", str(target)])
    assert result.exit_code == 0
    assert (target / "seed.toml").exists()
    assert (target / "template").is_dir()


def test_seed_init_duplicate(tmp_workspace):
    runner.invoke(app, ["seed", "init", "dup-seed"])
    result = runner.invoke(app, ["seed", "init", "dup-seed"])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_seed_init_toml_content(tmp_workspace):
    runner.invoke(app, ["seed", "init", "toml-seed", "--desc", "Check content"])
    toml_path = tmp_workspace.parent / "data" / "seeds" / "toml-seed" / "seed.toml"
    content = toml_path.read_text()
    assert 'name = "toml-seed"' in content
    assert 'description = "Check content"' in content
    assert "# [seed.dependencies]" in content
    assert "# [seed.post_create]" in content
    assert "# [seed.files]" in content


def test_seed_init_visible_in_list(tmp_workspace):
    runner.invoke(app, ["seed", "init", "listed-seed", "--desc", "Should appear"])
    result = runner.invoke(app, ["seed", "list"])
    assert result.exit_code == 0
    assert "listed-seed" in result.output
