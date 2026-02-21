# Docs Format

Templates for each documentation file. Adapt to the project's language and structure.

## architecture.md

```markdown
# Architecture

## Project Structure

\`\`\`
<directory tree of source code with inline comments>
\`\`\`

## Layer Diagram

\`\`\`
<ASCII diagram showing component relationships>
\`\`\`

<Brief explanation of how components interact.>

## Component Documentation

| Document | Description |
|----------|-------------|
| [<component>.md](<component>.md) | <description> |

## Data Flow: <Primary Operation>

\`\`\`
<Step-by-step ASCII flow diagram>
\`\`\`

## Runtime Layout (if applicable)

\`\`\`
<Directory structure created at runtime>
\`\`\`

## Data Models (if applicable)

<Key schemas, config files, or data structures with example values.>
```

**Notes:**
- Project structure should show every source file with a brief comment
- Layer diagram should match the architecture section in CLAUDE.md
- Pick the most important operation for the data flow example
- Include runtime layout only if the project creates files/dirs at runtime

---

## development.md

```markdown
# Development

## Prerequisites

- <Language> <version>+
- <Package manager>
- <Other tools>

## Setup

\`\`\`bash
<clone + install commands>
\`\`\`

## Commands

### Run

\`\`\`bash
<run commands with comments>
\`\`\`

### Test

\`\`\`bash
<test commands with comments>
\`\`\`

### Build (if applicable)

\`\`\`bash
<build commands>
\`\`\`

## Manual Testing (if applicable)

<Quick smoke test sequence.>
```

**Notes:**
- Only include sections that apply to the project
- Commands should be copy-pasteable
- Derive from actual config files (package.json scripts, Makefile targets, etc.)

---

## coding-guidelines.md

```markdown
# Coding Guidelines

## Code Style

- Formatter/linter: **<tool>**
- <Key style rules specific to this project>

## Layer Separation (if applicable)

| Layer | Directory | Can import | Cannot import |
|-------|-----------|-----------|---------------|
| ... | ... | ... | ... |

Key rules:
- <Rule 1>
- <Rule 2>

## Naming Conventions

### Files
- <Pattern>

### Functions
- <Pattern>

### Types / Classes
- <Pattern>

## Error Handling

- <How errors flow through the codebase>

## Testing Patterns (brief)

- <Key testing conventions>

See [testing.md](testing.md) for details.
```

**Notes:**
- Infer style rules from linter config (.eslintrc, ruff.toml, .prettierrc, etc.)
- Layer separation only if the project has explicit architectural boundaries
- Keep testing patterns brief here — details go in testing.md

---

## testing.md

```markdown
# Testing

## Running Tests

\`\`\`bash
<test commands>
\`\`\`

## Test Structure

\`\`\`
tests/
├── <test directories and files with comments>
\`\`\`

## Key Fixtures / Helpers

<Most important test utilities with code examples.>

## Patterns

<Recurring testing patterns specific to this project.>

## Writing New Tests

1. <Step 1>
2. <Step 2>
3. ...
```

**Notes:**
- Include actual fixture code if it's central to the test setup
- Focus on patterns unique to this project, not generic testing advice

---

## Component docs (<component>.md)

```markdown
# <Component Name>

<One-line description of what this component does and what it's built with.>

## Structure

\`\`\`
<component-dir>/
├── <files with comments>
\`\`\`

## <Section per major module or concept>

| Function / Class | Description |
|------------------|-------------|
| `name` | What it does |

## Patterns

<Notable implementation patterns specific to this component.>
```

**Notes:**
- Name the file after the component (lowercase): `cli.md`, `api.md`, `core.md`
- Include a structure tree showing all files in the component
- Use tables for public API — function/class name + brief description
- Patterns section covers anything a developer should know when working in this component
