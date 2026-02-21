"""Git subprocess wrapper."""

import subprocess
from pathlib import Path


def init(directory: Path) -> None:
    """Initialize a git repository."""
    subprocess.run(
        ["git", "init"],
        cwd=directory,
        check=True,
        capture_output=True,
        text=True,
    )


def add_and_commit(directory: Path, message: str, paths: list[str] | None = None) -> None:
    """Stage files and commit."""
    add_cmd = ["git", "add"]
    if paths:
        add_cmd.extend(paths)
    else:
        add_cmd.append(".")

    subprocess.run(add_cmd, cwd=directory, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=directory,
        check=True,
        capture_output=True,
        text=True,
    )


def remove_and_commit(directory: Path, target: str, message: str) -> None:
    """Remove a path and commit the removal."""
    subprocess.run(
        ["git", "rm", "-rf", target],
        cwd=directory,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=directory,
        check=True,
        capture_output=True,
        text=True,
    )


def is_git_repo(directory: Path) -> bool:
    """Check if a directory is inside a git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=directory,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
