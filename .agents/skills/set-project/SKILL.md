---
name: set-project
description: Analyze a codebase and generate project documentation structure. Creates docs/ with architecture, development, coding-guidelines, testing, and per-component docs, plus .claude/CLAUDE.md and .agents/AGENTS.md. Use when the user asks to "set up project docs", "initialize project documentation", "create CLAUDE.md", "set up project for Claude", or says "/set-project". Works with any language or framework.
---

# Set Project

Analyze the current codebase and generate a complete documentation structure.

## What Gets Created

```
docs/
├── architecture.md          # Structure, layers, data flow
├── development.md           # Setup, prerequisites, dev workflow
├── coding-guidelines.md     # Style, patterns, conventions
├── testing.md               # Test structure, fixtures, patterns
├── <component-1>.md         # Per-component deep-dive
├── <component-2>.md         # Per-component deep-dive
└── ...
.claude/
└── CLAUDE.md                # Agent instructions (commands, docs table, architecture, commits)
.agents/
└── AGENTS.md                # Symlink to ../.claude/CLAUDE.md
```

## Workflow

### 1. Analyze the codebase

Explore the project to understand:

- **Language & tooling** — What language, package manager, test framework, and build tools are used? Check files like `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `Makefile`, etc.
- **Entry points** — How is the project run? What are the main commands?
- **Source structure** — What directories and modules exist under `src/`, `lib/`, `app/`, or equivalent?
- **Test structure** — Where are tests? What framework and fixtures are used?
- **Existing docs** — Is there already a `docs/`, `README.md`, `CLAUDE.md`, or `AGENTS.md`?

If docs already exist, ask the user whether to overwrite, merge, or skip.

### 2. Identify components

Group the source code into logical components. Look for natural boundaries:

- **Interface layers** — CLI, API, TUI, web frontend, etc.
- **Business logic** — Core domain logic, services, controllers
- **Data layer** — Models, schemas, database, ORM
- **Shared utilities** — Helpers, config, logging, common abstractions
- **Infrastructure** — Build, deploy, CI/CD, Docker

Aim for 3–7 components. Each becomes a dedicated doc in `docs/`.

Present the proposed component breakdown to the user before generating docs.

### 3. Generate docs/

Create each doc file following the formats in [references/docs-format.md](references/docs-format.md).

**Cross-cutting docs** (always created):
- `architecture.md` — High-level overview, layer diagram, component table, data flow
- `development.md` — Prerequisites, setup, run/test/build commands
- `coding-guidelines.md` — Style rules, layer boundaries, naming, error handling
- `testing.md` — Test structure, key fixtures, patterns, how to write new tests

**Component docs** (one per identified component):
- Named after the component: `cli.md`, `api.md`, `core.md`, `models.md`, etc.
- Contains: module structure, public API, patterns, internal details

### 4. Generate .claude/CLAUDE.md

Create the agent instructions file following [references/claude-md-format.md](references/claude-md-format.md).

```bash
mkdir -p .claude
```

The file should include: project name and description, common commands, documentation table, core principles, architecture diagram, and commit format.

### 5. Generate .agents/AGENTS.md

Create a symlink so both Claude Code and other agent tools discover the same instructions:

```bash
mkdir -p .agents
ln -s ../.claude/CLAUDE.md .agents/AGENTS.md
```

### 6. Report to user

Summarize what was created:
- List all generated files
- Highlight any decisions made (component breakdown, skipped sections)
- Suggest reviewing and customizing the generated docs
