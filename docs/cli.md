# CLI

Command-line interface built with [Typer](https://typer.tiangolo.com/). Formats output with [Rich](https://rich.readthedocs.io/).

## Entry Point

`novo.cli:app` (registered in `pyproject.toml`). When invoked without a subcommand, launches the TUI.

```
cli/
├── __init__.py     # Typer app, --shell-init callback, TUI fallback
├── new.py          # novo new
├── list.py         # novo list
├── delete.py       # novo delete
├── search.py       # novo search
├── open.py         # novo open + hidden _open-path
├── info.py         # novo info
└── seed.py         # novo seed {list,init,add,create,remove}
```

## Commands

| Command | File | Description |
|---------|------|-------------|
| `novo new <name>` | `new.py` | Create experiment. Options: `--seed`, `--python`, `--desc`, `--tag`, `--no-date` |
| `novo list` | `list.py` | List experiments. Options: `--sort`, `--tag`, `--json` |
| `novo delete <name>` | `delete.py` | Delete experiment. Options: `--force` |
| `novo search <query>` | `search.py` | Search by name/description/tags. Options: `--json` |
| `novo open <name>` | `open.py` | Open experiment dir (requires shell integration) |
| `novo info [name]` | `info.py` | Show experiment details, or workspace info if no name given |
| `novo seed list` | `seed.py` | List available seeds |
| `novo seed init <name>` | `seed.py` | Scaffold new empty seed (`--desc`, `--path`) |
| `novo seed add <url>` | `seed.py` | Install seed from git URL |
| `novo seed create <name>` | `seed.py` | Create seed from experiment (`--from`) |
| `novo seed remove <name>` | `seed.py` | Remove user-installed seed |
| `novo --shell-init` | `__init__.py` | Print shell function for `novo open` |

## Patterns

**Lazy imports** — Core modules are imported inside command functions, not at module level. Keeps CLI startup fast.

**Error handling** — Each command wraps core calls in try/except, prints Rich-formatted messages, and exits with code 1 on failure.

**JSON output** — `list` and `search` support `--json` for machine-readable output via `model_dump(mode="json")`.

**Seed subcommands** — Implemented as a nested `typer.Typer` attached via `app.add_typer(seed_app, name="seed")`.

**Shell integration** — `novo open` requires a shell function (printed by `--shell-init`) because a subprocess can't change the parent shell's directory. A hidden `_open-path` command provides the raw path.
