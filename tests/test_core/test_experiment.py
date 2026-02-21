"""Tests for experiment module."""

import subprocess
from unittest.mock import patch

import pytest

from novo.core.experiment import (
    _make_dir_name,
    _read_novo_toml,
    _write_novo_toml,
    create,
    delete,
    get,
    list_all,
    search,
)
from novo.models.experiment import Experiment


def test_make_dir_name_with_date():
    name = _make_dir_name("test", use_date_prefix=True)
    # Should be YYYY-MM-DD-test
    assert name.endswith("-test")
    assert len(name.split("-")) >= 4  # date parts + name


def test_make_dir_name_without_date():
    name = _make_dir_name("test", use_date_prefix=False)
    assert name == "test"


def test_write_and_read_novo_toml(tmp_path):
    exp = Experiment(name="test", seed="default", tags=["web"], description="A test")
    _write_novo_toml(tmp_path, exp)

    loaded = _read_novo_toml(tmp_path)
    assert loaded is not None
    assert loaded.name == "test"
    assert loaded.seed == "default"
    assert loaded.tags == ["web"]


@patch("novo.core.experiment.uv.uv_init")
def test_create_experiment(mock_uv_init, tmp_workspace):
    exp = create(name="test-exp", no_date=True)

    assert exp.name == "test-exp"
    assert exp.dir_name == "test-exp"
    assert (tmp_workspace / "test-exp" / ".novo.toml").exists()
    mock_uv_init.assert_called_once()


@patch("novo.core.experiment.uv.uv_init")
def test_create_duplicate_fails(mock_uv_init, tmp_workspace):
    create(name="dup-test", no_date=True)
    with pytest.raises(FileExistsError):
        create(name="dup-test", no_date=True)


@patch("novo.core.experiment.uv.uv_init")
def test_list_all(mock_uv_init, tmp_workspace):
    create(name="exp-a", no_date=True)
    create(name="exp-b", no_date=True)

    experiments = list_all()
    names = [e.name for e in experiments]
    assert "exp-a" in names
    assert "exp-b" in names


@patch("novo.core.experiment.uv.uv_init")
def test_get_experiment(mock_uv_init, tmp_workspace):
    create(name="find-me", no_date=True)

    exp = get("find-me")
    assert exp is not None
    assert exp.name == "find-me"


@patch("novo.core.experiment.uv.uv_init")
def test_search_experiments(mock_uv_init, tmp_workspace):
    create(name="web-app", description="A web application", tags=["web"], no_date=True)
    create(name="ml-model", description="Machine learning", tags=["ml"], no_date=True)

    results = search("web")
    assert len(results) >= 1
    assert results[0].name == "web-app"


@patch("novo.core.experiment.uv.uv_init")
def test_delete_experiment(mock_uv_init, tmp_workspace):
    create(name="delete-me", no_date=True)
    assert get("delete-me") is not None

    result = delete("delete-me")
    assert result is True
