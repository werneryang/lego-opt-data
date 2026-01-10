#!/usr/bin/env bash
set -euo pipefail

# Runs the opt-data daily scheduler in "timer-friendly" mode:
# - schedule today's jobs
# - exit when all jobs are done (--exit-when-idle)
#
# Intended to be invoked by launchd at a fixed wall-clock time each day.

if [[ -n "${OPT_DATA_ROOT:-}" ]]; then
  REPO_ROOT="$OPT_DATA_ROOT"
  if [[ ! -d "$REPO_ROOT" ]]; then
    echo "[opt-data-daily] OPT_DATA_ROOT not found: $REPO_ROOT" >&2
    exit 1
  fi
else
  REPO_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.." >/dev/null 2>&1
    pwd
  )"
fi

cd "$REPO_ROOT"

mkdir -p "$REPO_ROOT/state/run_logs" "$REPO_ROOT/state/run_locks"

LOCK_DIR="$REPO_ROOT/state/run_locks/opt-data-daily.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[opt-data-daily] lock exists, another run may still be active: $LOCK_DIR" >&2
  exit 1
fi

cleanup() {
  rmdir "$LOCK_DIR" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM HUP

PYTHON="$REPO_ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "[opt-data-daily] missing venv python: $PYTHON" >&2
  echo "[opt-data-daily] create it with: python3.11 -m venv .venv && .venv/bin/pip install -r ../../requirements-dev.lock && .venv/bin/pip install -e . --no-deps" >&2
  exit 1
fi

CONFIG_PATH="${OPT_DATA_CONFIG:-$REPO_ROOT/config/opt-data.snapshot.local.toml}"
if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "[opt-data-daily] config not found: $CONFIG_PATH" >&2
  exit 1
fi

export TZ="${TZ:-America/New_York}"

"$PYTHON" -m opt_data.cli schedule --live --exit-when-idle --config "$CONFIG_PATH"
