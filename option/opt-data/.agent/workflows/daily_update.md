---
description: Run the daily data update process
---
This workflow runs the daily production update (ET timezone).

1. Start streaming subscription (trading days 09:35–16:00 ET)
// turbo
python -m opt_data.cli streaming --config config/opt-data.local.toml --duration 23100

2. Start scheduler (recommended)
// turbo
python -m opt_data.cli schedule --live --exit-when-idle --config config/opt-data.local.toml

3. If running manually for a given trade_date (same ET day)
   - 17:30 close snapshot → rollup  
   - Next day 04:30 enrichment → selfcheck/logscan
// turbo
python -m opt_data.cli close-snapshot --date today --config config/opt-data.local.toml
python -m opt_data.cli rollup --date today --config config/opt-data.local.toml
python -m opt_data.cli enrichment --date today --config config/opt-data.local.toml
python -m opt_data.cli selfcheck --date today --config config/opt-data.local.toml --log-max-total 1
python -m opt_data.cli logscan --date today --config config/opt-data.local.toml --max-total 1

Notes:
- For macOS unattended mode, use launchd + `--exit-when-idle` (template: `docs/ops/launchd/com.legosmos.opt-data.timer.plist`).
- For macOS streaming unattended mode, use launchd template `docs/ops/launchd/com.legosmos.opt-data.streaming.plist`.
