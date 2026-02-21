"""Workspace init and management."""

from pathlib import Path

from novo.core import git
from novo.core.config import get_workspace_path, load_config, save_config


def ensure_initialized() -> Path:
    """Ensure the workspace exists and is a git repo. Returns workspace path."""
    config = load_config()
    workspace = get_workspace_path(config)

    if not workspace.exists():
        workspace.mkdir(parents=True, exist_ok=True)

    if not git.is_git_repo(workspace):
        git.init(workspace)
        # Create .gitignore
        gitignore = workspace / ".gitignore"
        gitignore.write_text(
            "# Python\n__pycache__/\n*.pyc\n*.pyo\n.venv/\n*.egg-info/\ndist/\nbuild/\n"
        )
        git.add_and_commit(workspace, "novo: initialize workspace")

    # Save config if it doesn't exist yet
    from novo.utils.paths import config_file

    if not config_file().exists():
        save_config(config)

    return workspace
