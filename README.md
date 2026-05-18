<div align="center">

<img src="https://raw.githubusercontent.com/fmeiraf/novo/main/public/novo_logo.png" alt="novo" width="160" />

# novo

**Spin up Python experiments in seconds, from anywhere in your terminal.**

Install once with `uv`, then use `novo` from any directory to scaffold isolated, git-tracked Python experiments from reusable seed templates — drive it from the command line or a built-in TUI.

[![PyPI](https://img.shields.io/pypi/v/novo?style=flat-square&color=5DE4C7)](https://pypi.org/project/novo/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Built with uv](https://img.shields.io/badge/built%20with-uv-DE5FE9?style=flat-square)](https://docs.astral.sh/uv/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Changelog](https://img.shields.io/badge/CHANGELOG-md-blue?style=flat-square)](CHANGELOG.md)

</div>

---

## Install

novo is distributed as a [uv tool](https://docs.astral.sh/uv/concepts/tools/) — installed once into an isolated environment and exposed on your `PATH`.

**Prerequisite:** [`uv`](https://docs.astral.sh/uv/getting-started/installation/) and `git`.

```bash
# from PyPI
uv tool install novo

# or from this repo
uv tool install git+https://github.com/fmeiraf/novo
```

If `novo` isn't found after install, run `uv tool update-shell` once to add `~/.local/bin` to your `PATH`.

```bash
novo --version
```

That's it — the novo source tree is no longer needed. Use `novo` from any directory.

---

## First steps

### 1. Pick a workspace (optional)

novo stores experiments in a **workspace** — a directory marked with `.novo/` (same pattern as git's `.git/`). You don't have to set one up to get started: `novo new` works from any directory.

When you run any `novo` command, it resolves the active workspace in this order:

1. **cwd discovery** — walks up from the current directory looking for a `.novo/` marker. First hit wins.
2. **configured home** — if nothing is found, falls back to `workspace.path` in `~/.config/novo/config.toml` (only if you've set it).
3. **auto-detached** — if neither resolves, novo runs in detached mode against the current directory. `novo new` drops a self-contained experiment in cwd; read-only commands refuse with a `novo init` tip.

So `novo new churn-analysis` in a brand-new terminal just works — the experiment lands right next to you, as its own self-contained project. novo prints a one-line hint the first time so you know what happened:

```
ℹ no workspace found here — running in detached mode (run `novo init` to set up a workspace).
```

Want experiments to live in a specific tree (e.g. one per project)? Turn any directory into a workspace:

```bash
cd ~/code/experiments
novo init
```

`novo init` writes the `.novo/` marker and initializes the directory as a git repo. From then on, every `novo` command run inside that tree (or any subdirectory) operates on that workspace.

You can also point at a workspace explicitly with `--workspace <path>` or `NOVO_WORKSPACE=<path>`, or force detached mode with `--detached` (see [Detached mode](#detached-mode)).

### 2. Create your first experiment

```bash
novo new image-classifier --tag ml --desc "ResNet experiments"
```

novo creates a date-prefixed directory inside your workspace, sets up a `uv` project, applies the default seed, and commits the result.

### 3. Set up a seed (optional)

Seeds are reusable project templates — your favorite stack, scripts, and config files copied into every new experiment.

```bash
novo seed list                      # see what's available
novo seed init data-science         # scaffold a new empty seed
```

This creates `~/.local/share/novo/seeds/data-science/` with a `seed.toml` manifest and a `template/` directory. Edit the manifest to declare dependencies and post-create hooks:

```toml
[seed]
name = "data-science"
description = "Numpy + pandas + jupyter starter"

[seed.dependencies]
packages = ["numpy", "pandas", "jupyter"]

[seed.post_create]
commands = ["mkdir notebooks"]
```

Drop starter files into `template/` — they'll be copied into every new experiment that uses the seed:

```bash
novo new churn-analysis --seed data-science
```

### 4. Use seeds from a team registry (optional)

A **remote seed registry** is a git repo whose top-level subdirectories each contain a seed. One repo can hold many seeds:

```
team-seeds/
├── etl/
│   ├── seed.toml
│   └── template/
├── ml-experiment/
│   ├── seed.toml
│   └── template/
└── ...
```

Link it once with a local name:

```bash
novo seed link git@github.com:team/novo-seeds.git --name team
```

Every seed in the registry is now available as `remote:team/<seed-name>`:

```bash
novo new pricing-model --seed remote:team/ml-experiment
novo seed sync team        # pull updates later
novo seed unlink team      # drop the link
```

See [`docs/seeds.md`](docs/seeds.md) for scope resolution, identifier syntax, and how to structure a registry repo.

---

## Configuration

novo works out of the box, but a handful of settings let you tailor the defaults. They live in a single TOML file at `~/.config/novo/config.toml` (XDG-compliant; the exact path depends on your OS).

| Key | Type | Default | What it does |
|-----|------|---------|--------------|
| `workspace.path` | str | `""` (none) | Optional "home" workspace used when cwd discovery finds nothing. Empty = no home workspace; commands auto-detach in cwd. Set explicitly with `novo config set workspace.path <path>`. |
| `defaults.seed` | str | `"default"` | Seed used when `novo new` is called without `--seed`. Accepts scoped forms (e.g. `"user:data-science"`, `"remote:team/etl"`). |
| `defaults.python` | str | `""` (system) | Python version passed to `uv init` for new experiments (e.g. `"3.12"`). Override per-experiment with `--python`. |
| `defaults.auto_commit` | bool | `true` | Auto-commit the workspace on `novo new` / `novo delete`. |
| `defaults.detached_git` | bool | `true` | In detached mode, init a git repo inside each created experiment and commit. |
| `naming.date_prefix` | bool | `true` | Prefix experiment directories with today's date (`2026-05-06-foo`). Skip per-experiment with `--no-date`. |
| `[[seeds.remotes]]` | table-list | `[]` | Linked remote seed registries. Managed via `novo seed link / unlink`. See [`docs/seeds.md`](docs/seeds.md) for registry layout. |

### Inspecting and changing settings

```bash
novo config show                          # table of all keys
novo config get defaults.python           # read one key
novo config set defaults.python 3.12      # write one key
novo config set naming.date_prefix false  # accepts true/false, yes/no, 1/0, on/off
```

You can also edit `~/.config/novo/config.toml` directly:

```toml
[workspace]
path = "/Users/me/code/experiments"

[defaults]
seed = "user:data-science"
python = "3.12"
auto_commit = true
detached_git = true

[naming]
date_prefix = true

[[seeds.remotes]]
name = "team"
url = "git@github.com:team/novo-seeds.git"
ref = ""   # empty = follow the cloned branch
```

### Pinning a Python version

A seed itself can't declare a Python version today — it's resolved per-experiment in this order:

1. `--python` flag on `novo new`
2. `defaults.python` in `config.toml`
3. Whatever `uv` picks as the system default

So to make every new experiment use 3.12 by default:

```bash
novo config set defaults.python 3.12
novo new quick-test          # uses 3.12
novo new legacy --python 3.10  # one-off override
```

---

## The TUI

Run `novo` with no arguments to launch the interactive terminal UI — a Textual app for browsing, searching, and managing experiments without memorizing flags.

```
 ┌─ Experiments ─────────────┐ ┌─ Details ──────────────────┐
 │  > 2026-04-21-transformer  │ │  Name: transformer-exp     │
 │    2026-04-20-image-cls    │ │  Seed: ml-stack            │
 │    2026-04-19-data-clean   │ │  Tags: nlp, pytorch        │
 └────────────────────────────┘ └────────────────────────────┘
  n new  d delete  s seeds  / search  Enter open  ? help  q quit
```

| Key | Action |
|-----|--------|
| `n` | Create new experiment |
| `d` | Delete selected |
| `s` | Switch to Seeds tab |
| `e` | Switch to Experiments tab |
| `/` | Search |
| `Enter` | Open experiment in a new terminal window |
| `j` / `k` | Navigate (vim-style) |
| `?` | Help |
| `q` | Quit |

Extra bindings on the **Seeds tab**: `N` scaffold seed, `l` link remote registry, `u` unlink, `r` sync remotes, `t` focus the template tree.

See [`docs/tui.md`](docs/tui.md) for the full screen and widget breakdown.

---

## Detached mode

Sometimes you don't want a workspace at all — just a one-off, self-contained experiment wherever you happen to be standing. That's what `--detached` is for.

```bash
cd ~/scratch
novo --detached new spike-idea
```

What you get:

- A fresh project directory at `~/scratch/spike-idea/` with its own `uv` env and seed-applied files.
- Its own git repo + initial commit (when `defaults.detached_git = true`, the default).
- No registration anywhere — novo's workspace listing won't track it. `novo list / info / search / delete / open` deliberately refuse under `--detached` to keep the boundary clear.

Use `--at <path>` to drop the experiment somewhere other than cwd:

```bash
novo --detached new spike-idea --at ~/tmp
```

Running `novo --detached` with no subcommand launches a minimal TUI landing screen with the actions that make sense outside a workspace: new experiment here, link a remote registry, init a workspace here, browse seeds (CLI hint).

Drop `--detached` (or run `novo init` once in that directory) when you want to go back to workspace mode.

---

## Everyday commands

```bash
novo                                       # launch the interactive TUI
novo new <name>                            # create an experiment
novo list                                  # list experiments
novo info [name]                           # workspace summary, or details for one experiment
novo search <query>                        # fuzzy search across name, description, tags
novo open <name>                           # cd into an experiment (needs shell integration)
novo delete <name>
novo init [path]                           # write a `.novo/` marker at path (default cwd)
novo seed list | init <name>               # browse / scaffold seeds
novo seed link <url>                       # link a remote seed registry (idempotent)
novo seed sync [<name>] | unlink <name>    # refresh or remove a linked remote
novo config show | get <key> | set <key> <value>
novo --workspace <path> <cmd>              # operate on a specific workspace
novo --detached new <name>                 # create a self-contained experiment in cwd
```

For `novo open` to actually `cd`, add this to your `~/.zshrc` / `~/.bashrc`:

```bash
eval "$(novo --shell-init)"
```

---

## Updating & uninstalling

```bash
uv tool upgrade novo
uv tool uninstall novo
```

---

## Documentation

Deeper docs live in [`docs/`](docs/):

| Document | Description |
|----------|-------------|
| [architecture.md](docs/architecture.md) | Layers, data flow, project structure |
| [cli.md](docs/cli.md) | All CLI commands and flags |
| [tui.md](docs/tui.md) | Textual app, screens, keybindings |
| [core.md](docs/core.md) | Experiment, seed, config, workspace, remote, git logic |
| [seeds.md](docs/seeds.md) | Seed scopes, identifier syntax, remote sync workflow |
| [models.md](docs/models.md) | Pydantic schemas |
| [development.md](docs/development.md) | Local dev setup |
| [testing.md](docs/testing.md) | Test layout and conventions |

---

## Development

Work on novo itself with an editable install so changes are picked up immediately:

```bash
git clone https://github.com/fmeiraf/novo
cd novo
uv tool install --editable .
uv run pytest
```

---

## License

[MIT](LICENSE)
