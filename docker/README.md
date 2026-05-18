# Docker test rig

A throwaway Linux container for testing the local `novo` build without
touching your host install, config, or workspace.

The setup:

- **`Dockerfile`** — `python:3.13-slim` + `git` + `uv` + sensible git defaults.
- **`entrypoint.sh`** — on every container start, runs
  `uv tool install --reinstall --editable /novo` against the bind-mounted
  repo. Live edits flow through immediately, no rebuild needed.
- **`run.sh`** — host-side wrapper that builds the image lazily and
  starts a container with the repo mounted.

## Quick start

```bash
# Interactive shell (clean state every run):
./docker/run.sh

# Inside the container:
novo --version
novo --help
novo --detached new test --no-date
novo seed list
```

Or via `make`:

```bash
make docker-shell             # ephemeral interactive shell
make docker-shell-persistent  # named volumes for /root/.config + /root/.local/share
make docker-clean             # remove image + persistent volumes
```

## Forwarding arguments

`run.sh` forwards everything after its own flags to the container's
entrypoint, so any of these work:

```bash
./docker/run.sh novo --help
./docker/run.sh novo seed list --json
./docker/run.sh novo --detached new foo --no-date
./docker/run.sh                       # interactive bash (default)
```

## Persistence

By default each run is fully ephemeral — config, default workspace,
linked remotes, and the cloned repos all disappear on exit. That's
deliberate: it's how you exercise the silent-migration code path and
test "fresh install" behavior.

Pass `-p` / `--persistent` to keep `~/.config` and `~/.local/share`
(novo and uv state) across runs via named volumes:

```bash
./docker/run.sh --persistent novo seed link <url>   # link persists
./docker/run.sh --persistent novo seed sync         # uses the linked remote
```

Volumes are named `novo-test-config` and `novo-test-data`. Wipe with:

```bash
make docker-clean
# or manually:
docker volume rm novo-test-config novo-test-data
```

## Rebuilding the image

The image bakes in git + uv but not novo itself, so you usually never
need to rebuild — `entrypoint.sh` reinstalls novo from /novo every run.
You do need to rebuild after editing the Dockerfile or entrypoint:

```bash
./docker/run.sh --rebuild
```

## How TUI testing works

Textual needs an interactive TTY plus 256-color support. `run.sh` passes
`-it` and forwards `TERM` from the host. So:

```bash
./docker/run.sh novo            # workspace mode TUI
./docker/run.sh novo --detached # detached-mode landing screen
```

…both render correctly inside the container.

## What gets mounted

| Host path | Container path | Purpose |
|-----------|----------------|---------|
| `<repo root>` | `/novo` | Source for editable install |
| `novo-test-config` (named volume, `-p` only) | `/root/.config` | XDG config dir |
| `novo-test-data` (named volume, `-p` only) | `/root/.local/share` | XDG data dir + uv tool state |

`/workspace` is the container's working directory — a writable scratch
area you can use for ad-hoc workspaces or detached experiments.
