# Plan: Restructure docs/ + Create `set-project` skill

## Context

The current `docs/` directory has 4 cross-cutting files (architecture, development, coding-guidelines, testing) but no dedicated documentation for each major component. Adding per-component docs makes it easier to understand and maintain each part of the codebase independently. Additionally, a `set-project` skill will automate this documentation structure setup for any project.

Bonus fix: `.agents/AGENTS.md` is a broken symlink (points to `CLAUDE.md` relative, but CLAUDE.md lives in `.claude/`).

---

## Part 1: Restructure `docs/`

### New files to create

Add 5 component-specific docs, one per architectural layer:

| File | Content |
|------|---------|
| `docs/cli.md` | CLI commands, Typer app structure, argument handling, Rich output patterns |
| `docs/tui.md` | Textual app, screens, widgets, TCSS styles, keybindings |
| `docs/core.md` | Business logic: experiment CRUD, seed management, config, workspace, git |
| `docs/models.md` | Pydantic schemas: NovoConfig, Experiment, Seed — fields, validation, TOML mapping |
| `docs/utils.md` | XDG paths, uv wrapper, shell integration |

### Approach

Extract per-module details from `docs/architecture.md` into the component docs, then enrich with specifics from the source code. Architecture.md becomes a concise high-level overview.

### Changes to existing files

- **`docs/architecture.md`** — Keep layer diagram, data flow, workspace layout, data models. Remove the Module Responsibilities table (those details move into component docs). Add cross-references to new docs.
- **`.claude/CLAUDE.md`** — Update the Documentation table to include the new component docs.
- **`.agents/AGENTS.md`** — Fix the broken symlink: should point to `../.claude/CLAUDE.md`.

### Files left unchanged

- `docs/development.md` — Already scoped correctly (setup, commands, manual testing)
- `docs/coding-guidelines.md` — Already scoped correctly (style, layers, naming, errors)
- `docs/testing.md` — Already scoped correctly (fixtures, patterns, CLI tests)

---

## Part 2: Create `set-project` skill

### What the skill does

Language/framework agnostic — works on any codebase (Python, JS, Go, Rust, etc.).

When triggered, it analyzes the current codebase and generates:
1. `docs/` directory with cross-cutting docs + per-component docs
2. `.claude/CLAUDE.md` with the standard format (commands, docs table, principles, architecture, commits)
3. `.agents/AGENTS.md` symlinked to `.claude/CLAUDE.md`

### Skill structure

```
.agents/skills/set-project/
├── SKILL.md                      # Workflow + format instructions
└── references/
    ├── claude-md-format.md       # Template/format for CLAUDE.md
    └── docs-format.md            # Template/format for docs/ files
```

Plus symlink: `.claude/skills/set-project -> ../../.agents/skills/set-project`

### SKILL.md workflow (high level)

1. **Analyze the codebase** — Read project structure, entry points, source directories, package manager, test setup
2. **Identify components** — Group source modules into logical components (e.g., CLI, API, core, models, utils)
3. **Generate docs/** — Create `architecture.md`, `development.md`, `coding-guidelines.md`, `testing.md`, plus one doc per identified component
4. **Generate `.claude/CLAUDE.md`** — Project name, commands, documentation table, core principles, architecture diagram, commit format
5. **Generate `.agents/AGENTS.md`** — Symlink to `.claude/CLAUDE.md`
6. **Report to user** — Show what was created and suggest review

### Reference files

- `references/claude-md-format.md` — The exact template structure for CLAUDE.md based on this repo's format
- `references/docs-format.md` — Templates for each doc type (architecture, development, coding-guidelines, testing, component docs)

---

## Verification

1. Check all new doc files render correctly with consistent formatting
2. Verify `.agents/AGENTS.md` symlink is no longer broken
3. Verify `.claude/CLAUDE.md` Documentation table includes all docs
4. Test the `set-project` skill by reading SKILL.md and confirming the workflow is clear and references are reachable
5. Run `ls -la .claude/skills/set-project` to verify symlink exists
