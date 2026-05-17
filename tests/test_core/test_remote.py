"""Tests for the remote seed sync flow (link / sync / unlink / list_remotes)."""

import subprocess
from pathlib import Path

import pytest

from novo.core import seed as seed_core


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _make_seed_dir(parent: Path, name: str, description: str = "") -> Path:
    seed = parent / name
    seed.mkdir()
    (seed / "template").mkdir()
    (seed / "seed.toml").write_text(
        f'[seed]\nname = "{name}"\ndescription = "{description}"\n'
    )
    return seed


def _make_origin(path: Path, seeds: dict[str, str]) -> Path:
    """Build a local git repo containing each seed as a subdir; usable as a clone URL."""
    path.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    for name, desc in seeds.items():
        _make_seed_dir(path, name, desc)
    _git(["add", "."], cwd=path)
    _git(["commit", "-m", "seed registry"], cwd=path)
    return path


# --- link_remote ---


def test_link_remote_clones_and_persists_config(tmp_workspace, tmp_path):
    origin = _make_origin(tmp_path / "origin", {"etl": "extract", "ml": "train"})

    remote = seed_core.link_remote(str(origin), name="team")
    assert remote.name == "team"
    assert remote.url == str(origin)

    # Clone exists under remotes_dir/team.
    cloned = tmp_workspace.parent / "data" / "remotes" / "team"
    assert (cloned / "etl" / "seed.toml").is_file()
    assert (cloned / "ml" / "seed.toml").is_file()

    # Config got persisted.
    from novo.core.config import load_config

    config = load_config()
    names = [r.name for r in config.seeds.remotes]
    assert names == ["team"]


def test_link_remote_default_name_derived_from_url(tmp_workspace, tmp_path):
    origin = _make_origin(tmp_path / "novo-seeds", {"x": "y"})
    remote = seed_core.link_remote(str(origin))
    assert remote.name == "novo-seeds"


def test_link_remote_is_idempotent(tmp_workspace, tmp_path):
    origin = _make_origin(tmp_path / "origin", {"x": "y"})
    seed_core.link_remote(str(origin), name="dup")
    seed_core.link_remote(str(origin), name="dup")  # must not raise

    from novo.core.config import load_config

    config = load_config()
    assert sum(1 for r in config.seeds.remotes if r.name == "dup") == 1


def test_link_remote_writes_last_synced_metadata(tmp_workspace, tmp_path):
    origin = _make_origin(tmp_path / "origin", {"x": "y"})
    seed_core.link_remote(str(origin), name="team")

    remotes = seed_core.list_remotes()
    assert remotes[0].last_synced_at is not None


# --- list_remotes ---


def test_list_remotes_empty_when_none_linked(tmp_workspace):
    assert seed_core.list_remotes() == []


def test_list_remotes_returns_registered(tmp_workspace, tmp_path):
    origin = _make_origin(tmp_path / "origin", {"x": "y"})
    seed_core.link_remote(str(origin), name="team")

    remotes = seed_core.list_remotes()
    assert len(remotes) == 1
    assert remotes[0].name == "team"
    assert remotes[0].url == str(origin)


# --- seeds from linked remote surface via list_seeds() ---


def test_remote_seeds_surface_via_list_seeds(tmp_workspace, tmp_path):
    origin = _make_origin(tmp_path / "origin", {"etl": "extract", "ml": "train"})
    seed_core.link_remote(str(origin), name="team")

    seeds = seed_core.list_seeds()
    identifiers = {s.identifier for s in seeds}
    assert "remote:team/etl" in identifiers
    assert "remote:team/ml" in identifiers


def test_resolve_seed_with_remote_prefix(tmp_workspace, tmp_path):
    origin = _make_origin(tmp_path / "origin", {"etl": "extract"})
    seed_core.link_remote(str(origin), name="team")

    resolved = seed_core.resolve_seed("remote:team/etl")
    assert resolved.scope == "remote"
    assert resolved.remote == "team"
    assert resolved.seed.name == "etl"


# --- sync_remote ---


def test_sync_picks_up_new_commits(tmp_workspace, tmp_path):
    origin = _make_origin(tmp_path / "origin", {"first": "a"})
    seed_core.link_remote(str(origin), name="team")

    # Add a new seed to the origin and commit.
    _make_seed_dir(origin, "second", "b")
    _git(["add", "."], cwd=origin)
    _git(["commit", "-m", "add second"], cwd=origin)

    results = seed_core.sync_remote("team")
    assert results[0][0] == "team"
    assert results[0][1] is True

    # New seed visible.
    identifiers = {s.identifier for s in seed_core.list_seeds()}
    assert "remote:team/second" in identifiers


def test_sync_all_when_name_omitted(tmp_workspace, tmp_path):
    a = _make_origin(tmp_path / "a", {"x": "y"})
    b = _make_origin(tmp_path / "b", {"x": "y"})
    seed_core.link_remote(str(a), name="alpha")
    seed_core.link_remote(str(b), name="beta")

    results = seed_core.sync_remote()
    names = {n for n, _, _ in results}
    assert names == {"alpha", "beta"}
    assert all(ok for _, ok, _ in results)


def test_sync_unknown_remote_raises(tmp_workspace):
    with pytest.raises(ValueError, match="unknown remote"):
        seed_core.sync_remote("nope")


def test_sync_missing_clone_reports_failure(tmp_workspace, tmp_path):
    origin = _make_origin(tmp_path / "origin", {"x": "y"})
    seed_core.link_remote(str(origin), name="team")

    # Simulate someone deleting the clone behind our back.
    import shutil

    shutil.rmtree(tmp_workspace.parent / "data" / "remotes" / "team")

    results = seed_core.sync_remote("team")
    assert results[0][1] is False
    assert "missing" in results[0][2]


# --- unlink_remote ---


def test_unlink_removes_config_and_clone(tmp_workspace, tmp_path):
    origin = _make_origin(tmp_path / "origin", {"x": "y"})
    seed_core.link_remote(str(origin), name="team")

    assert seed_core.unlink_remote("team") is True
    assert not (tmp_workspace.parent / "data" / "remotes" / "team").exists()
    from novo.core.config import load_config

    assert load_config().seeds.remotes == []


def test_unlink_unknown_returns_false(tmp_workspace):
    assert seed_core.unlink_remote("nope") is False
