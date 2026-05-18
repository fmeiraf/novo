"""Workspace init, discovery, and resolution.

A workspace is any directory containing a `.novo/` marker. Multiple workspaces
are supported; `.novo/` is to novo what `.git/` is to git.

Resolution order on every CLI/TUI invocation:
1. `--detached` flag → detached mode, no workspace.
2. `--workspace` / `NOVO_WORKSPACE` override → that path.
3. Walk up from cwd looking for `.novo/`.
4. `config.workspace.path` if non-empty.
5. Otherwise → auto-detached at cwd.

The XDG default (`~/.local/share/novo/workspace/`) is NOT a silent fallback;
opt in by setting `workspace.path` to it explicitly.
"""

from pathlib import Path

from novo.core import git
from novo.core.config import load_config, save_config

MARKER_NAME = ".novo"

_workspace_override: Path | None = None
_detached_forced: bool = False


def set_workspace_override(path: Path | str | None) -> None:
    """Set a process-scoped workspace override (used by CLI --workspace / env)."""
    global _workspace_override
    _workspace_override = Path(path).resolve() if path else None


def get_workspace_override() -> Path | None:
    """Return the current process-scoped workspace override, if any."""
    return _workspace_override


def set_detached_forced(value: bool) -> None:
    """Set the process-scoped `--detached` flag.

    When forced, every command treats the invocation as detached regardless
    of whether a workspace could be discovered.
    """
    global _detached_forced
    _detached_forced = bool(value)


def is_detached_forced() -> bool:
    """True only when `--detached` was passed explicitly."""
    return _detached_forced


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


def current_workspace(cwd: Path | None = None) -> Path | None:
    """Resolve the active workspace path for this invocation, or None.

    Order: --workspace override → cwd walk-up → config.workspace.path.
    Returns None when nothing resolves (i.e. the invocation auto-detaches).

    Note: `--detached` forced is intentionally NOT consulted here — this
    returns *where the workspace would be* if you weren't detached. Use
    `is_detached()` / `resolve_mode()` to check effective mode.
    """
    if _workspace_override is not None:
        return _workspace_override

    found = discover(cwd)
    if found is not None:
        return found

    config = load_config()
    if config.workspace.path:
        return Path(config.workspace.path).resolve()

    return None


def is_detached(cwd: Path | None = None) -> bool:
    """True when running in detached mode — forced or inferred."""
    if _detached_forced:
        return True
    return current_workspace(cwd) is None


def is_auto_detached(cwd: Path | None = None) -> bool:
    """True when detached because nothing resolved (not from `--detached`).

    Lets the CLI surface a friendly hint only when the user didn't ask
    for detached mode explicitly.
    """
    return (not _detached_forced) and current_workspace(cwd) is None


def resolve_mode(cwd: Path | None = None) -> tuple[bool, Path | None]:
    """Return `(is_detached, workspace_or_None)` for the current invocation."""
    if _detached_forced:
        return True, None
    ws = current_workspace(cwd)
    return (ws is None, ws)


def ensure_initialized(target: Path | None = None) -> Path:
    """Ensure a workspace exists at `target` (or the resolved current workspace).

    Creates the directory if missing, writes the `.novo/` marker (with an
    empty per-workspace `config.toml` and `seeds/` dir), and initializes
    git on first creation. Idempotent — safe to call repeatedly.

    Raises:
        RuntimeError: when `target` is None and no workspace can be resolved
            (the invocation is auto-detached). Callers should check
            `is_detached()` before calling, or pass an explicit target.
    """
    if target is None:
        resolved = current_workspace()
        if resolved is None:
            raise RuntimeError(
                "no workspace resolved — pass a target, run `novo init`, "
                "or set workspace.path in config"
            )
        target = resolved
    workspace = Path(target).resolve()

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
