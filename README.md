<div align="center">

# novo

**Spin up Python experiments in seconds.**

Create isolated, reproducible Python environments with one command.<br>
Powered by [uv](https://docs.astral.sh/uv/), organized by convention, extensible through seeds.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Built with uv](https://img.shields.io/badge/built%20with-uv-DE5FE9?style=flat-square)](https://docs.astral.sh/uv/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

</div>

---

```bash
$ novo new image-classifier --tag ml --desc "ResNet experiments"

  Created: image-classifier
     Path: ~/.local/share/novo/workspace/2026-02-21-image-classifier
     Seed: default
```

```
2026-02-21-image-classifier/
  .venv/             # isolated virtual environment
  pyproject.toml     # managed by uv
  .novo.toml         # experiment metadata
  .claude/           # AI agent scaffolding (from seed)
  .agents/
```

---

## Why novo?

You're prototyping. You want a clean Python environment with your usual dependencies and project structure, right now, without copy-pasting boilerplate or remembering setup steps.

**novo gives you:**

- **One-command setup** -- `novo new <name>` creates a full Python project with uv, git, and your template files
- **Seed templates** -- Package your favorite stack (dependencies, config files, scripts) into reusable seeds
- **Date-prefixed directories** -- Experiments are chronologically organized by default
- **Git tracking** -- Every experiment is auto-committed to a shared workspace repo
- **Interactive TUI** -- Browse, search, and manage experiments without memorizing commands
- **Zero config needed** -- Works out of the box with sensible defaults and XDG-compliant paths

---

## Installation

**Requirements:** Python 3.11+, [uv](https://docs.astral.sh/uv/), git

```bash
git clone https://github.com/your-user/novo.git
cd novo
uv sync
```

Run directly:
```bash
uv run novo --help
```

Or install for global access:
```bash
uv pip install -e .
novo --help
```

---

## Quick start

```bash
# 1. Initialize your workspace (first time only)
novo init

# 2. Create an experiment
novo new my-experiment

# 3. See what you've got
novo list

# 4. Launch the interactive TUI
novo
```

---

## Usage

### Creating experiments

```bash
novo new <name> [options]
```

| Option | Description |
|--------|-------------|
| `--seed, -s` | Seed template to use (default: `default`) |
| `--python, -p` | Python version for the environment |
| `--desc, -d` | Short description |
| `--tag, -t` | Tags (repeatable) |
| `--no-date` | Skip the `YYYY-MM-DD` directory prefix |

```bash
# Minimal
novo new quick-test

# Full options
novo new transformer-exp --seed ml-stack --python 3.12 --desc "Fine-tuning GPT" --tag nlp --tag pytorch
```

### Browsing and searching

```bash
novo list                          # list all experiments
novo list --sort modified --tag ml # filter and sort
novo list --json                   # machine-readable output
novo search "transformer"          # fuzzy search across name, description, tags
novo info my-experiment            # detailed view of one experiment
novo info                          # workspace summary
```

### Managing experiments

```bash
novo delete my-experiment          # interactive confirmation
novo delete my-experiment --force  # skip confirmation
novo open my-experiment            # cd into the directory (requires shell integration)
```

---

## Interactive TUI

Run `novo` with no arguments to launch the terminal UI.

```
 ┌─ Experiments ─────────────┐ ┌─ Details ──────────────────┐
 │                            │ │                             │
 │  > 2026-02-21-transformer  │ │  Name: transformer-exp      │
 │    2026-02-20-image-cls    │ │  Seed: ml-stack              │
 │    2026-02-19-data-clean   │ │  Tags: nlp, pytorch          │
 │                            │ │  Created: 2026-02-21         │
 │                            │ │                             │
 └────────────────────────────┘ └─────────────────────────────┘
  n new  d delete  s seeds  / search  ? help  q quit
```

| Key | Action |
|-----|--------|
| `n` | Create new experiment |
| `d` | Delete selected |
| `s` | Browse seeds |
| `/` | Search |
| `Enter` | Open experiment directory |
| `j` / `k` | Navigate (vim-style) |
| `?` | Help |
| `q` | Quit |

---

## Seeds

Seeds are reusable project templates. When you create an experiment, novo copies the seed's template files, installs its dependencies via `uv add`, and runs any post-creation scripts.

### The built-in seed

novo ships with a `default` seed that includes `.claude/` and `.agents/` scaffolding for AI-assisted development.

### Creating your own seed

```bash
novo seed init my-seed --desc "Data science starter"
```

This scaffolds the seed structure at `~/.local/share/novo/seeds/my-seed/`:

```
my-seed/
  seed.toml          # manifest
  template/          # files copied into new experiments
```

Edit `seed.toml` to define dependencies, post-creation hooks, and file exclusions:

```toml
[seed]
name = "my-seed"
description = "Data science starter"

[seed.dependencies]
packages = ["numpy", "pandas", "matplotlib", "jupyter"]

[seed.post_create]
commands = ["mkdir notebooks", "echo 'Ready!'"]

[seed.files]
exclude = ["__pycache__", "*.pyc", ".git"]
```

Drop your starter files into `template/` -- they'll be copied into every experiment that uses this seed.

### Seed commands

```bash
novo seed list                                   # see all available seeds
novo seed init <name> [--desc] [--path]          # scaffold a new seed
novo seed add <git-url> [--name]                 # install seed from a git repo
novo seed create <name> --from <experiment>      # extract a seed from an existing experiment
novo seed remove <name>                          # uninstall a user seed
```

---

## Shell integration

`novo open` needs a shell function to change your working directory. Add this line to your `~/.bashrc` or `~/.zshrc`:

```bash
eval "$(novo --shell-init)"
```

After reloading your shell, `novo open my-experiment` will `cd` you directly into the experiment directory.

---

## Configuration

```bash
novo config show                 # display all settings
novo config get <key>            # read a value
novo config set <key> <value>    # write a value
```

Stored at `~/.config/novo/config.toml`:

| Key | Default | Description |
|-----|---------|-------------|
| `workspace.path` | XDG data dir | Where experiments live |
| `defaults.seed` | `"default"` | Seed applied to new experiments |
| `defaults.auto_commit` | `true` | Auto-commit experiments to git |
| `defaults.python` | system default | Python version for new environments |
| `naming.date_prefix` | `true` | Prepend `YYYY-MM-DD` to directory names |

---

## How it works

When you run `novo new my-experiment`:

```
1.  Resolve workspace directory
2.  Generate directory name (2026-02-21-my-experiment)
3.  uv init --no-workspace        # create Python project
4.  Apply seed template            # copy files, install deps, run hooks
5.  Write .novo.toml               # save experiment metadata
6.  git add + commit               # track in workspace repo
```

### Architecture

```
CLI (Typer)  ───>  Core  <───  TUI (Textual)
                    │
              Models (Pydantic)
                    │
                  Utils
```

| Layer | Role |
|-------|------|
| **CLI** | Typer commands, Rich-formatted output |
| **TUI** | Textual app with screens, widgets, vim keybindings |
| **Core** | Experiment CRUD, seed management, config, git |
| **Models** | Pydantic schemas (`NovoConfig`, `Experiment`, `Seed`) |
| **Utils** | XDG paths via `platformdirs`, `uv` wrapper, shell integration |

### Directory layout

```
~/.config/novo/
  config.toml

~/.local/share/novo/
  workspace/                          # git-tracked workspace
    2026-02-21-my-experiment/
      .novo.toml
      pyproject.toml
      .venv/
      ...
  seeds/                              # user-installed seeds
    my-seed/
      seed.toml
      template/
```

---

## Development

```bash
uv sync                              # install all dependencies
uv run novo                          # run the app
uv run pytest                        # run full test suite
uv run pytest tests/test_core        # core tests only
uv run pytest -x -v                  # stop on first failure, verbose
```

---

## License

[MIT](LICENSE)
