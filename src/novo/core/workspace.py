"""Workspace init, discovery, and resolution.

A workspace is any directory containing a `.novo/` marker. Multiple workspaces
are supported; `.novo/` is to novo what `.git/` is to git.

Resolution order on every CLI/TUI invocation:
1. Explicit override (CLI `--workspace` or `NOVO_WORKSPACE` env), if set.
2. Walk up from cwd looking for `.novo/`.
3. Fall back to `config.workspace.path` or the XDG default workspace.
"""

from pathlib import Path

from novo.core import git
from novo.core.config import get_workspace_path, load_config, save_config

MARKER_NAME = ".novo"

_workspace_override: Path | None = None


def set_workspace_override(path: Path | str | None) -> None:
    """Set a process-scoped workspace override (used by CLI --workspace / env)."""
    global _workspace_override
    _workspace_override = Path(path).resolve() if path else None


def get_workspace_override() -> Path | None:
    """Return the current process-scoped workspace override, if any."""
    return _workspace_override


def discover(start: Path | None = None) -> Path | None:
    """Walk up from `start` (default: cwd) looking for a `.novo/` marker.

    Returns the workspace path (the directory containing `.novo/`), or None
    if no marker is found before reaching the filesystem root.
    """
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / MARKER_NAME).is_dir():
            return candidate
    return None


def current_workspace(cwd: Path | None = None) -> Path:
    """Resolve the active workspace path for this invocation.

    Order: override → cwd walk-up → config.workspace.path → XDG default.
    Always returns a path (never None); the caller is responsible for
    ensuring it actually exists/has a marker via `ensure_initialized`.
    """
    if _workspace_override is not None:
        return _workspace_override

    found = discover(cwd)
    if found is not None:
        return found

    return get_workspace_path(load_config())


def ensure_initialized(target: Path | None = None) -> Path:
    """Ensure a workspace exists at `target` (or the resolved current workspace).

    Creates the directory if missing, writes the `.novo/` marker (with an
    empty per-workspace `config.toml` and `seeds/` dir), and initializes
    git on first creation. Idempotent — safe to call repeatedly.

    Existing default workspaces from older versions get their `.novo/`
    marker silently added the first time this function touches them.
    """
    workspace = (target or current_workspace()).resolve()

    workspace.mkdir(parents=True, exist_ok=True)

    marker = workspace / MARKER_NAME
    if not marker.exists():
        marker.mkdir()
        (marker / "seeds").mkdir()
        (marker / "config.toml").write_text("")

    if not git.is_git_repo(workspace):
        git.init(workspace)
        gitignore = workspace / ".gitignore"
        gitignore.write_text(
            "# Python\n__pycache__/\n*.pyc\n*.pyo\n.venv/\n*.egg-info/\ndist/\nbuild/\n"
        )
        git.add_and_commit(workspace, "novo: initialize workspace")

    from novo.utils.paths import config_file

    if not config_file().exists():
        save_config(load_config())

    return workspace
