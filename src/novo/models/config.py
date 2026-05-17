"""NovoConfig pydantic model."""

from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceConfig(BaseModel):
    """Workspace configuration."""

    path: str = ""  # Empty = XDG default


class DefaultsConfig(BaseModel):
    """Default settings."""

    seed: str = "default"
    auto_commit: bool = True
    python: str = ""  # Empty = system default
    detached_git: bool = True  # Detached experiments get their own git repo


class NamingConfig(BaseModel):
    """Naming configuration."""

    date_prefix: bool = True


class RemoteSeed(BaseModel):
    """A linked remote seed registry (cloned git repo of multiple seeds)."""

    name: str
    url: str
    # Empty string = track whatever branch the clone is on. Set explicitly to
    # pin a branch/tag/SHA.
    ref: str = ""
    # Populated at runtime from <remote_dir>/.novo-remote.toml; not persisted
    # to the global config (the field is excluded on serialization).
    last_synced_at: datetime | None = None


class SeedsConfig(BaseModel):
    """Seed-related configuration sections (currently: linked remotes)."""

    remotes: list[RemoteSeed] = Field(default_factory=list)


class NovoConfig(BaseModel):
    """Global novo configuration, stored in config.toml."""

    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    naming: NamingConfig = Field(default_factory=NamingConfig)
    seeds: SeedsConfig = Field(default_factory=SeedsConfig)
