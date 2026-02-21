"""uv subprocess wrapper."""

import subprocess
from pathlib import Path


def uv_init(directory: Path, python: str | None = None) -> None:
    """Run `uv init` in the given directory."""
    cmd = ["uv", "init", "--no-workspace"]
    if python:
        cmd.extend(["--python", python])
    subprocess.run(cmd, cwd=directory, check=True, capture_output=True, text=True)


def uv_add(directory: Path, packages: list[str]) -> None:
    """Run `uv add <packages>` in the given directory."""
    if not packages:
        return
    cmd = ["uv", "add"] + packages
    subprocess.run(cmd, cwd=directory, check=True, capture_output=True, text=True)


def list_python_versions() -> list[str]:
    """Get installed Python versions via `uv python list --only-installed`."""
    try:
        result = subprocess.run(
            ["uv", "python", "list", "--only-installed"],
            capture_output=True,
            text=True,
            check=True,
        )
        versions = []
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if parts:
                # Format: "cpython-3.12.0-..." or "3.12.0 ..."
                version_str = parts[0]
                if version_str.startswith("cpython-"):
                    version_str = version_str.split("-")[1]
                versions.append(version_str)
        return versions
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def install_python(version: str) -> None:
    """Install a Python version via `uv python install`."""
    subprocess.run(
        ["uv", "python", "install", version],
        check=True,
        capture_output=True,
        text=True,
    )
