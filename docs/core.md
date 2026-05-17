# Core

Business logic layer. Handles all filesystem I/O, subprocess calls, and data persistence. Both CLI and TUI import from here — neither touches the filesystem directly.

## Structure

```
core/
├── config.py       # Load/save config.toml
├── workspace.py    # Workspace marker + discovery, mode resolution, init
├── experiment.py   # Experiment CRUD (workspace + detached modes)
├── git.py          # Git subprocess wrapper
├── remote.py       # Git wrappers and metadata for linked remotes
└── seed.py         # Seed listing, scope-aware resolution, remote management
```

## Modules

### config.py

Manages the global `config.toml` (at `~/.config/novo/config.toml`).

| Function | Description |
|----------|-------------|
| `load_config()` | Load `NovoConfig` from TOML. Returns defaults if file is missing. |
| `save_config(config)` | Persist config to TOML. Excludes per-remote `last_synced_at` (that lives in the per-remote metadata file). |
| `get_workspace_path(config)` | Resolve workspace path from config or fall back to XDG default. |

### workspace.py

```
MARKER_NAME = ".novo"
```

A workspace is any directory containing a `.novo/` marker dir (same pattern as git's `.git/`). Resolution and detached-mode state are process-scoped via module globals (cleared between tests by `conftest.py`).

| Function | Description |
|----------|-------------|
| `set_workspace_override(path)` | Pin a workspace for the current invocation (CLI sets it from `--workspace` / `NOVO_WORKSPACE`). |
| `get_workspace_override()` | Read-only access to the override. |
| `set_detached_forced(bool)` | Flip the process into detached mode (CLI sets it from `--detached`). |
| `is_detached_forced()` | True if the current invocation was started with `--detached`. |
| `discover(start=None)` | Walk up from `start` (default cwd) looking for `.novo/`. Returns the workspace path or None. |
| `current_workspace(cwd=None)` | Override → walk-up → `config.workspace.path` → XDG default. Always returns a path. |
| `resolve_mode(cwd=None)` | Returns `(is_detached, workspace_or_None)` for the current invocation. |
| `ensure_initialized(target=None)` | Create the dir, write `.novo/` marker (with `seeds/` and `config.toml`), init git on first creation. Idempotent. Silently migrates pre-marker workspaces. |

### experiment.py

The main CRUD module. All experiment operations go through here.

| Function | Description |
|----------|-------------|
| `create(name, seed_name, python, description, tags, no_date, detached=False, at=None)` | Create experiment. In workspace mode: `uv init` → apply seed → write `.novo.toml` → commit to workspace. In detached mode: target dir is `(at or cwd)/<dir_name>`, with its own git repo (gated on `defaults.detached_git`). Stores the **scoped** seed identifier in `.novo.toml`. |
| `list_all(sort_by, tag)` | List experiments. |
| `get(name)` | Get experiment by name or dir_name. |
| `get_path(name)` | Filesystem path to experiment directory. |
| `delete(name)` | Delete via git or `shutil.rmtree`. |
| `search(query)` | Token-based search across name/description/tags/seed. |

### git.py

Thin subprocess wrappers (`init`, `add_and_commit`, `remove_and_commit`, `is_git_repo`).

### remote.py

Git wrappers for linked remote seed registries, plus per-remote metadata persistence.

| Function | Description |
|----------|-------------|
| `clone(url, target, ref=None)` | `git clone <url> <target>`, optional `git checkout <ref>`. |
| `pull(repo_dir, ref=None)` | `git pull --ff-only`, or `fetch + reset --hard origin/<ref>` when ref is given. |
| `read_metadata(remote_dir)` | Read `<remote_dir>/.novo-remote.toml` (returns `{}` if missing). |
| `write_metadata(remote_dir, last_synced_at)` | Persist sync timestamp. |
| `read_last_synced_at(remote_dir)` | Convenience that returns just the timestamp. |

### seed.py

Manages seed templates across four scopes — local (workspace `.novo/seeds/`), user (`~/.local/share/novo/seeds/`), remote (`~/.local/share/novo/remotes/<n>/<seed>/`), builtin (bundled).

| Function | Description |
|----------|-------------|
| `list_seeds(workspace=None)` | Walk every scope in order; return `list[ScopedSeed]`. |
| `resolve_seed(identifier, workspace=None)` | Resolve an identifier — explicit prefix or bare. Raises `ValueError` on ambiguity (same name in multiple scopes) or missing. |
| `get_seed(name)` | Back-compat shim — returns the underlying `Seed` (no scope info). |
| `apply_seed(identifier, target_dir, workspace=None)` | Copy template, install deps, run post-create. Returns the resolved `ScopedSeed`. |
| `init_seed(name, description, path=None, scope="user", workspace=None)` | Scaffold a new seed in the chosen scope (`local` or `user`). |
| `create_from_experiment(experiment_dir, name, description)` | Create a user-scope seed from an experiment. |
| `remove_seed(name)` | Remove a user-installed seed. |
| `link_remote(url, name=None, ref=None)` | Register and clone a remote registry. Idempotent — re-linking updates the URL/ref and reuses the clone. |
| `sync_remote(name=None)` | Pull one or all linked remotes. Returns `list[(name, ok, message)]`. |
| `unlink_remote(name)` | Remove config entry + delete the clone. |
| `list_remotes()` | Return `list[RemoteSeed]` from config, populating `last_synced_at` from the metadata file. |

**Template application flow:**
1. `resolve_seed(identifier)` picks the right scope.
2. Copy `template/` contents to the target (respecting `files.exclude`, skipping `pyproject.toml`).
3. Install `dependencies.packages` via `uv_add`.
4. Run `post_create.commands` as shell subprocesses.

**Scope resolution rules (implicit lookup):**
- Walks `local → user → remote → builtin`.
- Same name in multiple scopes → `ValueError("ambiguous seed …")` with explicit suggestions.
- Remote scope requires `remote:<name>/<seed>` to disambiguate registries — `remote:<seed>` is rejected at parse time.
