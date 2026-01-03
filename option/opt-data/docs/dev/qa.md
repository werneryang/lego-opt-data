# QA 与测试说明

> 本文聚焦测试/验收与开发自检，生产调度请参阅 `docs/ops/ops-runbook.md`；实验脚本与内部流程请继续放在 `docs/dev/` 目录。

## 日常生产验收（全量 `config/universe.csv`）
- 前置：IB Gateway/TWS 已登录，具备实时行情权限（无权限则关注 `delayed_fallback` 占比）；`TZ=America/New_York`；使用 `config/opt-data.toml`。
- 命令：
  - 自检：`python -m opt_data.cli selfcheck --date <trade_date> --config config/opt-data.toml --log-max-total 1`
  - 日志扫描：`python -m opt_data.cli logscan --date <trade_date> --config config/opt-data.toml --max-total 1 --write-summary`
- 判定阈值（每日）：槽位覆盖率 ≥90%；`rollup_strategy` 回退率 ≤5%；`missing_oi` 补齐率 ≥95%；`delayed_fallback` 占比 <10%；日志关键字超限为 FAIL。
- 输出位置：`state/run_logs/selfcheck/selfcheck_YYYYMMDD.json`、`state/run_logs/errors/errors_YYYYMMDD.log`、`state/run_logs/errors/summary_YYYYMMDD.json`、`state/run_logs/metrics/metrics_YYYYMMDD.json`。

## 本地/测试冒烟（`data_test/` + 精简清单）
- 前置：使用 `config/opt-data.test.toml`，如需缩减 Universe 可加 `--symbols AAPL,MSFT`。
- 快速链路：  
  `python -m opt_data.cli snapshot --date today --slot now --config config/opt-data.test.toml --symbols AAPL`  
  `python -m opt_data.cli rollup --date today --config config/opt-data.test.toml`  
  `python -m opt_data.cli enrichment --date today --fields open_interest --config config/opt-data.test.toml`
- QA 验证：`python -m opt_data.cli selfcheck --date today --config config/opt-data.test.toml --log-max-total 1`；日志扫描同上。
- 期待输出：`data_test/raw|clean/ib/chain/view=intraday/...`，`state_test/run_logs/*`。

### 详细冒烟步骤（可选）
1. 确保测试配置精简范围（例如 `--symbols AAPL`，或在 `config/opt-data.test.toml` 降低 `max_strikes_per_expiry` 并缩短 `slot_range`）。
2. 盘中采集至少 2 个槽：`python -m opt_data.cli snapshot --date today --slot now --symbols AAPL --config config/opt-data.test.toml`（必要时换另一个槽再跑一次）。
3. 检查输出目录：`data_test/raw/ib/chain/view=intraday/date=YYYY-MM-DD/underlying=AAPL/...` 与 `data_test/clean/ib/chain/view=intraday/...`。
4. 模拟无实时权限：临时设置 `market_data_type=3` 再采集一槽，确认输出包含 `delayed_fallback` 标记。
5. 收盘后跑 `rollup`：`python -m opt_data.cli rollup --date today --config config/opt-data.test.toml`，检查 `rollup_strategy` 与 `rollup_source_slot`。
6. 跑 enrichment：`python -m opt_data.cli enrichment --date today --fields open_interest --config config/opt-data.test.toml`（需要实时行情权限；否则观察降级/失败日志）。
7. 运行自检与日志扫描：`python -m opt_data.cli selfcheck --date today --config config/opt-data.test.toml --log-max-total 1`，并确认 `state_test/run_logs/` 下生成 selfcheck/metrics/errors 文件。

## 指标与日志定位
- 运行指标：`state/run_logs/metrics/metrics_YYYYMMDD.json`（覆盖率、延迟行情占比、rollup 回退率、OI 补齐率等）。
- 错误日志：`state/run_logs/errors/errors_YYYYMMDD.log`；摘要：`state/run_logs/errors/summary_YYYYMMDD.json`。
- 自检报告：`state/run_logs/selfcheck/selfcheck_YYYYMMDD.json`，遇到 FAIL 时会标注 breach 细项并给出补采建议。
- 调试/诊断：必要时开启 `--verbose`（CLI）并保留 `state/run_logs/*` 供事后复盘。

## 已知风险/依赖（持续跟踪）
- 实时行情权限不足时，流程会降级到延迟行情，需关注 `delayed_fallback` 占比并在 `TODO.now.md` 记录处置。
- 交易日历（含早收盘）依赖 `pandas-market-calendars`；缺失时会回退固定 09:30–16:00 槽并在日志标记 `early_close=False`，需人工核对。
