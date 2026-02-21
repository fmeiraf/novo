# Architecture

## Project Structure

```
src/
├── novo/
│   ├── __init__.py              # Package root
│   ├── __main__.py              # python -m novo entry
│   ├── cli/                     # CLI layer (Typer)
│   │   ├── __init__.py          # Typer app, --shell-init callback
│   │   ├── new.py               # novo new
│   │   ├── list.py              # novo list
│   │   ├── delete.py            # novo delete
│   │   ├── search.py            # novo search
│   │   ├── open.py              # novo open
│   │   ├── info.py              # novo info
│   │   └── seed.py              # novo seed {list,add,create,remove}
│   ├── core/                    # Business logic
│   │   ├── config.py            # Load/save config.toml
│   │   ├── workspace.py         # Workspace init (dirs + git)
│   │   ├── experiment.py        # Experiment CRUD
│   │   ├── git.py               # Git subprocess wrapper
│   │   └── seed.py              # Seed management
│   ├── models/                  # Pydantic schemas
│   │   ├── config.py            # NovoConfig (workspace, defaults, naming)
│   │   ├── experiment.py        # Experiment (.novo.toml)
│   │   └── seed.py              # Seed (seed.toml)
│   ├── utils/                   # Shared utilities
│   │   ├── paths.py             # XDG path resolution (platformdirs)
│   │   ├── shell.py             # Shell integration for `novo open`
│   │   ├── terminal.py          # Terminal detection and window opening
│   │   └── uv.py                # uv CLI wrapper (init, add, python)
│   └── tui/                     # TUI layer (Textual)
│       ├── app.py               # NovoApp entry
│       ├── styles/app.tcss      # Textual CSS
│       ├── screens/
│       │   ├── main.py          # Two-panel layout
│       │   ├── new_experiment.py # Creation modal
│       │   ├── confirm.py       # Confirmation dialog
│       │   └── seed_manager.py  # Seed browser
│       └── widgets/
│           ├── experiment_list.py # Navigable list (vim keys)
│           ├── experiment_card.py # Detail panel
│           ├── search_bar.py     # Search input
│           └── status_bar.py     # Keybinding hints
└── seeds/
    └── default/                 # Built-in seed
        ├── seed.toml            # Seed manifest
        └── template/            # Files copied into new experiments
```

## Layer Diagram

```
CLI (Typer)  ──→  Core  ←──  TUI (Textual)
                   ↓
                Models (Pydantic)
                   ↑
                 Utils
```

Both CLI and TUI call into Core. Neither accesses the filesystem directly — Core handles all I/O. Models are shared across all layers. Utils provides path resolution and subprocess wrappers used by Core.

## Component Documentation

For detailed documentation on each layer, see:

| Document | Description |
|----------|-------------|
| [cli.md](cli.md) | CLI commands, Typer app structure, patterns |
| [tui.md](tui.md) | Textual app, screens, widgets, keybindings, styles |
| [core.md](core.md) | Business logic: experiment CRUD, seed management, config, workspace, git |
| [models.md](models.md) | Pydantic schemas: NovoConfig, Experiment, Seed |
| [utils.md](utils.md) | XDG paths, uv wrapper, shell integration |

## Data Flow: Experiment Creation

```
novo new "my-exp" --seed default --tag ml
          │
          ▼
    cli/new.py          Parse args
          │
          ▼
    core/workspace.py   Ensure workspace dir + git repo exist
          │
          ▼
    core/experiment.py  Generate dir name (date prefix optional)
          │              Create directory
          │              Call uv_init() for Python environment
          │              Apply seed template
          │              Write .novo.toml metadata
          │              Git add + commit (if auto_commit enabled)
          │
          ▼
    Experiment model    Return to CLI for display
```

## Runtime Workspace Layout

```
~/.local/share/novo/
├── workspace/                   # Default workspace (git repo)
│   ├── .git/
│   ├── .gitignore
│   ├── 2026-02-20-my-exp/       # Date-prefixed experiment
│   │   ├── .novo.toml           # Experiment metadata
│   │   ├── .python-version
│   │   ├── pyproject.toml       # Created by uv init
│   │   ├── .claude/             # From seed template
│   │   └── .agents/             # From seed template
│   └── another-exp/             # No date prefix (--no-date)
│       └── ...
├── seeds/                       # User-installed seeds
│   └── custom-seed/
│       ├── seed.toml
│       └── template/
└── ...

~/.config/novo/
└── config.toml                  # Global configuration
```

## Data Models

### `.novo.toml` (per experiment)

```toml
[experiment]
name = "my-exp"
seed = "default"
tags = ["ml", "pytorch"]
description = "Image classifier experiment"
python = "3.12"
created_at = "2026-02-20T14:30:00.123456"
dir_name = "2026-02-20-my-exp"
```

### `config.toml` (global)

```toml
[workspace]
path = ""                # Empty = XDG default

[defaults]
seed = "default"
auto_commit = true
python = ""              # Empty = system default

[naming]
date_prefix = true
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
