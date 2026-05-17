# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Workspace markers and multi-workspace support.** Any directory with a `.novo/` marker is a valid workspace (like `.git/`). `--workspace <path>` / `NOVO_WORKSPACE` flag/env pin a specific workspace; otherwise novo walks up from cwd looking for a marker, then falls back to `config.workspace.path` or the XDG default. `ensure_initialized()` silently migrates pre-marker workspaces on first touch.
- **Scope-aware seed resolution.** Seeds live in four scopes: `local` (`<workspace>/.novo/seeds/`), `user`, `remote`, and `builtin`. `--seed` accepts both bare names and explicit scoped forms (`local:foo`, `user:foo`, `remote:team/foo`, `builtin:foo`); bare names error on ambiguity. `.novo.toml` records the scoped identifier so seed origin stays unambiguous.
- **Detached mode.** `novo --detached` skips workspace lookup. `novo --detached new <name>` creates a self-contained experiment at `(--at <path> or cwd)/<name>` with its own git repo (gated on the new `defaults.detached_git` config knob). The other registry-bound commands refuse cleanly. TUI launches a minimal landing screen with direct actions.
- **Remote seed registries.** `novo seed link <url>` clones a git repo of seeds into `~/.local/share/novo/remotes/<name>/`; every subdirectory with a `seed.toml` surfaces as `remote:<name>/<seed>`. `novo seed sync [<name>]` pulls one or all; `novo seed unlink <name>` removes the config entry + clone. Idempotent.
- **TUI overhaul.** New `SeedPicker` widget (scope-grouped OptionList with type-ahead filter and `(default)` indicator); `NewExperimentScreen` uses it. New screens: `DetachedScreen` (minimal landing), `RemoteLinkScreen`, `NewSeedScreen`. Seeds tab gains scope grouping (reuses the picker's row builder) and `N`/`l`/`u`/`r` keybindings. Status bar gains a mode chip and a sync-note slot.
- **New CLI commands and flags:** `novo seed link/sync/unlink`, `novo seed init --scope`, `novo seed list --scope/--json`, `novo new --detached/--at`, `--workspace`/`-W` global flag, `defaults.detached_git` config key.
- **New `docs/seeds.md`** covering scopes, identifier syntax, and the remote sync workflow.

### Changed
- `novo init` now writes a `.novo/` marker at the target path instead of mutating `config.workspace.path`. To pin a default workspace, run `novo config set workspace.path <path>` explicitly.
- `novo seed list` output is grouped by scope (WORKSPACE / USER / REMOTE: \<name> / BUILTIN) with origin badges; `--json` includes `scope`, `remote`, `identifier`, and `path` per seed.
- `RemoteSeed.ref` defaults to `""` (follow the cloned branch) rather than `"main"`, so registries on `master` or other branches work without explicit pinning.

### Removed
- `novo seed add <url>` — replaced by `novo seed link` for multi-seed repos. To install a single-seed repo, either reshape it into a multi-seed layout or `git clone` into `~/.local/share/novo/seeds/<name>/` manually.

## [0.1.4] - 2026-05-06

### Changed
- Default seed's `.claude/CLAUDE.md` now imports the canonical root `AGENTS.md` via Claude Code's `@` import syntax instead of duplicating its content.

## [0.1.3] - 2026-05-06

### Added
- Default seed now scaffolds a root `AGENTS.md` (canonical agent instructions, read by pi and the agents.md spec).
- Default seed adds `skills/` directories under `.claude/`, `.agents/`, and a new `.pi/` for the pi coding agent.
- TUI experiment card and `novo info` show `.pi` and root `AGENTS.md` presence indicators.

### Changed
- Replaced unused `.agents/agents.toml` with `.agents/skills/` in the default seed.

## [0.1.2] - 2026-05-06

### Added
- `novo --version` flag.
- `__version__` exposed at `novo.__version__`, sourced from package metadata.
- README "Configuration" section documenting all `config.toml` keys, defaults, and the Python-version resolution order.

### Fixed
- TUI welcome screen crashed on launch with `AttributeError: 'NovoConfig' object has no attribute 'workspace_dir'`. The detail panel now resolves the workspace path via `get_workspace_path()`.

## [0.1.1] - 2026-04-30

First public release on PyPI.

### Added
- Core CLI: `new`, `list`, `info`, `search`, `delete`, `open`, `init`, `config`, `seed`.
- Built-in `default` seed with starter `.claude/` and `.agents/` directories.
- Interactive Textual TUI (launches when `novo` is run with no arguments) with experiment browser, search, and seed file preview.
- Trusted publishing pipeline (TestPyPI + PyPI) via GitHub Actions.

### Fixed
- Default seed's `.claude/settings.local.json` was missing from the published wheel because a global gitignore rule excluded it from CI checkouts.
