# Testing

## Running Tests

```bash
uv run pytest                    # All tests
uv run pytest tests/test_core    # Core tests only
uv run pytest tests/test_cli     # CLI tests only
uv run pytest -x                 # Stop on first failure
uv run pytest -v                 # Verbose output
uv run pytest -k "test_create"   # Run tests matching pattern
```

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures (tmp_workspace, tmp_config)
├── test_core/
│   ├── test_config.py   # Config load/save roundtrip
│   └── test_experiment.py  # Experiment CRUD, search, dir naming
├── test_cli/
│   └── test_commands.py # CLI integration tests via CliRunner
└── test_tui/
    └── __init__.py      # Placeholder for future TUI tests
```

## Key Fixture: `tmp_workspace`

Defined in `conftest.py`. Creates temp directories and patches all XDG path functions so tests never touch real user data:

```python
@pytest.fixture
def tmp_workspace(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    monkeypatch.setattr("novo.utils.paths.config_dir", lambda: config_dir)
    monkeypatch.setattr("novo.utils.paths.data_dir", lambda: data_dir)
    monkeypatch.setattr("novo.utils.paths.config_file", lambda: config_dir / "config.toml")
    monkeypatch.setattr("novo.utils.paths.default_workspace_dir", lambda: workspace)
    monkeypatch.setattr("novo.utils.paths.seeds_dir", lambda: data_dir / "seeds")

    return workspace
```

Use `tmp_workspace` in any test that creates experiments, reads config, or otherwise touches the filesystem.

## Pattern: Mock `uv.uv_init`

Every test that calls `create()` (directly or via CLI) must mock `uv_init` to avoid running the real `uv` binary:

```python
from unittest.mock import patch

@patch("novo.core.experiment.uv.uv_init")
def test_create_experiment(mock_uv_init, tmp_workspace):
    exp = create(name="test-exp", no_date=True)
    assert exp.name == "test-exp"
    mock_uv_init.assert_called_once()
```

The mock target is always `novo.core.experiment.uv.uv_init` — patching where it's imported, not where it's defined.

## CLI Tests

CLI tests use Typer's `CliRunner` to invoke commands without spawning a subprocess:

```python
from typer.testing import CliRunner
from novo.cli import app

runner = CliRunner()

@patch("novo.core.experiment.uv.uv_init")
def test_new_command(mock_uv, tmp_workspace):
    result = runner.invoke(app, ["new", "test-proj", "--no-date"])
    assert result.exit_code == 0
    assert "test-proj" in result.output
```

## Writing New Tests

1. **Pick the right directory**: `test_core/` for business logic, `test_cli/` for CLI commands, `test_tui/` for TUI screens/widgets.
2. **Use `tmp_workspace`** if your test involves experiments, config, or workspace paths.
3. **Mock `uv.uv_init`** if your test creates experiments.
4. **Assert behavior, not implementation**: check that experiments exist, commands succeed, and output contains expected strings.
5. **Use `--no-date`** when creating experiments in tests to get deterministic directory names.
