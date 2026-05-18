#!/usr/bin/env bash
# Container entrypoint: install novo as a uv tool from the bind-mounted
# repo, then exec whatever command was passed (defaults to `bash`).
set -euo pipefail

if [ ! -f /novo/pyproject.toml ]; then
    cat >&2 <<'EOF'
Error: /novo is not the novo repo.

Expected the novo source tree to be bind-mounted at /novo. From docker/run.sh
this happens automatically; if you're running docker directly, pass:

    -v /path/to/novo:/novo
EOF
    exit 1
fi

# Reinstall every run so live edits to /novo are picked up immediately. The
# editable install records /novo as the source path, so subsequent code
# changes on the host take effect without re-running the container.
uv tool install --reinstall --editable /novo >/dev/null 2>&1

exec "$@"
