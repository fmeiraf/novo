# TUI

Interactive terminal interface built with [Textual](https://textual.textualize.io/). Launched when `novo` is run without a subcommand.

## Structure

```
tui/
├── app.py                  # NovoApp (root application)
├── styles/
│   └── app.tcss            # Textual CSS (colors, layout)
├── screens/
│   ├── main.py             # MainScreen — two-panel layout
│   ├── new_experiment.py   # NewExperimentScreen — creation modal
│   ├── confirm.py          # ConfirmScreen — yes/no dialog
│   └── seed_manager.py     # SeedManagerScreen — seed browser
└── widgets/
    ├── experiment_list.py  # ExperimentList — filterable list (vim keys)
    ├── experiment_card.py  # ExperimentCard — detail panel
    ├── search_bar.py       # SearchBar — search input
    └── status_bar.py       # StatusBar — context-sensitive keybindings
```

## App

`NovoApp` subclasses `textual.App`. Loads CSS from `styles/app.tcss`, binds `q` to quit, and pushes `MainScreen` on startup.

## Screens

### MainScreen

Primary two-panel layout: experiment list on the left, detail card on the right.

**Keybindings:** `n` new, `d` delete, `s` seeds, `/` search, `?` help, `q` quit.

**Lifecycle:**
1. `on_mount()` — Loads experiments via `core.experiment.list_all()`
2. Selection changes → updates `ExperimentCard`
3. Enter on an experiment → opens its directory path
4. Search input → filters the list in real-time

**Modals** are pushed onto the screen stack and return results via callbacks:
- `NewExperimentScreen` → refreshes list on success
- `ConfirmScreen` → deletes experiment if confirmed
- `SeedManagerScreen` → browse/manage seeds

### NewExperimentScreen

Modal with fields: name, description, tags (comma-separated), seed (dropdown from `core.seed.list_seeds()`), Python version (dropdown from `utils.uv.list_python_versions()`).

Calls `core.experiment.create()` on submit. Returns the created `Experiment` or `False` on cancel.

### ConfirmScreen

Reusable yes/no dialog. Accepts a message string, returns `True`/`False`. Binds `y`/`n`/`escape`.

### SeedManagerScreen

Two-panel seed browser showing all seeds with details (name, description, type, packages, path). Marks built-in seeds with a prefix.

## Widgets

| Widget | Purpose |
|--------|---------|
| `ExperimentList` | Extends `OptionList`. Vim-style navigation (`j`/`k`). Posts `Selected` and `Activated` messages. Supports `filter(query)` for real-time search across name, description, and tags. |
| `ExperimentCard` | Displays selected experiment details: name, created date, seed, Python version, tags, description, directory, `.claude`/`.agents` presence. |
| `SearchBar` | Horizontal input with `> ` prompt. Posts `Changed(query)` on each keystroke. |
| `StatusBar` | Shows keybinding hints. Switches context (`main`, `search`, `new`, `confirm`) to display relevant bindings. |

## Styling

All styles are in `styles/app.tcss`. Uses Textual CSS variables (`$primary`, `$accent`, `$surface`, `$text`). Layout is a vertical stack: header → search bar → horizontal split (list | card) → status bar.
