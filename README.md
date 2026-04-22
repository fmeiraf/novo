<div align="center">

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
# from PyPI (once published)
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

The workspace is a single git-tracked directory where all your experiments live.

```bash
cd ~/code/experiments    # or wherever you want them
novo init
```

This registers the current directory as your workspace and initializes it as a git repo. Skip it entirely and novo will use an XDG-compliant default (`~/.local/share/novo/workspace/`).

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
| `s` | Browse seeds |
| `/` | Search |
| `Enter` | Open experiment in a new terminal window |
| `j` / `k` | Navigate (vim-style) |
| `?` | Help |
| `q` | Quit |

See [`docs/tui.md`](docs/tui.md) for the full screen and widget breakdown.

---

## Everyday commands

```bash
novo                       # launch the interactive TUI
novo new <name>            # create an experiment
novo list                  # list experiments
novo info [name]           # workspace summary, or details for one experiment
novo search <query>        # fuzzy search across name, description, tags
novo open <name>           # cd into an experiment (needs shell integration)
novo delete <name>
novo seed list | init <name>
novo config show | get <key> | set <key> <value>
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
| [core.md](docs/core.md) | Experiment, seed, config, and git logic |
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
