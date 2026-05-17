# Models

Pydantic schemas shared across all layers. Pure data — no side effects, no filesystem access.

## Structure

```
models/
├── config.py       # NovoConfig + sub-models (incl. SeedsConfig + RemoteSeed)
├── experiment.py   # Experiment
├── scoped_seed.py  # ScopedSeed + parse_seed_identifier
└── seed.py         # Seed + sub-models
```

## NovoConfig (`models/config.py`)

Global configuration, persisted as `config.toml`.

```python
class NovoConfig(BaseModel):
    workspace: WorkspaceConfig    # path (empty = XDG default)
    defaults: DefaultsConfig      # seed, auto_commit, python, detached_git
    naming: NamingConfig          # date_prefix
    seeds: SeedsConfig            # remotes: list[RemoteSeed]
```

| Sub-model | Fields | Defaults |
|-----------|--------|----------|
| `WorkspaceConfig` | `path: str` | `""` (XDG default) |
| `DefaultsConfig` | `seed`, `auto_commit`, `python`, `detached_git` | `"default"`, `True`, `""`, `True` |
| `NamingConfig` | `date_prefix: bool` | `True` |
| `SeedsConfig` | `remotes: list[RemoteSeed]` | `[]` |
| `RemoteSeed` | `name`, `url`, `ref`, `last_synced_at` | —, —, `""` (follow clone), `None` |

`RemoteSeed.last_synced_at` is excluded from `save_config()` output — that field is read at runtime from `<remote_dir>/.novo-remote.toml`.

**TOML mapping:**

```toml
[workspace]
path = ""

[defaults]
seed = "default"
auto_commit = true
python = ""
detached_git = true

[naming]
date_prefix = true

[[seeds.remotes]]
name = "team"
url = "git@github.com:team/novo-seeds.git"
ref = ""             # "" = follow the cloned branch; set to pin a branch/tag/sha
```

## Experiment (`models/experiment.py`)

Per-experiment metadata, persisted as `.novo.toml` inside each experiment directory.

```python
class Experiment(BaseModel):
    name: str
    seed: str               # scoped identifier (e.g. "user:default", "remote:team/etl")
    tags: list[str]
    description: str
    python: str
    created_at: datetime
    dir_name: str
```

**Migration note:** experiments created before phase 2 store an unscoped seed name (e.g. `"default"`). These still display fine; scope-aware lookup runs lazily and treats them as bare identifiers (resolved via the implicit walk).

## Seed (`models/seed.py`)

Seed manifest, read from `seed.toml` in each seed directory.

```python
class Seed(BaseModel):
    name: str
    description: str
    dependencies: SeedDependencies
    post_create: SeedPostCreate
    files: SeedFiles
    path: str                # Resolved at runtime
    builtin: bool            # True for bundled seeds
```

| Sub-model | Fields | Purpose |
|-----------|--------|---------|
| `SeedDependencies` | `packages: list[str]` | Packages to install via `uv add` |
| `SeedPostCreate` | `commands: list[str]` | Shell commands to run after template copy |
| `SeedFiles` | `exclude: list[str]` | Glob patterns to skip during template copy |

## ScopedSeed (`models/scoped_seed.py`)

A seed paired with the scope it was discovered in.

```python
Scope = Literal["local", "user", "remote", "builtin"]

class ScopedSeed(BaseModel):
    seed: Seed
    scope: Scope
    remote: str | None        # set only when scope == "remote"
```

| Property | Returns |
|----------|---------|
| `identifier` | Canonical scoped string: `local:foo`, `user:foo`, `remote:team/foo`, `builtin:foo`. |

### `parse_seed_identifier(raw)`

Returns `(scope, remote, name)`:

| Input | Output |
|-------|--------|
| `"foo"` | `(None, None, "foo")` — implicit, needs `resolve_seed()` |
| `"local:foo"` | `("local", None, "foo")` |
| `"user:foo"` | `("user", None, "foo")` |
| `"builtin:foo"` | `("builtin", None, "foo")` |
| `"remote:team/foo"` | `("remote", "team", "foo")` |

Raises `ValueError` for malformed inputs (empty, unknown scope, `remote:` without `/`, etc.).
