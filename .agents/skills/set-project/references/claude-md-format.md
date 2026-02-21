# CLAUDE.md Format

Template for generating `.claude/CLAUDE.md`. Adapt each section to the project's language, tooling, and structure.

## Template

```markdown
# <project-name>

<One-line description of the project.>

## Commands

\`\`\`bash
<package-manager> install          # Install dependencies
<run-command>                       # Run the project
<run-command> --help                # Show help
<test-command>                      # Run all tests
<test-command> <subset>             # Run specific tests
<lint-command>                      # Lint / format
\`\`\`

Include only commands that actually work in this project. Add comments explaining each.

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture.md](docs/architecture.md) | Project structure, layers, data flow |
| [docs/development.md](docs/development.md) | Setup, prerequisites, dev workflow |
| [docs/coding-guidelines.md](docs/coding-guidelines.md) | Code style, patterns, conventions |
| [docs/testing.md](docs/testing.md) | Test structure, fixtures, patterns |
| [docs/<component>.md](docs/<component>.md) | <Component description> |

One row per doc file. Keep descriptions short.

## Core Principles

1. **<Principle 1>.** <Brief explanation.>
2. **<Principle 2>.** <Brief explanation.>
3. **<Principle 3>.** <Brief explanation.>

3–5 principles that capture the project's design philosophy. These should be specific to the project, not generic software advice.

## Architecture

\`\`\`
<ASCII diagram showing how the main components relate>
\`\`\`

- **<Component 1>** — <One-line role description.>
- **<Component 2>** — <One-line role description.>
- **<Component N>** — <One-line role description.>

Entry point: `<entry-point>` (defined in `<config-file>`).

## Commits

Format: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
Scopes: <comma-separated list of component names matching the project>
```

## Guidelines

- **Commands section** — Only include commands the developer actually runs. Derive from `package.json` scripts, `pyproject.toml`, `Makefile`, `Cargo.toml`, etc.
- **Core Principles** — Extract from README, existing docs, or infer from code patterns. Ask the user if unclear.
- **Architecture diagram** — Use ASCII art. Show relationships between components with arrows. Keep it under 10 lines.
- **Scopes** — Match the component names identified in step 2 of the workflow.
