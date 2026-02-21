# Utils

Shared utilities used by the Core layer. No business logic — just path resolution, subprocess wrappers, and shell integration.

## Structure

```
utils/
├── paths.py    # XDG path resolution (platformdirs)
├── uv.py       # uv CLI wrapper
└── shell.py    # Shell integration for `novo open`
```

## paths.py

XDG-compliant path resolution via [platformdirs](https://platformdirs.readthedocs.io/). All paths are resolved lazily through functions.

| Function | Returns | Default value |
|----------|---------|---------------|
| `config_dir()` | Config directory | `~/.config/novo/` |
| `data_dir()` | Data directory | `~/.local/share/novo/` |
| `config_file()` | Global config | `~/.config/novo/config.toml` |
| `default_workspace_dir()` | Workspace root | `~/.local/share/novo/workspace` |
| `seeds_dir()` | User-installed seeds | `~/.local/share/novo/seeds` |
| `builtin_seeds_dir()` | Package-bundled seeds | `<package>/seeds/` |

**Testing note:** Tests patch these functions via `monkeypatch.setattr` to redirect all paths to `tmp_path`. See [testing.md](testing.md) for the `tmp_workspace` fixture.

## uv.py

Wrappers around the [uv](https://docs.astral.sh/uv/) CLI. All calls use `subprocess.run`.

| Function | Description |
|----------|-------------|
| `uv_init(directory, python)` | `uv init --no-workspace` with optional `--python` flag. |
| `uv_add(directory, packages)` | `uv add <packages>` in the given directory. |
| `list_python_versions()` | Parse `uv python list --only-installed` and return version strings. |
| `install_python(version)` | `uv python install <version>`. |

**Testing note:** `uv_init` must be mocked in any test that creates experiments. Patch target: `novo.core.experiment.uv.uv_init`.

## shell.py

| Function | Description |
|----------|-------------|
| `get_shell_init()` | Returns a bash/zsh function that intercepts `novo open <name>` and `cd`s into the experiment directory. |

The function is printed by `novo --shell-init` and meant to be `eval`'d in the user's shell rc file. This is necessary because a child process (the CLI) cannot change the parent shell's working directory.
