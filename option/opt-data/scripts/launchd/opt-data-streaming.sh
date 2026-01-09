#!/usr/bin/env bash
set -euo pipefail

# Runs the streaming subscription in a timer-friendly mode:
# - compute duration until market close (early-close aware)
# - exit after duration

if [[ -n "${OPT_DATA_ROOT:-}" ]]; then
  REPO_ROOT="$OPT_DATA_ROOT"
  if [[ ! -d "$REPO_ROOT" ]]; then
    echo "[opt-data-streaming] OPT_DATA_ROOT not found: $REPO_ROOT" >&2
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

LOCK_DIR="$REPO_ROOT/state/run_locks/opt-data-streaming.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[opt-data-streaming] lock exists, another run may still be active: $LOCK_DIR" >&2
  exit 1
fi

cleanup() {
  rmdir "$LOCK_DIR" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM HUP

PYTHON="$REPO_ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "[opt-data-streaming] missing venv python: $PYTHON" >&2
  echo "[opt-data-streaming] create it with: python3.11 -m venv .venv && .venv/bin/pip install -e '.[dev]'" >&2
  exit 1
fi

CONFIG_PATH="${OPT_DATA_CONFIG:-$REPO_ROOT/config/opt-data.local.toml}"
if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "[opt-data-streaming] config not found: $CONFIG_PATH" >&2
  exit 1
fi

export TZ="${TZ:-America/New_York}"

START_CLOCK="${OPT_DATA_STREAMING_START:-09:35}"
DURATION="$("$PYTHON" "$REPO_ROOT/scripts/ops/streaming_duration.py" --start-clock "$START_CLOCK")"

if [[ -z "$DURATION" || "$DURATION" -le 0 ]]; then
  echo "[opt-data-streaming] no trading session or already past close; exiting" >&2
  exit 0
fi

"$PYTHON" -m opt_data.cli streaming --config "$CONFIG_PATH" --duration "$DURATION"
