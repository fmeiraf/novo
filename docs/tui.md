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

Modal fields: name, description, tags (comma-separated), seed (SeedPicker), Python version (Select), and a "Skip date prefix" checkbox (mirrors the `--no-date` CLI flag — directory name becomes `<name>` instead of `<YYYY-MM-DD>-<name>`). The modal is 100 columns wide (capped at 95% of the terminal) and its form fields live inside a `VerticalScroll` sized `1fr`, with the Create / Cancel buttons docked at a fixed `height: 3` at the bottom — so on short terminals (≲ 24 rows) the form scrolls internally and the action buttons stay reachable.

The SeedPicker is constructed with `hide_workspace=False` (the default) regardless of mode. Local seeds appear at the top whenever `current_workspace()` resolves to a real workspace — including `--detached` launches from inside a workspace directory — so users can pick a `local:foo` seed for a detached experiment. When the cwd genuinely has no workspace context (auto-detached), `list_seeds()` returns no `local` entries and `build_picker_rows()` drops the empty WORKSPACE section automatically.

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
| `SeedPicker` | OptionList-based scope-aware picker. Section headers (`█ WORKSPACE`, `█ USER`, `█ REMOTE: <name>`, `█ BUILTIN`) are rendered as disabled rows with a coloured block bar in the scope's accent colour; an empty disabled row separates adjacent sections. Entries are indented under the bar and show `name  description  [scope-badge]` plus `(default)` on the resolved default; the `[scope]` badge picks up the scope's accent colour so filtered views (where the header may be off-screen) still read at a glance. Type-ahead `Input` filters by name+description, dropping empty sections. The picker opens scrolled to the top with no auto-highlight — the `(default)` row badge marks which seed will be used if the form is submitted without picking one, and consumers fall back to that via `seed_name=None`. `hide_workspace=True` removes the local section (kept as a knob; the modal no longer passes it). `compact=True` (used by the Seeds tab, not the modal) drops the in-row description since the side detail pane shows it. |

### `build_picker_rows()` (in `seed_picker.py`)

Pure helper that returns `list[PickerRow(label, id, disabled)]` for an OptionList. Used by both `SeedPicker` and `MainScreen._refresh_seeds()` so the two surfaces stay consistent.

## Styling

All styles are in `styles/app.tcss`. Uses Textual CSS variables (`$primary`, `$accent`, `$surface`, `$text`). Layout is a vertical stack: header → tabs → status bar.
