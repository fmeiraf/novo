# novo

A terminal tool for managing experimental Python projects.

## Commands

```bash
uv sync                        # Install dependencies
uv run novo                    # Run novo (launches TUI)
uv run novo --help             # Show CLI help
uv run novo new <name>         # Create experiment
uv run novo list               # List experiments
uv run novo info [name]        # Show experiment or workspace info
uv run novo search <query>     # Search experiments
uv run novo delete <name>      # Delete experiment
uv run novo open <name>        # Open experiment directory
uv run novo seed list          # List available seeds
uv run pytest                  # Run all tests
uv run pytest tests/test_core  # Run core tests only
uv run pytest -x               # Stop on first failure
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture.md](docs/architecture.md) | Project structure, layers, data flow |
| [docs/development.md](docs/development.md) | Setup, prerequisites, dev workflow |
| [docs/coding-guidelines.md](docs/coding-guidelines.md) | Code style, patterns, conventions |
| [docs/testing.md](docs/testing.md) | Test structure, fixtures, patterns |
| [docs/cli.md](docs/cli.md) | CLI commands, Typer app, output patterns |
| [docs/tui.md](docs/tui.md) | Textual app, screens, widgets, keybindings |
| [docs/core.md](docs/core.md) | Business logic: experiment, seed, config, git |
| [docs/models.md](docs/models.md) | Pydantic schemas: NovoConfig, Experiment, Seed |
| [docs/utils.md](docs/utils.md) | XDG paths, uv wrapper, shell integration |

## Core Principles

1. **Creating an experiment should take seconds.** One command sets up a full Python environment with uv, git, and seed templates.
2. **Seeds make novo extensible without code changes.** Users add new templates as seed directories — no plugin API needed.
3. **Sensible defaults, minimal required config.** Works out of the box with XDG paths, auto-commit, and date-prefixed directories.

## Architecture

```
CLI (Typer)  ──→  Core  ←──  TUI (Textual)
                   ↓
                Models (Pydantic)
                   ↑
                 Utils
```

- **CLI** — Command handlers that parse arguments, call core functions, and format output with Rich.
- **TUI** — Interactive Textual app with screens and widgets for browsing experiments.
- **Core** — Business logic: experiment CRUD, seed management, config, git, workspace init.
- **Models** — Pydantic schemas for `NovoConfig`, `Experiment`, and `Seed`.
- **Utils** — XDG path resolution (`platformdirs`), `uv` subprocess wrapper, shell integration.

Entry point: `novo.cli:app` (defined in `pyproject.toml`).

## Commits

Format: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
Scopes: `cli`, `tui`, `core`, `models`, `utils`, `docs`
