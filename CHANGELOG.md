# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.3] - 2026-05-18

### Fixed
- TUI "New Experiment" modal clipped the bottom of the form (the "Skip date prefix" checkbox and the Create / Cancel buttons) on short terminals — including the default size most users see when launching `novo --detached` from a small split pane. The modal sized itself to `height: auto; max-height: 90%` with a plain `Vertical` body, so once content exceeded the cap there was no scrollbar and the clipped widgets were silently invisible. The form fields now live inside a `VerticalScroll` that takes `1fr` of the modal, with the buttons pinned to the bottom at a fixed height, so on any terminal size the action buttons stay reachable and the form scrolls if needed.
- SeedPicker opened scrolled past the first section. `_rebuild()` set `opts.highlighted = default_index` after populating the OptionList, and Textual's OptionList scrolls the viewport to keep the highlighted row visible — since the default lives at the bottom of the scope order (`local → user → remote → builtin`), the picker opened past the WORKSPACE / USER section headers, hiding the first line of the list. The picker now leaves `highlighted` unset on open and explicitly `scroll_home()`s the option list; the modal still falls back to the configured default when no row is selected (`seed_name=None` already triggers default-seed behaviour in `core.experiment.create`), and the `(default)` row badge continues to mark which seed will be used.

### Changed
- "New Experiment" modal is wider (100 cols, capped at 95% of the screen, up from 70). The previous 70-col width crammed seed rows — especially `[remote:<name>]` badges and longer descriptions — into truncated lines, and forced the form to scroll on terminals that should have been tall enough.
- `SeedPicker` (used by the modal and the Seeds tab) reads much more clearly as a first-time user: section headers now lead with a coloured block bar (`█ WORKSPACE`, `█ USER`, `█ REMOTE: <name>`, `█ BUILTIN`) in the scope's accent colour; entries are indented under the bar; a blank row separates adjacent sections; and the per-row `[scope]` badge picks up the same scope colour so users scrolling through a filtered view (where the header may be off-screen) can still tell at a glance which scope a seed belongs to. The picker's option list is also two rows taller (12 vs 10) to make up for the new spacer rows.
- New Experiment modal no longer hides the WORKSPACE section on `--detached` launches. Previously the modal forced `hide_workspace=is_detached()` on the SeedPicker, so running `novo --detached` from inside a workspace still stripped the entire WORKSPACE section — and with it the `[local]` badge — even though `current_workspace()` could happily resolve local seeds. The picker now uses the default `hide_workspace=False`; when the cwd is truly outside any workspace (auto-detached), `list_seeds()` already returns no `local` entries and the section auto-hides via `build_picker_rows()`, so nothing extra renders on a pure-detached run. Net effect: in detached-from-workspace launches you can now pick a `local:foo` seed, and the WORKSPACE section sits at the top of the picker (per the `local → user → remote → builtin` scope order).

## [0.2.2] - 2026-05-18

### Fixed
- TUI "New Experiment" modal silently used workspace mode regardless of how the app was launched. `novo --detached new …` (and any auto-detached launch) would land the experiment in whatever workspace `cwd`'s walk-up could find a `.novo/` marker for, instead of in cwd as the detached contract promised. The modal now propagates `detached=is_detached()` to `core.experiment.create()` (matching the CLI) and the success notification reports the detached location.

### Added
- "Skip date prefix" checkbox on the New Experiment modal — surfaces the `--no-date` flag in the TUI so detached one-offs can opt out of the `YYYY-MM-DD-` directory prefix without dropping back to the shell.
- Arrow / `j` / `k` navigation between buttons on the DetachedScreen, plus auto-focus on the primary "New experiment here" button on mount, so the screen is keyboard-drivable without an initial Tab.

### Changed
- Seeds tab rows are now compact (`name  [scope]  (default)`), with the description rendered in the side detail pane instead of crammed into the row. The list panel itself is also wider (1fr split, capped at 80 cols) and gets the same `option-list--option-highlighted` styling the experiments list has, so long remote-seed identifiers like `[remote:novo-seed-test]` stop wrapping or truncating. The New Experiment SeedPicker keeps the description in-row since it has no side detail pane.

> [0.2.1] was published to TestPyPI only; this is its first PyPI cut.

## [0.2.1] - 2026-05-18

### Fixed
- TUI crashed on launch (both workspace and `--detached` modes) with `AttributeError: 'NoneType' object has no attribute 'render_strips'`. `StatusBar` defined a `_render()` helper that shadowed Textual's framework hook `Widget._render()` (which is supposed to return the `Visual` to draw), so the widget rendered as `None`. Renamed the helper to `_repaint()` and added a regression test that asserts subclasses don't override `_render`.

### Changed
- `r` on the Seeds tab now syncs **just the highlighted remote** when a remote seed is selected, and falls back to syncing all linked remotes otherwise. Previously `r` always called `sync_remote(None)`, so there was no way to refresh a single registry from the TUI.

