# TUI

Interactive terminal interface built with [Textual](https://textual.textualize.io/). Launched when `novo` is run without a subcommand.

## Structure

```
tui/
├── app.py                  # NovoApp (root) — picks MainScreen vs DetachedScreen
├── styles/
│   └── app.tcss            # Textual CSS (colors, layout)
├── screens/
│   ├── main.py             # Workspace mode — tabbed Experiments + Seeds
│   ├── detached.py         # Detached-mode minimal landing screen
│   ├── new_experiment.py   # Create-experiment modal (uses SeedPicker)
│   ├── new_seed.py         # Scaffold-seed modal (name/desc/scope)
│   ├── remote_link.py      # Link-remote modal (url/name/ref)
│   └── confirm.py          # Reusable yes/no dialog
└── widgets/
    ├── experiment_list.py  # ExperimentList — filterable list (vim keys)
    ├── experiment_card.py  # ExperimentCard — detail panel
    ├── search_bar.py       # SearchBar — search input
    ├── status_bar.py       # StatusBar — mode chip + bindings + sync note
    ├── seed_picker.py      # SeedPicker — scope-grouped picker + pure helpers
    ├── file_tree.py        # Filtered directory tree
    └── file_preview.py     # File contents preview
```

## App

`NovoApp` subclasses `textual.App`. Loads CSS from `styles/app.tcss`, binds `q` to quit, and on mount inspects `core.workspace.is_detached_forced()` to choose its initial screen:

- `True` → push `DetachedScreen`
- `False` → push `MainScreen`

## Screens

### MainScreen (workspace mode)

Two-tab layout: **Experiments** (list + detail card, search bar) and **Seeds** (scope-grouped picker + detail/template/preview panels).

**Keybindings:**

| Key | Action |
|-----|--------|
| `n` | New experiment (modal) |
| `d` | Delete selected experiment (Experiments tab only) |
| `e` | Switch to Experiments tab |
| `s` | Switch to Seeds tab |
| `t` | Focus the seed file tree (Seeds tab only) |
| `/` | Focus search bar |
| `?` | Help notification |
| `q` | Quit |
| `N` | Scaffold new seed (Seeds tab only) |
| `l` | Link remote registry (Seeds tab only) |
| `u` | Unlink the registry of the highlighted remote seed (Seeds tab only) |
| `r` | Sync the highlighted remote (or all linked remotes if no remote seed is highlighted) (Seeds tab only) |

The seeds tab uses `build_picker_rows()` (the same helper as the SeedPicker widget) so the WORKSPACE / USER / REMOTE: \<n> / BUILTIN section headers and `[scope]` badges match the picker.

### DetachedScreen

Minimal landing screen for `novo --detached` launches (and auto-detached runs, when no workspace can be resolved) — no workspace registry to browse. Header reads `DETACHED — <cwd>` with four direct actions: New experiment here, Browse seeds (CLI hint), Link remote, Initialize workspace here. On mount the screen focuses the primary "New experiment here" button so arrows / `j` / `k` move between buttons and Enter activates the focused one without a prior Tab.

| Key | Action |
|-----|--------|
| `n` | New experiment here |
| `s` | Browse seeds (shows a CLI hint) |
| `l` | Link remote |
| `i` | Initialize workspace here (flips to workspace mode + switches to MainScreen) |
| `↑` / `k` | Focus previous button |
| `↓` / `j` | Focus next button |
| `enter` | Activate focused button |
| `q` | Quit |

### NewExperimentScreen

Modal fields: name, description, tags (comma-separated), seed (SeedPicker), Python version (Select), and a "Skip date prefix" checkbox (mirrors the `--no-date` CLI flag — directory name becomes `<name>` instead of `<YYYY-MM-DD>-<name>`).

The SeedPicker is constructed with `hide_workspace=is_detached_forced()` so detached launches omit the WORKSPACE section.

On submit, calls `core.experiment.create(seed_name=picker.selected_identifier, no_date=…, detached=is_detached(), …)` — `.novo.toml` records the scoped form. `detached` is read live from `core.workspace.is_detached()` so the modal lands the experiment in cwd when the app was launched with `--detached` (or auto-detached), instead of falling through to workspace mode.

### NewSeedScreen

Modal for `novo seed init` from within the TUI. Fields: name, description, scope (local/user). Default scope mirrors the CLI: local if cwd is inside a workspace, else user.

### RemoteLinkScreen

Modal for `novo seed link`. Fields: URL (required), local name (optional, defaults to repo name), ref (optional). On submit calls `link_remote()` and dismisses with `True`; the main screen then runs a sync and surfaces the result in the status bar.

### ConfirmScreen

Reusable yes/no dialog. Accepts a message string, returns `True`/`False`. Binds `y`/`n`/`escape`.

## Widgets

| Widget | Purpose |
|--------|---------|
| `ExperimentList` | Extends `OptionList`. Vim-style navigation (`j`/`k`). Posts `Selected` and `Activated` messages. Supports `filter(query)` for real-time search across name, description, and tags. |
| `ExperimentCard` | Displays selected experiment details: name, created date, seed, Python version, tags, description, directory, `.claude`/`.agents` presence. |
| `SearchBar` | Horizontal input with `> ` prompt. Posts `Changed(query)` on each keystroke. |
| `StatusBar` | Three slots: mode chip (`WORKSPACE: foo` / `DETACHED`), key bindings (context-aware: `main`, `seeds`, `search`, `new`, `confirm`), and a transient sync note for `seed sync` results. Rendering is exposed via `compose_text()` for testability. |
| `SeedPicker` | OptionList-based scope-aware picker. Sections rendered as disabled header rows; entries show `name  description  [scope-badge]` plus `(default)` on the resolved default. Type-ahead `Input` filters by name+description, dropping empty sections. `hide_workspace=True` removes the local section (used in detached mode). `compact=True` (used by the Seeds tab, not the modal) drops the in-row description since the side detail pane shows it. |

### `build_picker_rows()` (in `seed_picker.py`)

Pure helper that returns `list[PickerRow(label, id, disabled)]` for an OptionList. Used by both `SeedPicker` and `MainScreen._refresh_seeds()` so the two surfaces stay consistent.

## Styling

All styles are in `styles/app.tcss`. Uses Textual CSS variables (`$primary`, `$accent`, `$surface`, `$text`). Layout is a vertical stack: header → tabs → status bar.
