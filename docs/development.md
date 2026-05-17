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
uv run novo seed list                                         # grouped by scope
uv run novo seed init my-seed --scope user                    # scaffold an empty seed
uv run novo seed link git@github.com:team/seeds.git --name team
uv run novo seed sync team
uv run novo seed unlink team
uv run novo seed create my-seed --from smoke-test
uv run novo seed remove my-seed
```

### Workspace modes

```bash
# Workspace mode (default): cwd discovery or XDG fallback.
uv run novo new my-exp

# Pin a specific workspace.
uv run novo --workspace /tmp/scratch new my-exp

# Detached: self-contained experiment in cwd (or --at <dir>), own git repo.
uv run novo --detached new my-exp
uv run novo --detached new my-exp --at /tmp
```

### TUI

```bash
uv run novo               # workspace mode
uv run novo --detached    # minimal-mode landing screen
```

Key bindings: `n` new, `d` delete, `s` seeds, `e` experiments, `/` search, `q` quit. Seeds tab adds: `N` new seed, `l` link remote, `u` unlink, `r` sync remotes, `t` focus tree.
