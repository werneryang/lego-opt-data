# IBKR 历史 Bars（经验边界）

用于指导 `reqHistoricalData(durationStr, barSizeSetting, whatToShow)` 的默认参数选择与诊断；具体生产运维入口以 `docs/ops/ops-runbook.md` 为准。

## 探针脚本
- `scripts/historical_probe_quarterly_duration_ladder.py`
- `scripts/historical_probe_quarterly_universe_stage.py`（分阶段/分批 + `probe.json` 复用探针合约）
- 输出：`state/run_logs/historical_probe_duration_ladder/duration_ladder_<SYMBOL>_<run_id>.jsonl`

`scripts/historical_probe_quarterly_universe_stage.py` 默认更偏“稳健参数”：`1 min` 用 `1 M`，`>=5 mins/1 hour` 默认 `6 M`（通常仍会被合约可用起点截断）；必要时可打开 `--discovery-per-minute/--discovery-burst` 做 discovery 侧的轻量限速（默认关闭）。

## 已记录的经验值（TSLA）
- 样本：`TSLA 20251219 C 460`（`useRTH=True`）
- `barSize=1 min`：`TRADES/MIDPOINT` 在 `durationStr=1 M` 可返回；`durationStr>=6 M` 本次为空（bars=0）。需要更长需分块回拉。
- `barSize=5 mins`–`8 hours`：本次 `TRADES` 实际可回溯约 123 天，`MIDPOINT` 约 65 天；把 `durationStr` 设到 `5 Y` 也会被合约可用起点截断。

来源：`docs/dev/ops-notes.md` 中“历史 Bars 拉取边界（经验数据）”。
