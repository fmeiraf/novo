"""Config load/save."""

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from novo.models.config import NovoConfig
from novo.utils.paths import config_file


def load_config() -> NovoConfig:
    """Load config from config.toml, creating defaults if missing."""
    path = config_file()
    if not path.exists():
        return NovoConfig()

    with open(path, "rb") as f:
        data = tomllib.load(f)

    return NovoConfig(**data)


def save_config(config: NovoConfig) -> None:
    """Save config to config.toml.

    Per-remote `last_synced_at` lives in `<remote_dir>/.novo-remote.toml`
    and is excluded here so the global config only holds the link spec.
    """
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(
        exclude={"seeds": {"remotes": {"__all__": {"last_synced_at"}}}}
    )
    with open(path, "wb") as f:
        tomli_w.dump(data, f)


def get_workspace_path(config: NovoConfig | None = None) -> Path | None:
    """Return the configured `workspace.path`, or None if unset.

    Returns None when the user hasn't set a "home" workspace explicitly — the
    XDG default is no longer a silent fallback. Callers wanting the resolved
    active workspace (with cwd discovery, override, etc.) should use
    `novo.core.workspace.current_workspace()`.
    """
    if config is None:
        config = load_config()

    if config.workspace.path:
        return Path(config.workspace.path)

    return None
