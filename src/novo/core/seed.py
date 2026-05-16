"""Seed management with scope-aware resolution.

Scopes, in resolution order for implicit lookups:
    1. local    — `<workspace>/.novo/seeds/`
    2. user     — `~/.local/share/novo/seeds/`
    3. remote   — `~/.local/share/novo/remotes/<remote>/<seed>/`
    4. builtin  — bundled with the package

Listings always show every scope; resolution order only kicks in for an
unprefixed `--seed foo`. Ambiguity at the same name raises an error and
demands an explicit prefix.
"""

import fnmatch
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterator

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from novo.models.scoped_seed import VALID_SCOPES, Scope, ScopedSeed, parse_seed_identifier
from novo.models.seed import Seed
from novo.utils import uv
from novo.utils.paths import (
    builtin_seeds_dir,
    remotes_dir,
    seeds_dir,
    workspace_seeds_dir,
)


def _load_seed_from_dir(seed_dir: Path, builtin: bool = False) -> Seed | None:
    """Load a seed from a directory containing seed.toml."""
    toml_path = seed_dir / "seed.toml"
    if not toml_path.exists():
        return None

    with open(toml_path, "rb") as f:
        data = tomllib.load(f)

    seed_data = data.get("seed", {})
    for key in ("dependencies", "post_create", "files"):
        if f"seed.{key}" in data:
            seed_data[key] = data[f"seed.{key}"]
        elif key in data.get("seed", {}):
            pass

    seed_data["path"] = str(seed_dir)
    seed_data["builtin"] = builtin
    return Seed(**seed_data)


def _iter_scope(scope: Scope, workspace: Path | None) -> Iterator[ScopedSeed]:
    """Yield every seed found in a given scope."""
    if scope == "local":
        if workspace is None:
            return
        root = workspace_seeds_dir(workspace)
        if not root.exists():
            return
        for item in sorted(root.iterdir()):
            if item.is_dir():
                seed = _load_seed_from_dir(item)
                if seed:
                    yield ScopedSeed(seed=seed, scope="local")
        return

    if scope == "user":
        root = seeds_dir()
        if not root.exists():
            return
        for item in sorted(root.iterdir()):
            if item.is_dir():
                seed = _load_seed_from_dir(item)
                if seed:
                    yield ScopedSeed(seed=seed, scope="user")
        return

    if scope == "remote":
        root = remotes_dir()
        if not root.exists():
            return
        for remote in sorted(root.iterdir()):
            if not remote.is_dir():
                continue
            for item in sorted(remote.iterdir()):
                if item.is_dir():
                    seed = _load_seed_from_dir(item)
                    if seed:
                        yield ScopedSeed(seed=seed, scope="remote", remote=remote.name)
        return

    if scope == "builtin":
        root = builtin_seeds_dir()
        if not root.exists():
            return
        for item in sorted(root.iterdir()):
            if item.is_dir():
                seed = _load_seed_from_dir(item, builtin=True)
                if seed:
                    yield ScopedSeed(seed=seed, scope="builtin")
        return


def list_seeds(workspace: Path | None = None) -> list[ScopedSeed]:
    """List every seed across every scope, in resolution order.

    Pass `workspace` to enumerate local seeds for a specific workspace; if
    omitted, the current workspace (per cwd discovery / override) is used.
    """
    if workspace is None:
        from novo.core.workspace import current_workspace

        workspace = current_workspace()

    result: list[ScopedSeed] = []
    for scope in VALID_SCOPES:
        result.extend(_iter_scope(scope, workspace))
    return result


def resolve_seed(identifier: str, workspace: Path | None = None) -> ScopedSeed:
    """Resolve a seed identifier to a single ScopedSeed.

    Explicit prefixes (`local:foo`, `remote:team/foo`, ...) jump straight
    to the named scope. An unprefixed identifier walks the scope order
    (local → user → remote → builtin); if the same name exists in more
    than one scope, raises a ValueError demanding an explicit prefix.

    Raises:
        ValueError: identifier is malformed, ambiguous, or not found.
    """
    scope, remote_name, name = parse_seed_identifier(identifier)

    if workspace is None:
        from novo.core.workspace import current_workspace

        workspace = current_workspace()

    if scope is not None:
        for candidate in _iter_scope(scope, workspace):
            if candidate.seed.name != name:
                continue
            if scope == "remote" and candidate.remote != remote_name:
                continue
            return candidate

        target = (
            f"{scope}:{remote_name}/{name}" if scope == "remote" else f"{scope}:{name}"
        )
        raise ValueError(f"seed not found: {target}")

    matches: list[ScopedSeed] = []
    for candidate in list_seeds(workspace):
        if candidate.seed.name == name:
            matches.append(candidate)

    if not matches:
        raise ValueError(f"seed not found: {name}")

    if len(matches) > 1:
        suggestions = ", ".join(m.identifier for m in matches)
        raise ValueError(
            f"ambiguous seed {name!r} found in: {suggestions}. "
            f"Use an explicit scope like --seed {matches[0].identifier}."
        )

    return matches[0]


