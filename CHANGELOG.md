# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `novo --version` flag.
- `__version__` exposed at `novo.__version__`, sourced from package metadata.

## [0.1.1] - 2026-04-30

First public release on PyPI.

### Added
- Core CLI: `new`, `list`, `info`, `search`, `delete`, `open`, `init`, `config`, `seed`.
- Built-in `default` seed with starter `.claude/` and `.agents/` directories.
- Interactive Textual TUI (launches when `novo` is run with no arguments) with experiment browser, search, and seed file preview.
- Trusted publishing pipeline (TestPyPI + PyPI) via GitHub Actions.

### Fixed
- Default seed's `.claude/settings.local.json` was missing from the published wheel because a global gitignore rule excluded it from CI checkouts.
