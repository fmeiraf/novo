# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