### Docs
- README documents `novo new --no-date`, `--python <ver>`, and `novo seed init --path <dir>` — the last is the recommended path for authoring a remote seed registry, since it scaffolds seeds straight into a cloned registry repo without bouncing through `user`/`local` scope.

## [0.2.0] - 2026-05-18

### Added
- **Workspace markers and multi-workspace support.** Any directory with a `.novo/` marker is a valid workspace (like `.git/`). `--workspace <path>` / `NOVO_WORKSPACE` flag/env pin a specific workspace; otherwise novo walks up from cwd looking for a marker, then falls back to `config.workspace.path` or auto-detach. `ensure_initialized()` silently migrates pre-marker workspaces on first touch.
- **Auto-detach when no workspace is found.** If a command runs in a directory with no `.novo/` marker in its ancestry and no `workspace.path` configured, novo now treats it as detached: `novo new` drops a self-contained experiment in cwd (with its own git repo) instead of silently materializing the hidden XDG default workspace; read-only commands (`list / info / search / delete / open`) refuse cleanly with a `novo init` tip. A one-line hint surfaces the mode switch. New `core.workspace.is_detached()` / `is_auto_detached()` accessors.
- **Scope-aware seed resolution.** Seeds live in four scopes: `local` (`<workspace>/.novo/seeds/`), `user`, `remote`, and `builtin`. `--seed` accepts both bare names and explicit scoped forms (`local:foo`, `user:foo`, `remote:team/foo`, `builtin:foo`); bare names error on ambiguity. `.novo.toml` records the scoped identifier so seed origin stays unambiguous.
- **Detached mode.** `novo --detached` skips workspace lookup. `novo --detached new <name>` creates a self-contained experiment at `(--at <path> or cwd)/<name>` with its own git repo (gated on the new `defaults.detached_git` config knob). The other registry-bound commands refuse cleanly. TUI launches a minimal landing screen with direct actions.
- **Remote seed registries.** `novo seed link <url>` clones a git repo of seeds into `~/.local/share/novo/remotes/<name>/`; every subdirectory with a `seed.toml` surfaces as `remote:<name>/<seed>`. `novo seed sync [<name>]` pulls one or all; `novo seed unlink <name>` removes the config entry + clone. Idempotent.
- **TUI overhaul.** New `SeedPicker` widget (scope-grouped OptionList with type-ahead filter and `(default)` indicator); `NewExperimentScreen` uses it. New screens: `DetachedScreen` (minimal landing), `RemoteLinkScreen`, `NewSeedScreen`. Seeds tab gains scope grouping (reuses the picker's row builder) and `N`/`l`/`u`/`r` keybindings. Status bar gains a mode chip and a sync-note slot.
- **New CLI commands and flags:** `novo seed link/sync/unlink`, `novo seed init --scope`, `novo seed list --scope/--json`, `novo new --detached/--at`, `--workspace`/`-W` global flag, `defaults.detached_git` config key.
- **New `docs/seeds.md`** covering scopes, identifier syntax, and the remote sync workflow.
- **Local Docker test rig** (`make docker-shell` / `docker-shell-persistent`) with an editable install of the bind-mounted source.

### Changed
- `novo init` now writes a `.novo/` marker at the target path instead of mutating `config.workspace.path`. To pin a default workspace, run `novo config set workspace.path <path>` explicitly.
- `novo seed list` output is grouped by scope (WORKSPACE / USER / REMOTE: \<name> / BUILTIN) with origin badges; `--json` includes `scope`, `remote`, `identifier`, and `path` per seed.
- `RemoteSeed.ref` defaults to `""` (follow the cloned branch) rather than `"main"`, so registries on `master` or other branches work without explicit pinning.
- `core.config.get_workspace_path()` now returns `None` when `workspace.path` is unset (previously returned the XDG default). Use `core.workspace.current_workspace()` for the active workspace with full resolution.

### Fixed
- `novo new` no longer silently swallows a bad `--seed` value and proceeds to create a bare `uv init` directory. A malformed (`remote:foo` with no `/`), unknown, or ambiguous identifier now aborts before any files are written and prints the parse / not-found / ambiguity error. Internally, `apply_seed(identifier, ...)` was split: callers resolve via `resolve_seed()` first and then call `apply_seed(scoped, target_dir)`.

### Removed
- `novo seed add <url>` — replaced by `novo seed link` for multi-seed repos. To install a single-seed repo, either reshape it into a multi-seed layout or `git clone` into `~/.local/share/novo/seeds/<name>/` manually.
- Silent XDG-default workspace fallback. `~/.local/share/novo/workspace/` is no longer auto-used; opt in by setting `workspace.path` explicitly, or rely on auto-detach.

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