def get_seed(name: str, workspace: Path | None = None) -> Seed | None:
    """Back-compat helper: resolve a seed by name and return the underlying Seed."""
    try:
        return resolve_seed(name, workspace).seed
    except ValueError:
        return None


def apply_seed(identifier: str, target_dir: Path, workspace: Path | None = None) -> ScopedSeed | None:
    """Apply a seed (by scoped or unscoped identifier) to an experiment directory.

    Returns the resolved ScopedSeed, or None if the seed could not be found.
    Ambiguity errors propagate to the caller; missing-seed silently skips
    to preserve current behavior.
    """
    try:
        scoped = resolve_seed(identifier, workspace)
    except ValueError as err:
        if "ambiguous" in str(err):
            raise
        return None

    seed = scoped.seed
    seed_path = Path(seed.path)
    template_dir = seed_path / "template"

    if template_dir.exists():
        _copy_template(template_dir, target_dir, seed.files.exclude)

    if seed.dependencies.packages:
        uv.uv_add(target_dir, seed.dependencies.packages)

    for cmd in seed.post_create.commands:
        subprocess.run(cmd, shell=True, cwd=target_dir, check=False, capture_output=True)

    return scoped


def _copy_template(src: Path, dst: Path, exclude: list[str]) -> None:
    """Copy template files, skipping excluded patterns and not overwriting pyproject.toml."""
    for item in src.rglob("*"):
        rel = item.relative_to(src)

        if any(fnmatch.fnmatch(str(rel), pat) or fnmatch.fnmatch(item.name, pat) for pat in exclude):
            continue

        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            if target.name == "pyproject.toml" and target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def add_from_git(url: str, name: str | None = None) -> Seed:
    """Install a single-seed repo from a git URL into the user scope.

    Deprecated by `seed link` (phase 4) for multi-seed repositories.
    """
    user_seeds = seeds_dir()
    user_seeds.mkdir(parents=True, exist_ok=True)

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
        raise ValueError("Cloned repo does not contain a valid seed.toml")

    return seed


def create_from_experiment(experiment_dir: Path, name: str, description: str = "") -> Seed:
    """Create a new seed from an existing experiment directory (user scope)."""
    user_seeds = seeds_dir()
    user_seeds.mkdir(parents=True, exist_ok=True)

    target = user_seeds / name
    if target.exists():
        raise FileExistsError(f"Seed '{name}' already exists")

    target.mkdir(parents=True)
    template_dir = target / "template"
    template_dir.mkdir()

    exclude = {"__pycache__", ".git", ".venv", "*.pyc", ".novo.toml"}
    for item in experiment_dir.iterdir():
        if item.name in exclude or item.name.startswith(".venv"):
            continue
        dest = template_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, ignore=shutil.ignore_patterns(*exclude))
        else:
            shutil.copy2(item, dest)

    seed_data = {
        "seed": {
            "name": name,
            "description": description,
        }
    }
    with open(target / "seed.toml", "wb") as f:
        tomli_w.dump(seed_data, f)

    return _load_seed_from_dir(target)


def init_seed(
    name: str,
    description: str = "",
    path: Path | None = None,
    scope: Scope = "user",
    workspace: Path | None = None,
) -> ScopedSeed:
    """Scaffold a new empty seed.

    `scope` picks the destination directory:
        - `user` (default) → `~/.local/share/novo/seeds/<name>/`
        - `local`          → `<workspace>/.novo/seeds/<name>/`

    `path` overrides the scope and writes the seed at the given absolute path
    (the returned ScopedSeed is reported under the explicit `scope`).
    """
    if path is None:
        if scope == "local":
            if workspace is None:
                from novo.core.workspace import current_workspace

                workspace = current_workspace()
            root = workspace_seeds_dir(workspace)
            root.mkdir(parents=True, exist_ok=True)
            target = root / name
        elif scope == "user":
            root = seeds_dir()
            root.mkdir(parents=True, exist_ok=True)
            target = root / name
        else:
            raise ValueError(f"cannot init a {scope!r} seed; use local or user")
    else:
        target = path

    if target.exists():
        raise FileExistsError(f"Seed '{name}' already exists")

    target.mkdir(parents=True)
    (target / "template").mkdir()

    seed_data = {"seed": {"name": name, "description": description}}
    toml_content = tomli_w.dumps(seed_data)
    toml_content += (
        "\n"
        "# [seed.dependencies]\n"
        '# packages = ["numpy", "pandas"]\n'
        "\n"
        "# [seed.post_create]\n"
        '# commands = ["echo hello"]\n'
        "\n"
        "# [seed.files]\n"
        '# exclude = ["__pycache__", "*.pyc", ".git"]\n'
    )
    (target / "seed.toml").write_text(toml_content)

    seed = _load_seed_from_dir(target)
    return ScopedSeed(seed=seed, scope=scope)


def remove_seed(name: str) -> bool:
    """Remove a user-installed seed."""
    user_seeds = seeds_dir()
    target = user_seeds / name
    if not target.exists():
        return False

    seed = _load_seed_from_dir(target)
    if seed and seed.builtin:
        return False

    shutil.rmtree(target)
    return True
