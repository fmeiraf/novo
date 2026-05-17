# Architecture

## Project Structure

```
src/
├── novo/
│   ├── __init__.py              # Package root
│   ├── __main__.py              # python -m novo entry
│   ├── cli/                     # CLI layer (Typer)
│   │   ├── __init__.py          # Typer app, --workspace/--detached, require_workspace helper
│   │   ├── new.py               # novo new (workspace + detached)
│   │   ├── list.py              # novo list
│   │   ├── delete.py            # novo delete
│   │   ├── search.py            # novo search
│   │   ├── open.py              # novo open
│   │   ├── info.py              # novo info
│   │   ├── init.py              # novo init [path]
│   │   ├── config.py            # novo config {show,get,set}
│   │   └── seed.py              # novo seed {list,init,link,sync,unlink,create,remove}
│   ├── core/                    # Business logic
│   │   ├── config.py            # Load/save config.toml
│   │   ├── workspace.py         # Marker + discovery + mode resolution
│   │   ├── experiment.py        # Experiment CRUD (workspace + detached)
│   │   ├── git.py               # Git subprocess wrapper
│   │   ├── remote.py            # Git wrappers + per-remote metadata
│   │   └── seed.py              # Scope-aware seed mgmt + remote link/sync/unlink
│   ├── models/                  # Pydantic schemas
│   │   ├── config.py            # NovoConfig (incl. SeedsConfig + RemoteSeed)
│   │   ├── experiment.py        # Experiment (.novo.toml)
│   │   ├── seed.py              # Seed (seed.toml)
│   │   └── scoped_seed.py       # ScopedSeed + identifier parser
│   ├── utils/                   # Shared utilities
│   │   ├── paths.py             # XDG paths + remotes_dir + workspace_seeds_dir
│   │   ├── shell.py             # Shell integration for `novo open`
│   │   ├── terminal.py          # Terminal detection and window opening
│   │   └── uv.py                # uv CLI wrapper
│   └── tui/                     # TUI layer (Textual)
│       ├── app.py               # NovoApp — picks MainScreen vs DetachedScreen
│       ├── styles/app.tcss      # Textual CSS
│       ├── screens/
│       │   ├── main.py          # Workspace mode: tabbed Experiments + Seeds
│       │   ├── detached.py      # Detached-mode minimal landing screen
│       │   ├── new_experiment.py # Creation modal (uses SeedPicker)
│       │   ├── new_seed.py      # Scaffold-seed modal
│       │   ├── remote_link.py   # Link-remote modal
│       │   └── confirm.py       # Confirmation dialog
│       └── widgets/
│           ├── experiment_list.py
│           ├── experiment_card.py
│           ├── search_bar.py
│           ├── status_bar.py    # Mode chip + context bindings + sync note
│           ├── seed_picker.py   # Scope-grouped picker + pure build_picker_rows
│           ├── file_tree.py
│           └── file_preview.py
└── seeds/
    └── default/                 # Built-in seed
        ├── seed.toml
        └── template/
```

## Layer Diagram

```
CLI (Typer)  ──→  Core  ←──  TUI (Textual)
                   ↓
                Models (Pydantic)
                   ↑
                 Utils
```

Both CLI and TUI call into Core. Neither accesses the filesystem directly. Models are shared across layers. Utils provides path resolution and subprocess wrappers used by Core.

## Component Documentation

| Document | Description |
|----------|-------------|
| [cli.md](cli.md) | CLI commands, flags, scope-aware `--seed`, mode resolution |
| [tui.md](tui.md) | Textual app, screens, widgets, keybindings, styles |
| [core.md](core.md) | Business logic — workspace discovery, scope resolution, remotes, detached create |
| [models.md](models.md) | Pydantic schemas |
| [seeds.md](seeds.md) | Seed scopes, identifier syntax, remote sync workflow |
| [utils.md](utils.md) | XDG paths, uv wrapper, shell integration |

## Data Flow: Experiment Creation (workspace mode)

```
novo new "my-exp" --seed user:data-science --tag ml
          │
          ▼
    cli/new.py          Parse args, call core
          │
          ▼
    core/workspace.py   current_workspace() → ensure_initialized()
          │              (writes `.novo/` marker if missing, git-init on first run)
          ▼
    core/experiment.py  Generate dir name, mkdir
          │              Call uv_init for Python environment
          │              apply_seed("user:data-science", exp_dir)
          │                → resolve_seed → copy template → uv add → post-create
          │              Write .novo.toml (with scoped seed identifier)
          │              git add + commit in workspace
          ▼
    Experiment model    Returned to CLI for display
```

## Data Flow: Experiment Creation (detached mode)

```
novo --detached new "scratch" --at /tmp
          │
          ▼
    cli/__init__.py     set_detached_forced(True) at root callback
          │
          ▼
    cli/new.py          detached=True, at=/tmp → core.experiment.create
          │
          ▼
    core/experiment.py  No workspace prep; exp_dir = /tmp/scratch
          │              uv_init + apply_seed + write .novo.toml
          │              if defaults.detached_git: git init + commit inside exp_dir
          ▼
    Experiment model    Returned to CLI for display
```

## Runtime Layout

```
~/.local/share/novo/
├── workspace/                   # Default workspace (XDG fallback)
│   ├── .novo/
│   │   ├── seeds/               # local-scope seeds (per workspace)
│   │   └── config.toml          # per-workspace overrides (placeholder)
│   ├── .git/
│   ├── .gitignore
│   ├── 2026-02-20-my-exp/
│   │   ├── .novo.toml           # seed = "user:data-science"
│   │   └── …
│   └── …
├── seeds/                       # user-scope seeds
│   └── data-science/
│       ├── seed.toml
│       └── template/
└── remotes/                     # linked remote registries
    └── team/                    # one dir per remote name
        ├── .novo-remote.toml    # last_synced_at
        ├── .git/
        ├── etl/
        │   ├── seed.toml
        │   └── template/
        └── ml-experiment/
            └── …

~/.config/novo/
└── config.toml                  # Global configuration (incl. [[seeds.remotes]])
```

Any directory with a `.novo/` marker is also a valid workspace; the layout above just shows the XDG default. Multiple workspaces are supported via cwd discovery, `--workspace`, or `NOVO_WORKSPACE`.

## Data Models

### `.novo.toml` (per experiment)

```toml
[experiment]
name = "my-exp"
seed = "user:data-science"         # scoped identifier
tags = ["ml", "pytorch"]
description = "Image classifier experiment"
python = "3.12"
created_at = "2026-02-20T14:30:00.123456"
```

### `config.toml` (global)

```toml
[workspace]
path = ""                          # Empty = XDG default

[defaults]
seed = "default"
auto_commit = true
python = ""                        # Empty = system default
detached_git = true                # Detached experiments get their own git repo

[naming]
date_prefix = true

[[seeds.remotes]]
name = "team"
url  = "git@github.com:team/seeds.git"
ref  = ""                          # Empty = follow the cloned branch
```

### `seed.toml` (per seed)

```toml
[seed]
name = "default"
description = "Default experiment template with AI agent scaffolding"

[seed.dependencies]
packages = []

[seed.post_create]
commands = []

[seed.files]
exclude = ["__pycache__", "*.pyc", ".git"]
```

### `.novo-remote.toml` (per linked remote)

```toml
last_synced_at = "2026-05-16T18:00:00.123456"
```
