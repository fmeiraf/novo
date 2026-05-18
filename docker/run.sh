#!/usr/bin/env bash
# Host-side wrapper for the novo Docker test rig.
#
# Examples:
#   ./docker/run.sh                         # interactive bash, clean state
#   ./docker/run.sh novo --help
#   ./docker/run.sh novo --detached new test --no-date
#   ./docker/run.sh -p novo seed link <url>     # persistent across runs
#   ./docker/run.sh --rebuild                   # force image rebuild
set -euo pipefail

IMAGE=novo-test
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PERSISTENT=0
REBUILD=0

while [ $# -gt 0 ]; do
    case "$1" in
        -p|--persistent)
            PERSISTENT=1
            shift
            ;;
        --rebuild)
            REBUILD=1
            shift
            ;;
        -h|--help)
            sed -n '2,11p' "${BASH_SOURCE[0]}"
            exit 0
            ;;
        --)
            shift
            break
            ;;
        *)
            break
            ;;
    esac
done

if [ "$REBUILD" = "1" ]; then
    docker rmi -f "$IMAGE" >/dev/null 2>&1 || true
fi

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "[docker/run.sh] building $IMAGE…"
    docker build -t "$IMAGE" "$REPO_ROOT/docker"
fi

VOLUME_ARGS=(-v "$REPO_ROOT:/novo")
if [ "$PERSISTENT" = "1" ]; then
    VOLUME_ARGS+=(
        -v novo-test-config:/root/.config
        -v novo-test-data:/root/.local/share
    )
fi

exec docker run --rm -it \
    "${VOLUME_ARGS[@]}" \
    -e TERM \
    "$IMAGE" "${@:-bash}"
