---
name: commit-changes
description: Review staged and unstaged git changes before committing, assess whether documentation needs updating, and create a well-formatted commit. Use when the user asks to commit, save changes, or says "/commit-changes". Triggers on requests like "commit my changes", "commit this", "save my work", or any commit-related request.
---

# Commit Changes

Review all changes, assess documentation impact, then commit.

## Workflow

### 1. Review changes

Run these git commands to understand the full scope of changes:

```bash
git status
git diff
git diff --cached
git log --oneline -5
```

Identify which files changed and what the changes do. Categorize by layer: `cli/`, `tui/`, `core/`, `models/`, `utils/`, `tests/`, `seeds/`, or other.

### 2. Assess documentation impact

For each changed file, check whether the change affects anything described in the project documentation. The documentation files to consider are:

| File | Update when... |
|------|----------------|
| `docs/architecture.md` | New modules, changed module responsibilities, new data models, changed data flow, changed project structure |
| `docs/development.md` | New commands, changed setup steps, new prerequisites, changed dev workflow |
| `docs/coding-guidelines.md` | New conventions adopted, changed patterns, new layer rules |
| `docs/testing.md` | New test patterns, changed fixtures, new test directories |
| `.claude/CLAUDE.md` | New CLI commands, changed architecture diagram, changed core principles |
| `README.md` | User-facing feature changes (if the file exists) |

**Assessment rules:**

- Adding a new CLI command → update `docs/development.md` (commands list) and `.claude/CLAUDE.md` (commands table)
- Adding a new module or file → update `docs/architecture.md` (project structure)
- Changing a model schema → update `docs/architecture.md` (data models section)
- Adding a new test fixture or pattern → update `docs/testing.md`
- Changing layer boundaries or import rules → update `docs/coding-guidelines.md`
- Purely internal changes (bug fixes, refactors within existing modules) → typically no doc updates needed

### 3. Report findings

Before committing, report to the user:

1. **Summary of changes** — what was changed and why
2. **Documentation impact** — list which docs need updating and why, or confirm none need changes
3. **Proposed commit message** — following the project's conventional commit format: `<type>(<scope>): <description>`

If documentation updates are needed, ask the user whether to:
- Update the docs now before committing
- Commit code changes first, then update docs in a separate commit
- Skip documentation updates

### 4. Commit

After the user confirms, stage and commit following the project's commit conventions:

- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
- Scopes: `cli`, `tui`, `core`, `models`, `utils`, `docs`
- Use specific file staging (not `git add -A`)
- Pass the commit message via HEREDOC for proper formatting
