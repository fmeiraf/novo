"""Thin git wrappers and metadata storage for linked remote seed registries."""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

METADATA_FILE = ".novo-remote.toml"


def clone(url: str, target: Path, ref: str | None = None) -> None:
    """Clone `url` into `target`. If `ref` is given, check out that ref afterwards."""
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", url, str(target)],
        check=True,
        capture_output=True,
        text=True,
    )
    if ref:
        subprocess.run(
            ["git", "checkout", ref],
            cwd=target,
            check=True,
            capture_output=True,
            text=True,
        )


def pull(repo_dir: Path, ref: str | None = None) -> None:
    """Fast-forward `repo_dir` to the latest of `ref` (or the current branch)."""
    if ref:
        subprocess.run(
            ["git", "fetch", "origin", ref],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "checkout", ref],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "reset", "--hard", f"origin/{ref}"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )


def read_metadata(remote_dir: Path) -> dict:
    """Read `<remote_dir>/.novo-remote.toml` (returns {} if missing)."""
    path = remote_dir / METADATA_FILE
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def write_metadata(remote_dir: Path, last_synced_at: datetime) -> None:
    """Persist sync timestamp to `<remote_dir>/.novo-remote.toml`."""
    remote_dir.mkdir(parents=True, exist_ok=True)
    data = {"last_synced_at": last_synced_at.isoformat()}
    with open(remote_dir / METADATA_FILE, "wb") as f:
        tomli_w.dump(data, f)


def read_last_synced_at(remote_dir: Path) -> datetime | None:
    """Read just the `last_synced_at` timestamp from the metadata file."""
    raw = read_metadata(remote_dir).get("last_synced_at")
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None
