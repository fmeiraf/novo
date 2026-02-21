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
