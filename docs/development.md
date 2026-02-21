# Development

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (package manager)
- git

## Setup

```bash
git clone <repo-url>
cd novo
uv sync
```

This installs all runtime and dev dependencies in an isolated virtual environment.

## Commands

### Run

```bash
uv run novo              # Launch TUI (interactive mode)
uv run novo --help       # Show all CLI commands
uv run novo new my-exp   # Create an experiment
uv run novo list         # List experiments
uv run novo info my-exp  # Show experiment details
uv run novo search web   # Search experiments
uv run novo delete my-exp --force
```

### Test

```bash
uv run pytest                    # All tests
uv run pytest tests/test_core    # Core tests only
uv run pytest tests/test_cli     # CLI tests only
uv run pytest -x                 # Stop on first failure
uv run pytest -v                 # Verbose output
```

### Install locally

```bash
uv pip install -e .
novo --help              # Now available without `uv run`
```

## Manual Testing

Quick smoke test for a development cycle:

```bash
# Create an experiment
uv run novo new smoke-test --no-date --desc "testing" --tag test

# Verify it shows up
uv run novo list
uv run novo info smoke-test

# Search for it
uv run novo search testing

# Clean up
uv run novo delete smoke-test --force
```

### Seed commands

```bash
uv run novo seed list
uv run novo seed add https://github.com/user/seed-repo.git
uv run novo seed create my-seed --from smoke-test
uv run novo seed remove my-seed
```

### TUI

```bash
uv run novo   # Launches interactive TUI when no subcommand is given
```

Key bindings: `n` new, `d` delete, `s` seeds, `/` search, `q` quit.
