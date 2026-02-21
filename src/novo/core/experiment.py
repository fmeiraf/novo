"""Experiment CRUD operations."""

import shutil
import sys
from datetime import date, datetime
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from novo.core import git
from novo.core.config import load_config
from novo.core.workspace import ensure_initialized
from novo.models.experiment import Experiment
from novo.utils import uv


def _make_dir_name(name: str, use_date_prefix: bool) -> str:
    """Create directory name, optionally with date prefix."""
    if use_date_prefix:
        return f"{date.today().isoformat()}-{name}"
    return name


def _write_novo_toml(path: Path, experiment: Experiment) -> None:
    """Write .novo.toml metadata file."""
    data = {
        "experiment": {
            "name": experiment.name,
            "seed": experiment.seed,
            "tags": experiment.tags,
            "description": experiment.description,
            "python": experiment.python,
            "created_at": experiment.created_at.isoformat(),
        }
    }
    with open(path / ".novo.toml", "wb") as f:
        tomli_w.dump(data, f)


def _read_novo_toml(path: Path) -> Experiment | None:
    """Read .novo.toml and return an Experiment, or None if invalid."""
    toml_path = path / ".novo.toml"
    if not toml_path.exists():
        return None

    with open(toml_path, "rb") as f:
        data = tomllib.load(f)

    exp_data = data.get("experiment", {})
    if "created_at" in exp_data:
        exp_data["created_at"] = datetime.fromisoformat(exp_data["created_at"])
    exp_data["dir_name"] = path.name
    if "name" not in exp_data:
        exp_data["name"] = path.name

    return Experiment(**exp_data)


def create(
    name: str,
    seed_name: str | None = None,
    python: str | None = None,
    description: str = "",
    tags: list[str] | None = None,
    no_date: bool = False,
) -> Experiment:
    """Create a new experiment."""
    config = load_config()
    workspace = ensure_initialized()

    # Resolve settings
    seed = seed_name or config.defaults.seed
    python_version = python or config.defaults.python or None
    use_date = (not no_date) and config.naming.date_prefix
    dir_name = _make_dir_name(name, use_date)
    exp_dir = workspace / dir_name

    if exp_dir.exists():
        raise FileExistsError(f"Experiment directory already exists: {dir_name}")

    exp_dir.mkdir(parents=True)

    # Run uv init
    uv.uv_init(exp_dir, python=python_version)

    # Apply seed template
    from novo.core.seed import apply_seed

    apply_seed(seed, exp_dir)

    # Build experiment model
    experiment = Experiment(
        name=name,
        seed=seed,
        tags=tags or [],
        description=description,
        python=python_version or "",
        dir_name=dir_name,
    )

    # Write .novo.toml
    _write_novo_toml(exp_dir, experiment)

    # Git commit
    if config.defaults.auto_commit:
        git.add_and_commit(workspace, f"novo: create {name} (seed: {seed})")

    return experiment


def list_all(
    sort_by: str = "created",
    tag: str | None = None,
) -> list[Experiment]:
    """List all experiments in the workspace."""
    config = load_config()
    workspace = ensure_initialized()

    experiments = []
    for item in sorted(workspace.iterdir()):
        if not item.is_dir() or item.name.startswith("."):
            continue
        exp = _read_novo_toml(item)
        if exp is not None:
            if tag and tag not in exp.tags:
                continue
            experiments.append(exp)

    # Sort
    if sort_by == "name":
        experiments.sort(key=lambda e: e.name)
    elif sort_by == "created":
        experiments.sort(key=lambda e: e.created_at, reverse=True)
    elif sort_by == "modified":
        experiments.sort(
            key=lambda e: (workspace / e.dir_name).stat().st_mtime,
            reverse=True,
        )

    return experiments


def get(name: str) -> Experiment | None:
    """Get a single experiment by name (matches name or dir_name)."""
    workspace = ensure_initialized()
    for item in workspace.iterdir():
        if not item.is_dir() or item.name.startswith("."):
            continue
        exp = _read_novo_toml(item)
        if exp is not None and (exp.name == name or exp.dir_name == name or item.name == name):
            return exp
    return None


def get_path(name: str) -> Path | None:
    """Get the path to an experiment directory."""
    workspace = ensure_initialized()
    for item in workspace.iterdir():
        if not item.is_dir() or item.name.startswith("."):
            continue
        exp = _read_novo_toml(item)
        if exp is not None and (exp.name == name or exp.dir_name == name or item.name == name):
            return item
    return None


def delete(name: str) -> bool:
    """Delete an experiment."""
    config = load_config()
    workspace = ensure_initialized()

    exp_path = get_path(name)
    if exp_path is None:
        return False

    exp = _read_novo_toml(exp_path)
    exp_name = exp.name if exp else name

    if config.defaults.auto_commit and git.is_git_repo(workspace):
        git.remove_and_commit(workspace, exp_path.name, f"novo: delete {exp_name}")
    else:
        shutil.rmtree(exp_path)

    return True


def search(query: str) -> list[Experiment]:
    """Simple token-based fuzzy search across experiments."""
    all_exps = list_all()
    query_lower = query.lower()
    tokens = query_lower.split()

    scored = []
    for exp in all_exps:
        searchable = f"{exp.name} {exp.description} {' '.join(exp.tags)} {exp.seed}".lower()
        score = sum(1 for token in tokens if token in searchable)
        if score > 0:
            scored.append((score, exp))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [exp for _, exp in scored]
