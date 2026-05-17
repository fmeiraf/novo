# Seeds

A **seed** is a reusable project template — a directory containing a `seed.toml` manifest and a `template/` directory whose contents are copied into every new experiment. Seeds let novo scaffold experiments without baking in opinions about your stack.

## Scopes

novo discovers seeds from four scopes, listed in resolution order:

| Scope | Location | Source |
|-------|----------|--------|
| `local` | `<workspace>/.novo/seeds/` | Per-workspace seeds, not shared across workspaces |
| `user` | `~/.local/share/novo/seeds/` | Globally available on your machine |
| `remote` | `~/.local/share/novo/remotes/<remote>/<seed>/` | Cloned from a linked git registry |
| `builtin` | `<package>/seeds/` | Bundled with novo (currently just `default`) |

Listings (`novo seed list`, the TUI Seeds tab, the SeedPicker) always show every scope. The order above only matters for **implicit** seed lookups — i.e. when you write `--seed foo` (or `defaults.seed = "foo"` in config) with no scope prefix.

## Identifier syntax

Anywhere novo accepts a seed identifier (`--seed`, `defaults.seed`, the `seed` field in `.novo.toml`), all of these are valid:

| Form | Meaning |
|------|---------|
| `foo` | Implicit — walks scopes; errors if ambiguous |
| `local:foo` | Explicit local (workspace) seed |
| `user:foo` | Explicit user-installed seed |
| `builtin:foo` | Explicit bundled seed |
| `remote:<remote>/<seed>` | Explicit remote seed (the `<remote>` part is the local name you gave it with `seed link`) |

Malformed forms (`bogus:foo`, `remote:foo` without `/`, `user:` without a name) error at parse time.

## Resolution and ambiguity

When you use a bare name (`--seed foo`):

1. novo walks the scope order looking for a seed named `foo`.
2. If exactly one scope has it → that one wins.
3. If multiple scopes have it → novo errors:

   ```
   ambiguous seed 'shared' found in: local:shared, user:shared.
   Use an explicit scope like --seed local:shared.
   ```

Whichever identifier wins (explicit or resolved-from-implicit) gets recorded as the **scoped** identifier in `.novo.toml`. That way an experiment's seed origin stays unambiguous even if the seed later moves between scopes or a same-name seed appears in another scope.

## Authoring a seed

```bash
novo seed init my-stack --scope user --desc "My standard project setup"
```

This scaffolds `~/.local/share/novo/seeds/my-stack/` with a `seed.toml` (commented examples included) and a `template/` directory. Drop your starter files into `template/` and edit `seed.toml`:

```toml
[seed]
name = "my-stack"
description = "Numpy + pandas + jupyter starter"

[seed.dependencies]
packages = ["numpy", "pandas", "jupyter"]

[seed.post_create]
commands = ["mkdir notebooks"]

[seed.files]
exclude = ["__pycache__", "*.pyc", ".git"]
```

When applied, novo:

1. Copies `template/` contents into the experiment (respecting `files.exclude`, skipping `pyproject.toml` which `uv init` already wrote).
2. Installs `dependencies.packages` via `uv add`.
3. Runs each `post_create.commands` entry as a shell command in the experiment dir.

### Scope flag

By default `seed init` picks `local` when cwd is inside a workspace, otherwise `user`. Override with:

```bash
novo seed init my-stack --scope user      # always global
novo seed init my-stack --scope local     # always per-workspace
novo seed init my-stack --path /custom    # explicit dir (advanced)
```

`remote` is not a valid scope for `seed init` — remote seeds live in a registry you maintain elsewhere and link with `seed link`.

## Remote registries

A **remote registry** is a git repo whose top-level subdirectories each contain a seed (one `seed.toml` per subdir, like `team-seeds/etl/seed.toml`, `team-seeds/ml-experiment/seed.toml`). Linking the registry makes every seed in it available as `remote:<your-local-name>/<seed-name>`.

### Link

```bash
novo seed link git@github.com:team/novo-seeds.git --name team --ref main
```

- Clones into `~/.local/share/novo/remotes/team/`.
- Persists `[[seeds.remotes]]` in `~/.config/novo/config.toml`.
- Writes a `.novo-remote.toml` sync timestamp inside the clone.
- Idempotent — re-running with the same `--name` updates the URL/ref and reuses the existing clone.

`--name` defaults to the trailing path component of the URL (so `git@github.com:team/novo-seeds.git` becomes `novo-seeds`). `--ref` is empty by default ("follow whatever branch the clone is on"); set explicitly to pin a branch, tag, or SHA.

### Sync

```bash
novo seed sync              # all linked remotes
novo seed sync team         # just one
```

For each remote: pulls (`git pull --ff-only` for empty `ref`, or `fetch + reset --hard origin/<ref>` when pinned), updates `last_synced_at`, and reports the result. The TUI surfaces the same summary in the Seeds-tab status bar.

### Unlink

```bash
novo seed unlink team
```

Removes the config entry and deletes the clone.

### Inspecting

```bash
novo seed list                  # grouped output, REMOTE section shows the URL
novo seed list --scope remote   # filter
novo seed list --json           # machine-readable; includes scope + identifier + path
```

## Migration notes

- **Pre-marker workspaces:** the first time novo touches the XDG default workspace after upgrading, it silently writes the `.novo/` marker (plus `seeds/` and an empty per-workspace `config.toml`). Existing experiments and git history are untouched.
- **Unscoped `seed` values in old `.novo.toml`** (e.g. `seed = "default"`): still display fine. They're resolved lazily as bare identifiers — no automatic rewrite.
- **`seed add` removed:** the legacy single-seed install command is gone in favor of `seed link`. If you have a single-seed repo, either reshape it into a multi-seed layout (top-level dir per seed) and link it, or `git clone` it into `~/.local/share/novo/seeds/<name>/` manually (that's just the user scope).
