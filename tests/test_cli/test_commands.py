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
    assert (target / ".novo").is_dir()
    assert (target / ".novo" / "seeds").is_dir()
    assert (target / ".novo" / "config.toml").is_file()
    assert "Workspace initialized" in result.output


def test_init_default_cwd(tmp_workspace, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Workspace initialized" in result.output
    # New behavior: init creates the `.novo/` marker in cwd, does NOT mutate
    # the global config.workspace.path.
    assert (tmp_path / ".novo").is_dir()
    get_result = runner.invoke(app, ["config", "get", "workspace.path"])
    assert str(tmp_path) not in get_result.output


@patch("novo.core.experiment.uv.uv_init")
def test_workspace_flag_routes_to_explicit_workspace(mock_uv, tmp_workspace, tmp_path):
    other = tmp_path / "other-ws"
    other.mkdir()
    result = runner.invoke(app, ["--workspace", str(other), "new", "ws-flag-test", "--no-date"])
    assert result.exit_code == 0
    assert (other / ".novo").is_dir()
    assert (other / "ws-flag-test" / ".novo.toml").exists()
    # Default workspace should not have received the experiment.
    assert not (tmp_workspace / "ws-flag-test").exists()


@patch("novo.core.experiment.uv.uv_init")
def test_novo_workspace_env_routes_to_explicit_workspace(mock_uv, tmp_workspace, tmp_path):
    other = tmp_path / "env-ws"
    other.mkdir()
    result = runner.invoke(
        app,
        ["new", "env-test", "--no-date"],
        env={"NOVO_WORKSPACE": str(other)},
    )
    assert result.exit_code == 0
    assert (other / "env-test" / ".novo.toml").exists()
    assert not (tmp_workspace / "env-test").exists()


@patch("novo.core.experiment.uv.uv_init")
def test_workspace_flag_beats_env(mock_uv, tmp_workspace, tmp_path):
    flag_ws = tmp_path / "flag-ws"
    flag_ws.mkdir()
    env_ws = tmp_path / "env-ws"
    env_ws.mkdir()
    result = runner.invoke(
        app,
        ["--workspace", str(flag_ws), "new", "precedence-test", "--no-date"],
        env={"NOVO_WORKSPACE": str(env_ws)},
    )
    assert result.exit_code == 0
    assert (flag_ws / "precedence-test" / ".novo.toml").exists()
    assert not (env_ws / "precedence-test").exists()


@patch("novo.core.experiment.uv.uv_init")
def test_cwd_walk_up_discovers_workspace(mock_uv, tmp_workspace, tmp_path, monkeypatch):
    ws = tmp_path / "discovered-ws"
    ws.mkdir()
    (ws / ".novo").mkdir()
    nested = ws / "deep" / "subdir"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    result = runner.invoke(app, ["new", "cwd-test", "--no-date"])
    assert result.exit_code == 0
    assert (ws / "cwd-test" / ".novo.toml").exists()


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
    runner.invoke(app, ["seed", "init", "listed-seed", "--desc", "Should appear", "--scope", "user"])
    result = runner.invoke(app, ["seed", "list"])
    assert result.exit_code == 0
    assert "listed-seed" in result.output


# --- scoped seed list / init / --seed parsing ---


def test_seed_list_shows_grouped_sections(tmp_workspace):
    runner.invoke(app, ["seed", "init", "u1", "--scope", "user"])
    result = runner.invoke(app, ["seed", "list"])
    assert result.exit_code == 0
    # USER section appears (color codes stripped by Rich for non-TTY output).
    assert "USER" in result.output
    assert "BUILTIN" in result.output
    assert "u1" in result.output


def test_seed_list_scope_filter(tmp_workspace):
    runner.invoke(app, ["seed", "init", "userseed", "--scope", "user"])
    result = runner.invoke(app, ["seed", "list", "--scope", "user"])
    assert result.exit_code == 0
    assert "USER" in result.output
    assert "BUILTIN" not in result.output
    assert "userseed" in result.output


def test_seed_list_invalid_scope(tmp_workspace):
    result = runner.invoke(app, ["seed", "list", "--scope", "bogus"])
    assert result.exit_code == 1
    assert "Unknown scope" in result.output


def test_seed_list_json_includes_scope_and_identifier(tmp_workspace):
    runner.invoke(app, ["seed", "init", "jsonseed", "--scope", "user"])
    result = runner.invoke(app, ["seed", "list", "--json"])
    assert result.exit_code == 0
    import json

    data = json.loads(result.output)
    names = {item["name"]: item for item in data}
    assert "jsonseed" in names
    assert names["jsonseed"]["scope"] == "user"
    assert names["jsonseed"]["identifier"] == "user:jsonseed"


def test_seed_init_local_scope_writes_into_workspace(tmp_workspace, tmp_path, monkeypatch):
    ws = tmp_path / "explicit-ws"
    ws.mkdir()
    result = runner.invoke(
        app,
        ["--workspace", str(ws), "seed", "init", "ws-only", "--scope", "local"],
    )
    assert result.exit_code == 0
    assert (ws / ".novo" / "seeds" / "ws-only" / "seed.toml").is_file()


def test_seed_init_default_scope_is_local_when_in_workspace(tmp_workspace, tmp_path, monkeypatch):
    ws = tmp_path / "auto-local-ws"
    ws.mkdir()
    (ws / ".novo").mkdir()
    monkeypatch.chdir(ws)
    result = runner.invoke(app, ["seed", "init", "auto-local"])
    assert result.exit_code == 0
    assert (ws / ".novo" / "seeds" / "auto-local" / "seed.toml").is_file()


@patch("novo.core.experiment.uv.uv_init")
def test_new_with_scoped_seed_flag(mock_uv, tmp_workspace, tmp_path, monkeypatch):
    ws = tmp_path / "scoped-ws"
    ws.mkdir()
    # Pre-create a local seed.
    (ws / ".novo" / "seeds" / "local-one").mkdir(parents=True)
    (ws / ".novo" / "seeds" / "local-one" / "template").mkdir()
    (ws / ".novo" / "seeds" / "local-one" / "seed.toml").write_text(
        '[seed]\nname = "local-one"\ndescription = "ws-only"\n'
    )

    result = runner.invoke(
        app,
        [
            "--workspace",
            str(ws),
            "new",
            "scoped-exp",
            "--no-date",
            "--seed",
            "local:local-one",
        ],
    )
    assert result.exit_code == 0
    # Read .novo.toml back and check it stored the scoped identifier.
    import tomllib

    data = tomllib.loads((ws / "scoped-exp" / ".novo.toml").read_text())
    assert data["experiment"]["seed"] == "local:local-one"


# --- detached mode ---


@patch("novo.core.experiment.uv.uv_init")
def test_new_detached_creates_in_cwd(mock_uv, tmp_workspace, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--detached", "new", "stand-alone", "--no-date"])
    assert result.exit_code == 0
    assert (tmp_path / "stand-alone" / ".novo.toml").exists()
    assert (tmp_path / "stand-alone" / ".git").is_dir()
    assert "Detached at" in result.output
    # Default workspace untouched.
    assert not (tmp_workspace / "stand-alone").exists()


@patch("novo.core.experiment.uv.uv_init")
def test_new_detached_at_writes_under_at(mock_uv, tmp_workspace, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_workspace)
    parent = tmp_path / "exp-parent"
    parent.mkdir()
    result = runner.invoke(
        app,
        ["--detached", "new", "atexp", "--no-date", "--at", str(parent)],
    )
    assert result.exit_code == 0
    assert (parent / "atexp" / ".novo.toml").exists()


def test_new_at_without_detached_errors(tmp_workspace, tmp_path):
    result = runner.invoke(app, ["new", "x", "--at", str(tmp_path)])
    assert result.exit_code == 1
    assert "--at requires --detached" in result.output


def test_list_in_detached_mode_errors(tmp_workspace):
    result = runner.invoke(app, ["--detached", "list"])
    assert result.exit_code == 1
    assert "novo list" in result.output
    assert "--detached" in result.output


def test_info_in_detached_mode_errors(tmp_workspace):
    result = runner.invoke(app, ["--detached", "info"])
    assert result.exit_code == 1


def test_search_in_detached_mode_errors(tmp_workspace):
    result = runner.invoke(app, ["--detached", "search", "anything"])
    assert result.exit_code == 1


def test_delete_in_detached_mode_errors(tmp_workspace):
    result = runner.invoke(app, ["--detached", "delete", "anything", "--force"])
    assert result.exit_code == 1


def test_open_in_detached_mode_errors(tmp_workspace):
    result = runner.invoke(app, ["--detached", "open", "anything"])
    assert result.exit_code == 1


@patch("novo.core.experiment.uv.uv_init")
def test_new_seed_ambiguity_errors_with_helpful_message(mock_uv, tmp_workspace, tmp_path):
    ws = tmp_path / "ambig-ws"
    ws.mkdir()
    # local and user both have a seed called "shared". (default builtin is
    # filtered out by the unique name.)
    (ws / ".novo" / "seeds" / "shared").mkdir(parents=True)
    (ws / ".novo" / "seeds" / "shared" / "template").mkdir()
    (ws / ".novo" / "seeds" / "shared" / "seed.toml").write_text(
        '[seed]\nname = "shared"\n'
    )
    user_root = tmp_workspace.parent / "data" / "seeds"
    (user_root / "shared").mkdir(parents=True)
    (user_root / "shared" / "template").mkdir()
    (user_root / "shared" / "seed.toml").write_text('[seed]\nname = "shared"\n')

    result = runner.invoke(
        app,
        [
            "--workspace",
            str(ws),
            "new",
            "ambig-exp",
            "--no-date",
            "--seed",
            "shared",
        ],
    )
    assert result.exit_code == 1
    assert "ambiguous" in result.output
    assert "local:shared" in result.output
    assert "user:shared" in result.output
