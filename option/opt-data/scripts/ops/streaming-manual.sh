#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

exec ./.venv/bin/python -m opt_data.cli streaming \
  --config config/opt-data.streaming.local.toml \
  --flush-interval 1800 \
  --metrics-interval 300 \
  "$@"
