# 历史数据周末回填（实验）需求梳理

> 目的：在不影响生产 snapshot/rollup/enrichment 的前提下，以 **data_test** 为落地目录，尽快实现“按盘后合约集合批量拉取历史 bars”的能力，并通过周末分阶段跑完大 universe。

## 背景与动机
- IBKR 历史数据接口是按 **单合约(conId) reqHistoricalData** 拉取；探针脚本已证明单合约在部分 barSize/duration 组合上可行。
- 需要将“单合约探针”扩展为“按盘后快照同一套 expiry/strike/right 合约集合”做批量历史拉取，以便后续在程序中参数化与调度。

## 目标（MVP）
1. **合约集合**：以“最近一个交易日”的 contracts cache 为准（每个 symbol 各自取最新 cache date）。
2. **hours 阶段**：对每个 symbol 的合约集合拉取 `TRADES` 的 `8 hours` bars，回溯 `6 M`（`useRTH=true`），落盘 Parquet。
3. **minutes 阶段**：只对“活跃子集”拉取 `TRADES` 的分钟级 bars（先从 `30 mins` + `1 M` 开始），落盘 Parquet。
4. **断点续跑**：支持 batch 切片与 resume；每次运行输出 summary JSONL，便于生成补漏 rerun universe。

## 非目标（本阶段明确不做）
- 不对 `TRADES` 的 `no data` 自动 fallback 到 `MIDPOINT`（避免请求量扩大与数据类型混杂）。
- 不尝试对 discovery 阶段做 `reqContractDetails`（遵守 2025 升级要求：只用 `reqSecDefOptParams(exchange='SMART')` + 批量 `qualifyContracts/Async`）。
- 不把历史回填纳入生产调度（仅用于 data_test 与实验/诊断）。

## 关键约束与约定
- **Python**：3.11；对 IBKR 只用 `ib_insync`。
- **时区**：America/New_York；历史 bars `useRTH=true`（默认）。
- **数据类型**：TRADES（分钟级需要成交量时）。
- **输出目录**：实验落在 `data_test/`（避免污染生产 `data/`）。

## 合约集合来源（contracts cache）
- contracts cache 由项目 discovery 流程生成并落盘（示例：`state/contracts_cache/{SYMBOL}_{YYYY-MM-DD}.json` 或 `state_test/contracts_cache/...`，取决于配置）。
- 选择策略：每个 symbol 取 **最新日期** 的 cache 文件作为“最近一个交易日”的合约集合。
- 若 cache 缺失：本实验流程可选择失败并记录（不建议隐式 rebuild，避免引入不可控 strikes）。

## minutes 活跃子集（MVP 定义：近 ATM）
由于 contracts cache 不包含 volume/OI（或不稳定），MVP 采用 **近 ATM 子集**：
- 参考价：优先用“最近交易日的 underlying close”（从现有 rollup/close-snapshot 或临时用 `1 day TRADES` 拉取）。
- 选择规则（可配置 K/E）：
  - expiries：按到期日由近到远取前 `E` 个；
  - strikes：对每个 expiry、每个 right（C/P），按 `abs(strike - close)` 排序取前 `K` 个；
  - 合并去重后作为 minutes 阶段要拉的合约集合。
- 预期影响：
  - 显著减少分钟级请求量与 `EMPTY`；
  - 不保证“真正交易最活跃”，但足以尽快跑通全流程。

后续增强（非 MVP）：接入 close-snapshot/rollup 的 `volume/open_interest`，按 TopN 做更准确的活跃子集。

## 分阶段/分批运行（周末建议）
- hours 周末：先跑 `8 hours + 6 M`（全合约集合）。
- minutes 周末：先跑 `30 mins + 1 M`（活跃子集），再按需要扩展到 `15/5/1 min`。
- universe 分批：使用稳定切片 `batch-count/batch-index`，避免重复与便于故障恢复。

## 输出与可观测性
- bars 输出（建议沿用现有探针布局）：
  - `data_test/raw/ib/historical_bars_<scope>/{SYMBOL}/{conId}/{WHAT}/{BAR}.parquet`
- 运行 summary（JSONL）：
  - `state/run_logs/<...>/summary_*.jsonl`
  - 每条记录至少包含：symbol、conId、barSize、what、duration、bars、first/last、error_code/message、output_path。
- 补漏流程：
  - 通过 summary 聚合 `ERR/EMPTY` 生成 rerun universe CSV，再以更严格参数（如 `--no-skip-underlying-close`、更小 K/E）补跑。

## 增量补全（推荐默认）
`scripts/weekend_history_backfill.py` 支持对已落盘的合约做 **增量追加**：
- 若目标 Parquet 已存在：读取已有数据的最大时间戳 `max(ts)`，只追加本次拉取结果里 `ts > max(ts)` 的 bars。
- 合并后按 `ts, conid, bar_size, what_to_show` 去重并排序，再写回同一路径。
- 若历史上存在旧文件缺少 `ts` 字段或读失败：会自动禁用增量合并并回退到覆盖写（避免崩溃）。

运行开关：
- 默认启用：`--incremental`（默认 true）。
- 关闭增量（回到“已有文件直接跳过/或覆盖”行为）：`--no-incremental`（此时可配合 `--resume/--no-resume`）。

## 已有脚本/实现可复用点
- `scripts/historical_probe_quarterly_universe_stage.py`：分批/分阶段探针与落盘框架（目前为“每 symbol 1 张探针合约”）。
- `src/opt_data/ib/discovery.py::discover_contracts_for_symbol`：contracts cache 生成与 SMART-only discovery（2025 flow）。
- `src/opt_data/pipeline/history.py::HistoryRunner`：按 contracts cache 对每个 conId 拉历史的雏形（当前输出 JSON，且未形成 minutes 子集与 parquet 输出矩阵）。

## 验收（MVP）
- 能对一个小 universe（例如 10 个标的）在 hours 阶段跑完并落盘；summary 无崩溃、支持 resume。
- minutes 阶段按 K/E 子集能在合理时间内跑完；`EMPTY` 比全量 strikes 明显降低。
- 批量跑（>=300 symbols）时，Gateway 不因 pacing 被频繁断开；失败可通过 rerun universe 补齐。
