# Models

Pydantic schemas shared across all layers. Pure data — no side effects, no filesystem access.

## Structure

```
models/
├── config.py       # NovoConfig + sub-models
├── experiment.py   # Experiment
└── seed.py         # Seed + sub-models
```

## NovoConfig (`models/config.py`)

Global configuration, persisted as `config.toml`.

```python
class NovoConfig(BaseModel):
    workspace: WorkspaceConfig   # path (empty = XDG default)
    defaults: DefaultsConfig     # seed, auto_commit, python
    naming: NamingConfig         # date_prefix
```

| Sub-model | Fields | Defaults |
|-----------|--------|----------|
| `WorkspaceConfig` | `path: str` | `""` (XDG default) |
| `DefaultsConfig` | `seed: str`, `auto_commit: bool`, `python: str` | `"default"`, `True`, `""` |
| `NamingConfig` | `date_prefix: bool` | `True` |

**TOML mapping:**

```toml
[workspace]
path = ""

[defaults]
seed = "default"
auto_commit = true
python = ""

[naming]
date_prefix = true
```

## Experiment (`models/experiment.py`)

Per-experiment metadata, persisted as `.novo.toml` inside each experiment directory.

```python
class Experiment(BaseModel):
    name: str
    seed: str
    tags: list[str]
    description: str
    python: str
    created_at: datetime
    dir_name: str
```

| Field | Description |
|-------|-------------|
| `name` | User-provided experiment name |
| `seed` | Seed template used |
| `tags` | User-provided tags for categorization |
| `description` | Free-text description |
| `python` | Python version (empty = system default) |
| `created_at` | Creation timestamp |
| `dir_name` | Filesystem directory name (with optional date prefix) |

## Seed (`models/seed.py`)

Seed manifest, read from `seed.toml` in each seed directory.

```python
class Seed(BaseModel):
    name: str
    description: str
    dependencies: SeedDependencies
    post_create: SeedPostCreate
    files: SeedFiles
    path: Path | None       # Resolved at runtime
    builtin: bool           # True for bundled seeds
```

| Sub-model | Fields | Purpose |
|-----------|--------|---------|
| `SeedDependencies` | `packages: list[str]` | Packages to install via `uv add` |
| `SeedPostCreate` | `commands: list[str]` | Shell commands to run after template copy |
| `SeedFiles` | `exclude: list[str]` | Glob patterns to skip during template copy |
