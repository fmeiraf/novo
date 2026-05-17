<div align="center">

<img src="https://raw.githubusercontent.com/fmeiraf/novo/main/public/novo_logo.png" alt="novo" width="160" />

# novo

**Spin up Python experiments in seconds, from anywhere in your terminal.**

Install once with `uv`, then use `novo` from any directory to scaffold isolated, git-tracked Python experiments from reusable seed templates — drive it from the command line or a built-in TUI.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Built with uv](https://img.shields.io/badge/built%20with-uv-DE5FE9?style=flat-square)](https://docs.astral.sh/uv/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

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

### 1. Set up a workspace

A workspace is any directory containing a `.novo/` marker — the same pattern as git's `.git/`. Multiple workspaces are supported; novo picks one per invocation via cwd discovery (walks up looking for `.novo/`), then falls back to a configured `workspace.path` or the XDG default (`~/.local/share/novo/workspace/`).

```bash
cd ~/code/experiments    # or wherever you want them
novo init
```

`novo init` writes the `.novo/` marker and initializes the directory as a git repo. Skip it entirely and novo will create + use the XDG default the first time you run `novo new`.

You can also point at a workspace explicitly with `--workspace <path>` or `NOVO_WORKSPACE=<path>`, or operate outside any workspace with `--detached` (see [detached mode](#detached-mode) below).

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

---

## Configuration

novo works out of the box, but a handful of settings let you tailor the defaults. They live in a single TOML file at `~/.config/novo/config.toml` (XDG-compliant; the exact path depends on your OS).

| Key | Type | Default | What it does |
|-----|------|---------|--------------|
| `workspace.path` | str | `""` (XDG default) | Optional "home" workspace used when cwd discovery finds nothing. Empty falls back to `~/.local/share/novo/workspace/`. Set explicitly with `novo config set workspace.path <path>`. |
| `defaults.seed` | str | `"default"` | Seed used when `novo new` is called without `--seed`. Accepts scoped forms (e.g. `"user:data-science"`, `"remote:team/etl"`). |
| `defaults.python` | str | `""` (system) | Python version passed to `uv init` for new experiments (e.g. `"3.12"`). Override per-experiment with `--python`. |
| `defaults.auto_commit` | bool | `true` | Auto-commit the workspace on `novo new` / `novo delete`. |
| `defaults.detached_git` | bool | `true` | In detached mode, init a git repo inside each created experiment and commit. |
| `naming.date_prefix` | bool | `true` | Prefix experiment directories with today's date (`2026-05-06-foo`). Skip per-experiment with `--no-date`. |
| `[[seeds.remotes]]` | table-list | `[]` | Linked remote seed registries. Managed via `novo seed link / unlink`. |

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

### Detached mode

`novo --detached` skips workspace lookup entirely:

- **CLI:** `novo --detached new <name>` creates a self-contained experiment in `(--at <path> or cwd)/<name>`. With `defaults.detached_git = true` (default), each experiment gets its own git repo and initial commit. `novo list/info/search/delete/open` refuse cleanly under `--detached`.
- **TUI:** `novo --detached` launches a minimal landing screen with direct actions: new experiment here, link remote, initialize workspace here, browse seeds (CLI hint).

Drop `--detached` (or run `novo init` once) to get back to workspace mode.

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
