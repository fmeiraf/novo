# CLI

Command-line interface built with [Typer](https://typer.tiangolo.com/). Formats output with [Rich](https://rich.readthedocs.io/).

## Entry Point

`novo.cli:app` (registered in `pyproject.toml`). When invoked without a subcommand, launches the TUI.

```
cli/
├── __init__.py     # Typer app, root callback, --workspace/--detached flags, TUI fallback
├── new.py          # novo new
├── list.py         # novo list
├── delete.py       # novo delete
├── search.py       # novo search
├── open.py         # novo open + hidden _open-path
├── info.py         # novo info
├── init.py         # novo init [path]
├── config.py       # novo config {show,get,set}
└── seed.py         # novo seed {list,init,link,sync,unlink,create,remove}
```

## Global Options

These attach to every subcommand via the root callback:

| Flag | Description |
|------|-------------|
| `--workspace <path>` / `-W` | Operate on a specific workspace (must be a directory; gets a `.novo/` marker if missing). Overrides cwd discovery and `NOVO_WORKSPACE`. |
| `--detached` | Force detached mode: ignore any workspace, operate against cwd. `novo new` makes a self-contained experiment; workspace-bound commands (list/info/search/delete/open) refuse. |
| `--shell-init` | Print shell function for `novo open`. |
| `--version` | Print version and exit. |

Environment variable `NOVO_WORKSPACE` is read as a fallback for `--workspace`.

## Commands

| Command | File | Description |
|---------|------|-------------|
| `novo new <name>` | `new.py` | Create experiment. Options: `--seed`, `--python`, `--desc`, `--tag`, `--no-date`, `--at` (detached only) |
| `novo init [path]` | `init.py` | Initialize a workspace by creating a `.novo/` marker at `path` (default cwd). Does **not** mutate global config. |
| `novo list` | `list.py` | List experiments in the resolved workspace. Options: `--sort`, `--tag`, `--json` |
| `novo delete <name>` | `delete.py` | Delete experiment. Options: `--force` |
| `novo search <query>` | `search.py` | Search by name/description/tags. Options: `--json` |
| `novo open <name>` | `open.py` | Open experiment dir (requires shell integration) |
| `novo info [name]` | `info.py` | Show experiment details, or workspace info if no name given |
| `novo seed list` | `seed.py` | List seeds, grouped by scope (WORKSPACE / USER / REMOTE: \<n> / BUILTIN). `--scope`, `--json` |
| `novo seed init <name>` | `seed.py` | Scaffold new empty seed. `--desc`, `--path`, `--scope local\|user` |
| `novo seed link <url>` | `seed.py` | Link a remote seed registry (clones to `~/.local/share/novo/remotes/<name>/`). `--name`, `--ref`. Idempotent. |
| `novo seed sync [<name>]` | `seed.py` | Pull one or all linked remotes. |
| `novo seed unlink <name>` | `seed.py` | Remove a linked remote (config entry + local clone). |
| `novo seed create <name>` | `seed.py` | Create seed from existing experiment. `--from` |
| `novo seed remove <name>` | `seed.py` | Remove user-installed seed |
| `novo config show \| get \| set` | `config.py` | Inspect or change config keys (registered scalars only) |
| `novo --shell-init` | `__init__.py` | Print shell function for `novo open` |

## Workspace resolution

Every command resolves which workspace to use in this order (handled in `core/workspace.current_workspace()`):

1. `--workspace <path>` flag
2. `NOVO_WORKSPACE` env var
3. Walk up from cwd looking for `.novo/`
4. Fall back to `config.workspace.path` or the XDG default (`~/.local/share/novo/workspace/`)

`--detached` short-circuits this; only `novo new` is meaningful in detached mode.

## Scoped seed selection on `novo new`

`--seed` accepts both bare and scoped forms; bare names go through resolution and may error on ambiguity.

```
novo new x --seed default                   # implicit, resolved
novo new x --seed local:my-seed             # explicit workspace local
novo new x --seed user:data-science         # explicit user-installed
novo new x --seed remote:team/etl           # explicit remote registry
novo new x --seed builtin:default           # explicit bundled
```

If the bare name exists in more than one scope:

```
$ novo new x --seed shared
ambiguous seed 'shared' found in: local:shared, user:shared.
Use an explicit scope like --seed local:shared.
```

`.novo.toml` always records the scoped identifier so the seed origin stays unambiguous afterwards.

## Patterns

**Lazy imports** — core modules are imported inside command functions, not at module level. Keeps CLI startup fast.

**Error handling** — each command wraps core calls in try/except, prints Rich-formatted messages, and exits with code 1 on failure.

**JSON output** — `list`, `search`, and `seed list` support `--json` for machine-readable output via `model_dump(mode="json")`. `seed list --json` includes `scope`, `remote`, `identifier`, and `path` per seed.

**Seed subcommands** — implemented as a nested `typer.Typer` attached via `app.add_typer(seed_app, name="seed")`.

**Shell integration** — `novo open` requires a shell function (printed by `--shell-init`) because a subprocess can't change the parent shell's directory.

**Detached guard** — workspace-bound commands call `require_workspace(<name>)` at entry and exit cleanly under `--detached`.
