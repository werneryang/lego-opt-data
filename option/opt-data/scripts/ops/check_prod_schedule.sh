#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Check opt-data production schedule status (macOS launchd timer mode).

Usage:
  scripts/ops/check_prod_schedule.sh [--date today|YYYY-MM-DD] [--config PATH] [--label LABEL]

Defaults:
  --date   today
  --config $OPT_DATA_CONFIG or ./config/opt-data.snapshot.local.toml
  --label  com.legosmos.opt-data.timer
  uses $OPT_DATA_ROOT as repo root when set

Exit codes:
  0 OK (no obvious red flags)
  2 WARN/FAIL (non-zero last exit code OR lock exists OR stderr shows errors)
EOF
}

DATE_ARG="today"
LABEL="com.legosmos.opt-data.timer"
CONFIG_PATH="${OPT_DATA_CONFIG:-./config/opt-data.snapshot.local.toml}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --date) DATE_ARG="${2:-}"; shift 2;;
    --config) CONFIG_PATH="${2:-}"; shift 2;;
    --label) LABEL="${2:-}"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2;;
  esac
done

if [[ -n "${OPT_DATA_ROOT:-}" ]]; then
  REPO_ROOT="$OPT_DATA_ROOT"
  if [[ ! -d "$REPO_ROOT" ]]; then
    echo "[WARN] OPT_DATA_ROOT not found: $REPO_ROOT"
    exit 2
  fi
else
  REPO_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.." >/dev/null 2>&1
    pwd
  )"
fi
cd "$REPO_ROOT"

export TZ="${TZ:-America/New_York}"

STAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_LOG_DIR="$REPO_ROOT/state/run_logs"
OUT_DIR="$RUN_LOG_DIR/ops_checks"
mkdir -p "$OUT_DIR"
REPORT="$OUT_DIR/prod_schedule_check_${STAMP_UTC}.log"

warn=0

{
  echo "== identity =="
  echo "ts_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) ts_et=$(date +%Y-%m-%dT%H:%M:%S%z) tz=$TZ"
  echo "whoami=$(whoami) host=$(hostname) pwd=$PWD"
  echo

  echo "== config =="
  echo "date_arg=$DATE_ARG"
  echo "label=$LABEL"
  echo "config_path=$CONFIG_PATH"
  [[ -f "$CONFIG_PATH" ]] || echo "[WARN] config not found: $CONFIG_PATH"
  echo

  echo "== launchd status =="
  LAUNCHD_OUT="$(launchctl print "gui/$(id -u)/$LABEL" 2>&1 || true)"
  echo "$LAUNCHD_OUT"
  if echo "$LAUNCHD_OUT" | grep -E "Could not find service|service.*not found" >/dev/null 2>&1; then
    PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
    if [[ -f "$PLIST_PATH" ]]; then
      echo "[WARN] launchd service is not loaded (plist exists but not bootstrapped): $PLIST_PATH"
      echo "[HINT] run:"
      echo "  launchctl bootstrap gui/$(id -u) \"$PLIST_PATH\""
      echo "  launchctl kickstart -k gui/$(id -u)/$LABEL"
    else
      echo "[WARN] launchd service is not loaded and plist is missing: $PLIST_PATH"
      echo "[HINT] install the timer plist; see docs/ops/ops-runbook.md (macOS launchd section)"
    fi
    warn=1
  fi
  if echo "$LAUNCHD_OUT" | grep -E "last exit code = [1-9]" >/dev/null 2>&1; then
    echo "[WARN] launchd last exit code is non-zero"
    warn=1
  fi
  echo

  echo "== locks =="
  LOCK_DIR="$REPO_ROOT/state/run_locks/opt-data-daily.lock"
  if [[ -d "$LOCK_DIR" ]]; then
    echo "[WARN] lock exists: $LOCK_DIR (previous run may still be active or crashed)"
    warn=1
  else
    echo "no lock dir: $LOCK_DIR"
  fi
  ls -la "$REPO_ROOT/state/run_locks" 2>/dev/null || true
  echo

  echo "== launchd stdout/stderr (tail) =="
  STDOUT_LOG="$RUN_LOG_DIR/launchd_stdout.log"
  STDERR_LOG="$RUN_LOG_DIR/launchd_stderr.log"
  echo "-- stdout: $STDOUT_LOG --"
  tail -n 200 "$STDOUT_LOG" 2>/dev/null || echo "[WARN] missing: $STDOUT_LOG"
  echo "-- stderr: $STDERR_LOG --"
  tail -n 200 "$STDERR_LOG" 2>/dev/null || echo "[WARN] missing: $STDERR_LOG"
  if tail -n 200 "$STDERR_LOG" 2>/dev/null | grep -E \
    "Traceback|ERROR|ConnectionRefused|API connection failed|lock exists" >/dev/null 2>&1; then
    echo "[WARN] stderr contains error patterns (see tail above)"
    warn=1
  fi
  echo

  echo "== artifacts (latest) =="
  echo "-- snapshot logs --"
  ls -lt "$RUN_LOG_DIR/snapshot" 2>/dev/null | head -n 30 || echo "[WARN] missing: $RUN_LOG_DIR/snapshot"
  echo "-- errors --"
  ls -lt "$RUN_LOG_DIR/errors" 2>/dev/null | head -n 30 || echo "[WARN] missing: $RUN_LOG_DIR/errors"
  echo "-- selfcheck --"
  ls -lt "$RUN_LOG_DIR/selfcheck" 2>/dev/null | head -n 30 || echo "[WARN] missing: $RUN_LOG_DIR/selfcheck"
  echo

  echo "== deep inspection (optional) =="
  if [[ -x "$REPO_ROOT/.venv/bin/python" && -f "$CONFIG_PATH" ]]; then
    "$REPO_ROOT/.venv/bin/python" "$REPO_ROOT/scripts/check_schedule_run.py" \
      --date "$DATE_ARG" \
      --config "$CONFIG_PATH" \
      --max-errors 20 || warn=1
  else
    echo "skip: missing .venv/bin/python or config file"
  fi
} | tee "$REPORT"

echo
echo "report: $REPORT"

if [[ "$warn" -eq 1 ]]; then
  exit 2
fi
exit 0
