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
from datetime import datetime
from pathlib import Path
from typing import Iterator

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from novo.models.config import RemoteSeed
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


def _default_remote_name(url: str) -> str:
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name


def list_remotes() -> list[RemoteSeed]:
    """List every linked remote, populating `last_synced_at` from disk."""
    from novo.core.config import load_config
    from novo.core.remote import read_last_synced_at

    config = load_config()
    out: list[RemoteSeed] = []
    for entry in config.seeds.remotes:
        synced = read_last_synced_at(remotes_dir() / entry.name)
        out.append(
            RemoteSeed(name=entry.name, url=entry.url, ref=entry.ref, last_synced_at=synced)
        )
    return out


def link_remote(url: str, name: str | None = None, ref: str | None = None) -> RemoteSeed:
    """Register and clone a remote seed registry.

    Re-linking an existing name updates the registered url/ref and reuses
    the existing clone (idempotent). The remote is cloned into
    `~/.local/share/novo/remotes/<name>/`.
    """
    from novo.core.config import load_config, save_config
    from novo.core.remote import clone, write_metadata

    if name is None:
        name = _default_remote_name(url)
    if not name:
        raise ValueError(f"could not derive remote name from url: {url!r}")

    ref_value = ref or ""  # empty = follow the cloned branch

    config = load_config()
    existing = {r.name: r for r in config.seeds.remotes}

    target = remotes_dir() / name
    if name in existing:
        existing[name].url = url
        existing[name].ref = ref_value
    else:
        config.seeds.remotes.append(RemoteSeed(name=name, url=url, ref=ref_value))

    if not target.exists():
        clone(url, target, ref=ref_value or None)

    save_config(config)
    now = datetime.now()
    write_metadata(target, now)
    return RemoteSeed(name=name, url=url, ref=ref_value, last_synced_at=now)


def sync_remote(name: str | None = None) -> list[tuple[str, bool, str]]:
    """Pull one or all linked remotes. Returns (name, ok, message) per remote."""
    from novo.core.remote import pull, write_metadata

    remotes = list_remotes()
    if name is not None:
        remotes = [r for r in remotes if r.name == name]
        if not remotes:
            raise ValueError(f"unknown remote: {name}")

    results: list[tuple[str, bool, str]] = []
    for remote in remotes:
        target = remotes_dir() / remote.name
        if not target.exists():
            results.append((remote.name, False, "missing clone; re-link to recreate"))
            continue
        try:
            pull(target, ref=remote.ref or None)
            now = datetime.now()
            write_metadata(target, now)
            count = sum(1 for s in _iter_scope("remote", workspace=None) if s.remote == remote.name)
            results.append((remote.name, True, f"pulled ✓ {count} seed{'s' if count != 1 else ''}"))
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip() or str(exc)
            results.append((remote.name, False, stderr.splitlines()[-1] if stderr else "git pull failed"))
    return results


def unlink_remote(name: str) -> bool:
    """Remove a remote from config and delete its clone. Returns False if unknown."""
    from novo.core.config import load_config, save_config

    config = load_config()
    before = len(config.seeds.remotes)
    config.seeds.remotes = [r for r in config.seeds.remotes if r.name != name]
    if len(config.seeds.remotes) == before:
        return False
    save_config(config)

    target = remotes_dir() / name
    if target.exists():
        shutil.rmtree(target)
    return True


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
            if workspace is None:
                raise ValueError(
                    "--scope local requires a workspace; run `novo init` first "
                    "or use --scope user."
                )
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
