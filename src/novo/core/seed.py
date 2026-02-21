"""Seed management."""

import fnmatch
import shutil
import subprocess
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from novo.models.seed import Seed
from novo.utils import uv
from novo.utils.paths import builtin_seeds_dir, seeds_dir


def _load_seed_from_dir(seed_dir: Path, builtin: bool = False) -> Seed | None:
    """Load a seed from a directory containing seed.toml."""
    toml_path = seed_dir / "seed.toml"
    if not toml_path.exists():
        return None

    with open(toml_path, "rb") as f:
        data = tomllib.load(f)

    seed_data = data.get("seed", {})
    # Flatten nested tables
    for key in ("dependencies", "post_create", "files"):
        if f"seed.{key}" in data:
            seed_data[key] = data[f"seed.{key}"]
        elif key in data.get("seed", {}):
            pass  # Already there

    seed_data["path"] = str(seed_dir)
    seed_data["builtin"] = builtin
    return Seed(**seed_data)


def list_seeds() -> list[Seed]:
    """List all available seeds (built-in + user-installed)."""
    result = []

    # Built-in seeds
    builtin = builtin_seeds_dir()
    if builtin.exists():
        for item in sorted(builtin.iterdir()):
            if item.is_dir():
                seed = _load_seed_from_dir(item, builtin=True)
                if seed:
                    result.append(seed)

    # User-installed seeds
    user_seeds = seeds_dir()
    if user_seeds.exists():
        for item in sorted(user_seeds.iterdir()):
            if item.is_dir():
                seed = _load_seed_from_dir(item, builtin=False)
                if seed:
                    result.append(seed)

    return result


def get_seed(name: str) -> Seed | None:
    """Get a seed by name."""
    for seed in list_seeds():
        if seed.name == name:
            return seed
    return None


def apply_seed(seed_name: str, target_dir: Path) -> None:
    """Apply a seed template to an experiment directory."""
    seed = get_seed(seed_name)
    if seed is None:
        return  # No seed found, skip silently

    seed_path = Path(seed.path)
    template_dir = seed_path / "template"

    if template_dir.exists():
        _copy_template(template_dir, target_dir, seed.files.exclude)

    # Install dependencies
    if seed.dependencies.packages:
        uv.uv_add(target_dir, seed.dependencies.packages)

    # Run post-create commands
    for cmd in seed.post_create.commands:
        subprocess.run(cmd, shell=True, cwd=target_dir, check=False, capture_output=True)


def _copy_template(src: Path, dst: Path, exclude: list[str]) -> None:
    """Copy template files, skipping excluded patterns and not overwriting pyproject.toml."""
    for item in src.rglob("*"):
        rel = item.relative_to(src)

        # Check exclusions
        if any(fnmatch.fnmatch(str(rel), pat) or fnmatch.fnmatch(item.name, pat) for pat in exclude):
            continue

        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            # Don't overwrite pyproject.toml (created by uv init)
            if target.name == "pyproject.toml" and target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def add_from_git(url: str, name: str | None = None) -> Seed:
    """Install a seed from a git repository."""
    user_seeds = seeds_dir()
    user_seeds.mkdir(parents=True, exist_ok=True)

    # Determine name from URL if not provided
    if name is None:
        name = url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]

    target = user_seeds / name
    if target.exists():
        raise FileExistsError(f"Seed '{name}' already exists")

    subprocess.run(
        ["git", "clone", url, str(target)],
        check=True,
        capture_output=True,
        text=True,
    )

    seed = _load_seed_from_dir(target)
    if seed is None:
        shutil.rmtree(target)
        raise ValueError(f"Cloned repo does not contain a valid seed.toml")

    return seed


def create_from_experiment(experiment_dir: Path, name: str, description: str = "") -> Seed:
    """Create a new seed from an existing experiment directory."""
    user_seeds = seeds_dir()
    user_seeds.mkdir(parents=True, exist_ok=True)

    target = user_seeds / name
    if target.exists():
        raise FileExistsError(f"Seed '{name}' already exists")

    target.mkdir(parents=True)
    template_dir = target / "template"
    template_dir.mkdir()

    # Copy relevant files from experiment
    exclude = {"__pycache__", ".git", ".venv", "*.pyc", ".novo.toml"}
    for item in experiment_dir.iterdir():
        if item.name in exclude or item.name.startswith(".venv"):
            continue
        dest = template_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, ignore=shutil.ignore_patterns(*exclude))
        else:
            shutil.copy2(item, dest)

    # Write seed.toml
    seed_data = {
        "seed": {
            "name": name,
            "description": description,
        }
    }
    with open(target / "seed.toml", "wb") as f:
        tomli_w.dump(seed_data, f)

    return _load_seed_from_dir(target)


def remove_seed(name: str) -> bool:
    """Remove a user-installed seed."""
    user_seeds = seeds_dir()
    target = user_seeds / name
    if not target.exists():
        return False

    # Don't allow removing built-in seeds
    seed = _load_seed_from_dir(target)
    if seed and seed.builtin:
        return False

    shutil.rmtree(target)
    return True
