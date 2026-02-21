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
    """Save config to config.toml."""
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump()
    with open(path, "wb") as f:
        tomli_w.dump(data, f)


def get_workspace_path(config: NovoConfig | None = None) -> Path:
    """Resolve the workspace path from config or default."""
    if config is None:
        config = load_config()

    if config.workspace.path:
        return Path(config.workspace.path)

    from novo.utils.paths import default_workspace_dir

    return default_workspace_dir()
