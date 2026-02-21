---
name: commit-changes
description: When the user asks to commit changes, save work, or make a git commit. Triggers on any commit-related request including "commit", "commit my changes", "commit this", "commit you changes", "save my work", "make a commit", "/commit-changes", or any variation of asking to commit code to git.
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

### 2. Assess documentation impact

Review the diffs against **all** documentation files in the project (`docs/`, `.claude/CLAUDE.md`, `README.md`, and any other docs that exist). For each doc file, check whether the changes affect anything it describes — structure, commands, conventions, models, patterns, etc.

Purely internal changes (bug fixes, refactors within existing modules) typically need no doc updates. But any change that adds, removes, or alters something documented should be flagged.

If documentation updates are needed, make them immediately — do not ask, just update the docs as part of the commit.

### 3. Commit

After the user confirms, stage and commit following the project's commit conventions:

- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
- Scopes: `cli`, `tui`, `core`, `models`, `utils`, `docs`
- Use specific file staging (not `git add -A`)
- Pass the commit message via HEREDOC for proper formatting
