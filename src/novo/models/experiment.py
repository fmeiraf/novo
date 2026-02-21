"""Experiment pydantic model."""

from datetime import datetime

from pydantic import BaseModel, Field


class Experiment(BaseModel):
    """Metadata for a single experiment, stored in .novo.toml."""

    name: str
    seed: str = "default"
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    python: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    dir_name: str = ""  # The actual directory name (may include date prefix)
