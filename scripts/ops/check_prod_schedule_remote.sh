#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Run opt-data production schedule check on a remote host and pull the report back.

Usage:
  scripts/ops/check_prod_schedule_remote.sh --host HOST --repo REMOTE_REPO [options]

Required:
  --host HOST             Remote host (e.g., michaels-imac or 10.0.0.2)
  --repo REMOTE_REPO      Remote repo absolute path (e.g., /Users/datareader/opt-data)

Options:
  --user USER             SSH user (default: current user)
  --date DATE             today or YYYY-MM-DD (default: today)
  --config PATH           Remote config path (default: REMOTE_REPO/config/opt-data.local.toml)
  --label LABEL           launchd label (default: com.legosmos.opt-data.timer)
  --remote-script PATH    Remote check script path (default: REMOTE_REPO/scripts/ops/check_prod_schedule.sh)
  --dest DIR              Local directory to save report (default: ./state/run_logs/ops_checks)
  --identity PATH         SSH identity file
  --ssh-opts "OPTS"       Extra ssh options
  --no-pull               Skip pulling report file (leave only local stdout log)
  -h, --help              Show help

Example:
  scripts/ops/check_prod_schedule_remote.sh \
    --host michaels-imac \
    --user datareader \
    --repo /Users/datareader/opt-data
EOF
}

HOST=""
USER="$(whoami)"
REMOTE_REPO=""
DATE_ARG="today"
LABEL="com.legosmos.opt-data.timer"
REMOTE_SCRIPT=""
REMOTE_CONFIG=""
DEST_DIR="./state/run_logs/ops_checks"
IDENTITY=""
SSH_OPTS=""
PULL_REPORT=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="${2:-}"; shift 2;;
    --user) USER="${2:-}"; shift 2;;
    --repo) REMOTE_REPO="${2:-}"; shift 2;;
    --date) DATE_ARG="${2:-}"; shift 2;;
    --config) REMOTE_CONFIG="${2:-}"; shift 2;;
    --label) LABEL="${2:-}"; shift 2;;
    --remote-script) REMOTE_SCRIPT="${2:-}"; shift 2;;
    --dest) DEST_DIR="${2:-}"; shift 2;;
    --identity) IDENTITY="${2:-}"; shift 2;;
    --ssh-opts) SSH_OPTS="${2:-}"; shift 2;;
    --no-pull) PULL_REPORT=0; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2;;
  esac
done

if [[ -z "$HOST" || -z "$REMOTE_REPO" ]]; then
  echo "Missing --host or --repo" >&2
  usage
  exit 2
fi

REMOTE_SCRIPT="${REMOTE_SCRIPT:-$REMOTE_REPO/scripts/ops/check_prod_schedule.sh}"
REMOTE_CONFIG="${REMOTE_CONFIG:-$REMOTE_REPO/config/opt-data.local.toml}"

mkdir -p "$DEST_DIR"
STAMP_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
LOCAL_STDOUT_LOG="$DEST_DIR/remote_check_stdout_${STAMP_UTC}.log"

SSH_BASE=(ssh)
if [[ -n "$IDENTITY" ]]; then
  SSH_BASE+=(-i "$IDENTITY")
fi
if [[ -n "$SSH_OPTS" ]]; then
  # shellcheck disable=SC2206
  SSH_BASE+=($SSH_OPTS)
fi

REMOTE_CMD_STR=$(
  cat <<EOF
set -euo pipefail
cd "$REMOTE_REPO"
"$REMOTE_SCRIPT" --date "$DATE_ARG" --config "$REMOTE_CONFIG" --label "$LABEL"
EOF
)

echo "[remote] ${USER}@${HOST}:${REMOTE_REPO}"
echo "[remote] script: $REMOTE_SCRIPT"
echo "[remote] date: $DATE_ARG config: $REMOTE_CONFIG label: $LABEL"

set +e
"${SSH_BASE[@]}" "${USER}@${HOST}" "bash -lc $(printf '%q' "$REMOTE_CMD_STR")" 2>&1 | tee "$LOCAL_STDOUT_LOG"
REMOTE_EXIT=${PIPESTATUS[0]}
set -e

echo "[local] remote exit code: $REMOTE_EXIT"
echo "[local] stdout log: $LOCAL_STDOUT_LOG"

REPORT_PATH=""
if [[ "$PULL_REPORT" -eq 1 ]]; then
  REPORT_PATH="$(awk '/^report: /{print $2}' "$LOCAL_STDOUT_LOG" | tail -n 1)"
  if [[ -z "$REPORT_PATH" ]]; then
    echo "[local] report path not found in stdout log; probing remote"
    REPORT_PATH="$("${SSH_BASE[@]}" "${USER}@${HOST}" "ls -t \"$REMOTE_REPO/state/run_logs/ops_checks\"/prod_schedule_check_*.log 2>/dev/null | head -n 1")"
  else
    LOCAL_REPORT="$DEST_DIR/$(basename "$REPORT_PATH")"
    echo "[local] pulling report: $REPORT_PATH -> $LOCAL_REPORT"
    scp "${USER}@${HOST}:$REPORT_PATH" "$LOCAL_REPORT"
  fi
  if [[ -n "$REPORT_PATH" && ! -f "${LOCAL_REPORT:-}" ]]; then
    LOCAL_REPORT="$DEST_DIR/$(basename "$REPORT_PATH")"
    echo "[local] pulling report (fallback): $REPORT_PATH -> $LOCAL_REPORT"
    scp "${USER}@${HOST}:$REPORT_PATH" "$LOCAL_REPORT"
  fi
else
  echo "[local] pull skipped (--no-pull)"
fi

exit "$REMOTE_EXIT"
