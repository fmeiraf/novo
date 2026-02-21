"""Seed pydantic model."""

from pydantic import BaseModel, Field


class SeedDependencies(BaseModel):
    """Seed dependency configuration."""

    packages: list[str] = Field(default_factory=list)


class SeedPostCreate(BaseModel):
    """Post-creation commands."""

    commands: list[str] = Field(default_factory=list)


class SeedFiles(BaseModel):
    """File handling configuration."""

    exclude: list[str] = Field(default_factory=["__pycache__", "*.pyc", ".git"])


class Seed(BaseModel):
    """Seed manifest, parsed from seed.toml."""

    name: str
    description: str = ""
    dependencies: SeedDependencies = Field(default_factory=SeedDependencies)
    post_create: SeedPostCreate = Field(default_factory=SeedPostCreate)
    files: SeedFiles = Field(default_factory=SeedFiles)
    path: str = ""  # Resolved path to the seed directory (not in seed.toml)
    builtin: bool = False  # Whether this is a built-in seed
