"""XDG-compliant path resolution via platformdirs."""

from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "novo"


def config_dir() -> Path:
    """Return the novo config directory (~/.config/novo/)."""
    return Path(user_config_dir(APP_NAME))


def data_dir() -> Path:
    """Return the novo data directory (~/.local/share/novo/)."""
    return Path(user_data_dir(APP_NAME))


def config_file() -> Path:
    """Return the path to config.toml."""
    return config_dir() / "config.toml"


def default_workspace_dir() -> Path:
    """Return the default workspace directory."""
    return data_dir() / "workspace"


def seeds_dir() -> Path:
    """Return the user seeds directory."""
    return data_dir() / "seeds"


def builtin_seeds_dir() -> Path:
    """Return the built-in seeds directory (ships with package)."""
    return Path(__file__).parent.parent.parent / "seeds"
