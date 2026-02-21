# Core

Business logic layer. Handles all filesystem I/O, subprocess calls, and data persistence. Both CLI and TUI import from here — neither touches the filesystem directly.

## Structure

```
core/
├── config.py       # Load/save config.toml
├── workspace.py    # Workspace directory + git init
├── experiment.py   # Experiment CRUD
├── git.py          # Git subprocess wrapper
└── seed.py         # Seed management + template application
```

## Modules

### config.py

Manages the global `config.toml` (at `~/.config/novo/config.toml`).

| Function | Description |
|----------|-------------|
| `load_config()` | Load `NovoConfig` from TOML. Returns defaults if file is missing. |
| `save_config(config)` | Persist config to TOML via `tomli_w`. |
| `get_workspace_path(config)` | Resolve workspace path from config or fall back to XDG default. |

### workspace.py

| Function | Description |
|----------|-------------|
| `ensure_initialized()` | Create workspace dir if missing, init git repo, write `.gitignore`, commit. Returns workspace `Path`. |

Called at the start of experiment creation to guarantee the workspace exists.

### experiment.py

The main CRUD module. All experiment operations go through here.

| Function | Description |
|----------|-------------|
| `create(name, seed_name, python, description, tags, no_date)` | Create experiment: `uv init` → apply seed → write `.novo.toml` → git commit. Returns `Experiment`. |
| `list_all(sort_by, tag)` | List experiments. Sort by `created`, `name`, or `modified`. Optional tag filter. |
| `get(name)` | Get experiment by name or dir_name. Returns `Experiment` or `None`. |
| `get_path(name)` | Get filesystem path to experiment directory. |
| `delete(name)` | Delete experiment via git (`remove_and_commit`) or `shutil.rmtree`. |
| `search(query)` | Token-based search across name, description, tags, and seed. |

**Internal helpers:**
- `_make_dir_name(name, use_date_prefix)` — Prepends `YYYY-MM-DD-` if date prefix is enabled.
- `_write_novo_toml(path, experiment)` — Serializes experiment to `.novo.toml`.
- `_read_novo_toml(path)` — Reads `.novo.toml` and returns `Experiment`.

### git.py

Thin subprocess wrappers. All calls use `subprocess.run` with `check=True`.

| Function | Description |
|----------|-------------|
| `init(directory)` | `git init` |
| `add_and_commit(directory, message, paths)` | Stage files (all or specific paths) and commit. |
| `remove_and_commit(directory, target, message)` | `git rm -rf` target and commit. |
| `is_git_repo(directory)` | Check via `git rev-parse --is-inside-work-tree`. |

### seed.py

Manages seed templates — both the built-in `default` seed (bundled in the package) and user-installed seeds (in `~/.local/share/novo/seeds/`).

| Function | Description |
|----------|-------------|
| `list_seeds()` | List all seeds (built-in + user-installed). |
| `get_seed(name)` | Get seed by name. |
| `apply_seed(seed_name, target_dir)` | Copy template files, install dependencies, run post-create commands. |
| `add_from_git(url, name)` | Clone seed from git URL, validate `seed.toml`. |
| `create_from_experiment(experiment_dir, name, description)` | Create a new seed from an existing experiment directory. |
| `remove_seed(name)` | Remove user seed. Refuses to delete built-in seeds. |

**Template application flow:**
1. Load `seed.toml` to get config
2. Copy `template/` contents to target (respecting `files.exclude` patterns, skipping `pyproject.toml`)
3. Install `dependencies.packages` via `uv_add`
4. Run `post_create.commands` as shell subprocesses
