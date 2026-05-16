"""Tests for scope-aware seed resolution."""

from pathlib import Path

import pytest

from novo.core import seed as seed_core
from novo.core import workspace as workspace_core
from novo.models.scoped_seed import parse_seed_identifier


# --- parse_seed_identifier ---


def test_parse_implicit_name():
    assert parse_seed_identifier("foo") == (None, None, "foo")


def test_parse_local_explicit():
    assert parse_seed_identifier("local:foo") == ("local", None, "foo")


def test_parse_user_explicit():
    assert parse_seed_identifier("user:foo") == ("user", None, "foo")


def test_parse_builtin_explicit():
    assert parse_seed_identifier("builtin:foo") == ("builtin", None, "foo")


def test_parse_remote_explicit():
    assert parse_seed_identifier("remote:team/foo") == ("remote", "team", "foo")


def test_parse_unknown_scope_raises():
    with pytest.raises(ValueError, match="unknown seed scope"):
        parse_seed_identifier("bogus:foo")


def test_parse_remote_missing_slash_raises():
    with pytest.raises(ValueError, match="must be 'remote"):
        parse_seed_identifier("remote:foo")


def test_parse_remote_empty_seed_raises():
    with pytest.raises(ValueError):
        parse_seed_identifier("remote:team/")


def test_parse_empty_raises():
    with pytest.raises(ValueError):
        parse_seed_identifier("")


def test_parse_missing_seed_name_raises():
    with pytest.raises(ValueError, match="missing seed name"):
        parse_seed_identifier("user:")


# --- list_seeds / resolve_seed with fully controlled scope environment ---


def _make_seed(seed_dir: Path, name: str, description: str = "") -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "template").mkdir(exist_ok=True)
    (seed_dir / "seed.toml").write_text(
        f'[seed]\nname = "{name}"\ndescription = "{description}"\n'
    )


@pytest.fixture
def scope_env(tmp_path, monkeypatch):
    """Wire all four scopes to isolated tmp dirs and pin a workspace override."""
    workspace = tmp_path / "ws"
    (workspace / ".novo" / "seeds").mkdir(parents=True)
    user = tmp_path / "user-seeds"
    user.mkdir()
    remotes = tmp_path / "remotes"
    remotes.mkdir()
    builtin = tmp_path / "builtin-seeds"
    builtin.mkdir()

    monkeypatch.setattr("novo.utils.paths.seeds_dir", lambda: user)
    monkeypatch.setattr("novo.core.seed.seeds_dir", lambda: user)
    monkeypatch.setattr("novo.utils.paths.remotes_dir", lambda: remotes)
    monkeypatch.setattr("novo.core.seed.remotes_dir", lambda: remotes)
    monkeypatch.setattr("novo.utils.paths.builtin_seeds_dir", lambda: builtin)
    monkeypatch.setattr("novo.core.seed.builtin_seeds_dir", lambda: builtin)

    workspace_core.set_workspace_override(workspace)
    yield {
        "workspace": workspace,
        "local": workspace / ".novo" / "seeds",
        "user": user,
        "remotes": remotes,
        "builtin": builtin,
    }
    workspace_core.set_workspace_override(None)


def test_list_seeds_orders_by_scope(scope_env):
    _make_seed(scope_env["local"] / "alpha", "alpha", "local one")
    _make_seed(scope_env["user"] / "beta", "beta", "user one")
    _make_seed(scope_env["remotes"] / "team" / "gamma", "gamma", "remote one")
    _make_seed(scope_env["builtin"] / "delta", "delta", "builtin one")

    seeds = seed_core.list_seeds()
    assert [s.identifier for s in seeds] == [
        "local:alpha",
        "user:beta",
        "remote:team/gamma",
        "builtin:delta",
    ]


def test_list_seeds_includes_multiple_remotes(scope_env):
    _make_seed(scope_env["remotes"] / "team" / "etl", "etl")
    _make_seed(scope_env["remotes"] / "other" / "etl", "etl")

    seeds = seed_core.list_seeds()
    identifiers = [s.identifier for s in seeds]
    assert "remote:team/etl" in identifiers
    assert "remote:other/etl" in identifiers


def test_resolve_seed_explicit_local(scope_env):
    _make_seed(scope_env["local"] / "alpha", "alpha")
    _make_seed(scope_env["user"] / "alpha", "alpha")  # would otherwise be ambiguous

    resolved = seed_core.resolve_seed("local:alpha")
    assert resolved.scope == "local"
    assert resolved.identifier == "local:alpha"


def test_resolve_seed_explicit_remote_picks_named_remote(scope_env):
    _make_seed(scope_env["remotes"] / "team" / "etl", "etl")
    _make_seed(scope_env["remotes"] / "other" / "etl", "etl")

    resolved = seed_core.resolve_seed("remote:team/etl")
    assert resolved.scope == "remote"
    assert resolved.remote == "team"


def test_resolve_seed_explicit_missing_raises(scope_env):
    with pytest.raises(ValueError, match="seed not found: user:nope"):
        seed_core.resolve_seed("user:nope")


def test_resolve_seed_implicit_single_match(scope_env):
    _make_seed(scope_env["builtin"] / "default", "default")
    resolved = seed_core.resolve_seed("default")
    assert resolved.identifier == "builtin:default"


def test_resolve_seed_implicit_ambiguity_raises(scope_env):
    _make_seed(scope_env["user"] / "default", "default")
    _make_seed(scope_env["builtin"] / "default", "default")

    with pytest.raises(ValueError, match="ambiguous"):
        seed_core.resolve_seed("default")


def test_resolve_seed_implicit_ambiguity_message_lists_options(scope_env):
    _make_seed(scope_env["local"] / "x", "x")
    _make_seed(scope_env["remotes"] / "team" / "x", "x")

    with pytest.raises(ValueError) as exc:
        seed_core.resolve_seed("x")
    msg = str(exc.value)
    assert "local:x" in msg
    assert "remote:team/x" in msg


def test_resolve_seed_implicit_missing_raises(scope_env):
    with pytest.raises(ValueError, match="seed not found: missing"):
        seed_core.resolve_seed("missing")


# --- init_seed scope routing ---


def test_init_seed_user_scope(scope_env):
    scoped = seed_core.init_seed("fresh", scope="user")
    assert scoped.scope == "user"
    assert (scope_env["user"] / "fresh" / "seed.toml").is_file()
    assert (scope_env["user"] / "fresh" / "template").is_dir()


def test_init_seed_local_scope_writes_into_workspace(scope_env):
    scoped = seed_core.init_seed("ws-seed", scope="local")
    assert scoped.scope == "local"
    assert (scope_env["local"] / "ws-seed" / "seed.toml").is_file()


def test_init_seed_remote_scope_rejected(scope_env):
    with pytest.raises(ValueError, match="cannot init"):
        seed_core.init_seed("nope", scope="remote")
