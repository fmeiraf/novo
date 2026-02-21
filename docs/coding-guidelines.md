# Coding Guidelines

## Code Style

- Formatter/linter: **ruff** (standard Python conventions)
- Type hints on all public function signatures
- Docstrings on modules and non-obvious functions

## Layer Separation

The codebase has four layers with strict boundaries:

| Layer | Directory | Can import | Cannot import |
|-------|-----------|-----------|---------------|
| CLI | `cli/` | `core`, `models`, `utils` | `tui` |
| TUI | `tui/` | `core`, `models`, `utils` | `cli` |
| Core | `core/` | `models`, `utils` | `cli`, `tui` |
| Models | `models/` | (stdlib only) | `cli`, `tui`, `core`, `utils` |
| Utils | `utils/` | (stdlib + deps) | `cli`, `tui`, `core`, `models` |

Key rules:
- **CLI and TUI never touch the filesystem directly.** They call core functions which handle all I/O.
- **Core is the only layer that reads/writes files**, manages the workspace, and runs subprocesses (via utils wrappers).
- **Models are pure data** — Pydantic schemas with no side effects.

## Naming Conventions

### Files
- Lowercase with underscores: `experiment_list.py`, `seed_manager.py`
- One module per concept: `core/experiment.py` handles all experiment operations

### Functions
- Public core functions: verb-based — `create()`, `list_all()`, `get()`, `delete()`, `search()`
- Private helpers: prefixed with underscore — `_make_dir_name()`, `_write_novo_toml()`
- CLI commands: match the subcommand name — `new()`, `list_cmd()`, `delete()`

### Models
- PascalCase classes: `Experiment`, `NovoConfig`, `Seed`
- Sub-models grouped with parent: `WorkspaceConfig`, `DefaultsConfig`, `NamingConfig`

## Error Handling

- **Exceptions bubble up from core.** Core functions raise standard Python exceptions (`FileExistsError`, `FileNotFoundError`, `ValueError`).
- **CLI catches and formats.** CLI command handlers wrap core calls in try/except and print user-friendly messages with Rich.
- **TUI catches and notifies.** TUI screens catch exceptions and show them via Textual's notification system.
- **No silent failures.** If an operation fails, it raises — never returns `None` where a value is expected.

## Testing Patterns

- **Mock `uv.uv_init`** in any test that creates experiments — avoids real `uv` calls and network access.
- **Use `tmp_workspace` fixture** for all tests that touch the filesystem — patches XDG paths to temp dirs.
- **Use `CliRunner`** from `typer.testing` for CLI integration tests.

See [testing.md](testing.md) for details.
