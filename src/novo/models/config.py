"""NovoConfig pydantic model."""

from pydantic import BaseModel, Field


class WorkspaceConfig(BaseModel):
    """Workspace configuration."""

    path: str = ""  # Empty = XDG default


class DefaultsConfig(BaseModel):
    """Default settings."""

    seed: str = "default"
    auto_commit: bool = True
    python: str = ""  # Empty = system default


class NamingConfig(BaseModel):
    """Naming configuration."""

    date_prefix: bool = True


class NovoConfig(BaseModel):
    """Global novo configuration, stored in config.toml."""

    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    naming: NamingConfig = Field(default_factory=NamingConfig)
