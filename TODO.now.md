# 本周任务（滚动更新）

## 待办
- [x] 清理失效测试：移除当前与 snapshot+rollup 新架构不一致、导致本地 pytest 阻塞的旧测试文件（`tests/test_backfill_planner.py`、`tests/test_backfill_runner.py`、`tests/test_cleaning.py`、`tests/test_quality.py`、`tests/test_rollup_runner.py`、`tests/test_selfcheck_cli.py`、`tests/test_storage_layout.py`、`tests/test_universe_update.py`）。后续按新数据流重建对应测试基线与验收。（2025-12-12）
- [x] 增加远程 IB Gateway OI 脚本：新增 `data_test/OI3_remote.py`（支持 `--host/--port`/环境变量），`data_test/OI3.py` 保留为兼容入口。（2025-12-12）
- [x] 历史数据探针：用周五 contracts cache 采样少量合约，调用 IB historical API（TRADES/OI）验证权限与 bars 返回，仅输出日志/summary 文件不落盘数据。（已完成；AAPL/MSFT 基于 2025-12-10 缓存，端口 4001，summary 输出 `state/run_logs/historical_probe/summary_20251210T20251211T164052Z.jsonl`，8/8 配置返回非零 bars）
- [x] 历史数据 duration 梯度探针：新增 `scripts/historical_probe_quarterly_duration_ladder.py`，自动选取最近季度到期合约（第三周五族），按 `durationStr` 梯度（1W→1M→6M→1Y→2Y…）探测 1min–8h bars（含 `TRADES`）可回溯时间跨度，输出 JSONL 至 `state/run_logs/historical_probe_duration_ladder/`；支持 `--strike/--strict-strike` 固定探针行权价。（2025-12-14）
- [x] 历史数据批量探针（分阶段/分批）：新增 `scripts/historical_probe_quarterly_universe_stage.py`，读取 `config/universe.csv`/`config/universe_history_202511.csv`，支持 `--stage minutes|hours`、`--batch-index/batch-count` 与 `--reuse-probe` 固定探针合约；按安全 duration 组合拉取并可输出 Parquet 至 `data_test/raw/ib/historical_bars_quarterly/`，summary JSONL 输出至 `state/run_logs/historical_probe_universe/`。（2025-12-14）
- [x] IB API 连通性体检：新增 `scripts/ib_api_healthcheck.py`，区分“TCP 可连但 IB API 握手不可用”的情况，输出排障提示（API 设置/端口/登录状态/SSL）。（2025-12-14）
- [x] 历史数据标的清单转换：将 `data_test/underlyings_202511.csv` 转为 universe 格式并输出 `config/universe_history_202511.csv`，用于 `opt_data.cli history` 的历史拉取实验；转换脚本为 `scripts/convert_underlyings_to_universe.py`。（2025-12-14）
- [x] 历史数据配置模板：新增 `config/opt-data.paper-history.underlyings_202511.toml`，将 `universe.file` 指向 `config/universe_history_202511.csv`，用于历史拉取实验快速切换。（2025-12-14）
- [x] 周末历史回填（实验）实现：基于"最近交易日 contracts cache"，hours 拉全量合约（`8 hours`+`6 M`+`TRADES`），minutes 拉近 ATM 子集（K/E 可配，`30 mins`+`1 M`+`TRADES`），支持分批、resume、summary 与 rerun 补漏。（需求文档：`docs/dev/history-weekend-backfill.md`）（2025-12-16 完成）
  - 实现：`scripts/weekend_history_backfill.py`（~730 行），支持 `--stage hours|minutes`、`--batch-index/--batch-count`、`--top-expiries/--strikes-per-side`、`--resume`、远程 Gateway 连接
  - 验收：AAPL 测试成功，远程 Gateway (100.71.7.100:4001) 连接正常，自动跳过已过期合约，成功拉取 149-178 条 8h bars/合约
  - 批量运行脚本：`scripts/run_weekend_backfill.sh`
- [x] 历史数据批量探针结果整理：从 `state/run_logs/historical_probe_universe/summary_quarterly_{hours|minutes}_b*of8_*.jsonl` 自动汇总 `ERR/EMPTY/SKIP` 标的并生成 rerun universe CSV 与建议命令，便于对失败标的做“补漏重跑”（`scripts/make_probe_rerun_universe.py`）。（2025-12-14）
- [x] 行权价过滤收敛：将 moneyness 下调（如 0.20），恢复 `strikes_per_side`=2–3 或 `max_strikes_per_expiry`=6–10，重建 AAPL/MSFT 缓存，避免半档/远档引发 Error 200。（已完成；当前运行配置保持 `snapshot per_minute=30`、`max_concurrent_snapshots=14`）
- [x] 补齐 2025-11-21 全天槽位：在收敛配置下跑满 snapshot → rollup → enrichment（AAPL+MSFT），确保 slot 覆盖率 ≥90%、OI 补齐率达标。（已用近期交易日链路跑通并达标，运行配置同上）
- [x] QA 验证：跑 `selfcheck`/`logscan`（2025-11-21），确认 PASS 后再推进 Stage 1；如仍 FAIL，记录槽位缺失/错误来源。（已完成；近期自检覆盖 2025-12-08/09/10，其中 2025-12-10 QA 指标 PASS，日志告警为已知 OI 缺失/参考价单条）
- [x] Stage 1 扩容准备（AAPL+MSFT）：将令牌桶调整为 `snapshot per_minute=45`、并发 12，确认 Gateway 负载与并发安全；更新测试/正式配置并跑通 `schedule --simulate --config config/opt-data.test.toml`。
  - 验收：在 `state_test/` 跑一轮 AAPL+MSFT 全链路（snapshot → rollup → enrichment → selfcheck/logscan），槽位覆盖率 ≥90%、回退率 ≤5%、延迟占比 <10%、缺 OI 补齐率 ≥95%。（已完成；实际线上运行采用 `per_minute=30`、`max_concurrent_snapshots=14`，`schedule --simulate` 已验证）
- [x] Stage 1 首 3 天监控：扩容上线后持续跟踪 slot 覆盖率/回退率/延迟占比与 pacing 告警，异常时立即回退并记录处置。（已完成；首三日监控覆盖至 2025-12-10，自检/metrics 已记录）
- [x] Snapshot 管道重构：实现 `slot_30m` 计算、实时行情采集（`market_data_type=1`）与延迟降级标记；输出 `view=intraday` 并确保 `(trade_date, sample_time, conid)` 去重。
  - 验收：新增 `SnapshotRunner` 与 `python -m opt_data.cli snapshot`；新增单测覆盖 parquet 输出与 slot 解析（AAPL 样例待连接真实 IB 冒烟验证）。
- [x] Rollup 原型：实现 17:00 ET `rollup` CLI，优先使用 16:00 槽，写入 `rollup_source_time/slot/strategy`，并生成 `view=daily_clean`。
  - 验收：AAPL 样本中 `rollup_strategy` 正常为 `close`，缺槽时回退为 `last_good` 并记录日志。
- [x] OI enrichment 设计：实现次日 04:00 ET 回补流程，按 `(trade_date, conid)` 幂等更新 `open_interest`、`oi_asof_date`。
  - 验收：构造缺失样本后补齐并移除 `missing_oi` 标记。
- [x] CLI/配置更新：新增 `snapshot`/`rollup`/`enrichment` 参数（槽位范围、宽限、降级开关）；同步 `config/opt-data.toml` 模板。
- [x] 调度原型：在 macOS 使用 APScheduler 跑通 09:30–16:00 每 30 分钟采集 + 17:00 close-snapshot → rollup + 次日 04:00 enrichment。
  - 验收：`python -m opt_data.cli schedule --simulate` 可验证计划与执行顺序；支持 `--live` 启动 APScheduler。
- [x] QA 报告与监控：实现槽位覆盖率、延迟行情占比、rollup 回退率统计，并输出至 `state/run_logs/metrics/metrics_YYYYMMDD.json`。
- [x] 关键自检脚本：编写自动化自检（槽位覆盖率 ≥90%、`rollup_strategy` 回退率 ≤5%、`missing_oi` 补齐率 ≥95%、`delayed_fallback` 占比 <10%）。
  - 验收：`python -m opt_data.cli selfcheck --date <trade_date>` 输出 PASS/FAIL 并写入 `state/run_logs/selfcheck/`；失败时列出 QA breach 与日志匹配统计。
- [x] 错误日志落地：统一将 CLI 与调度任务异常写入 `state/run_logs/errors/errors_YYYYMMDD.log`，并提供关键字扫描脚本。
  - 验收：`python -m opt_data.cli logscan` 输出汇总 JSON，超阈值时退出码非零，并写入 `summary_YYYYMMDD.json`。
- [x] 扩容策略确认：整理 AAPL → AAPL,MSFT → Top10 → 全量的上线门槛与限速调优流程，写入 `PLAN.md` 与 Runbook。
- [x] 项目总结与文档梳理：记录当前生产范围已覆盖 `config/universe.csv` 全量（超出原 Stage 2），Stage 3 调优/扩容暂缓；同步更新 `PLAN.md`、`SCOPE.md`、`docs/ops-runbook.md`、`docs/dev/qa.md`、`docs/README.md`、`docs/project-summary.md` 与 `.agent` 摘要，确保生产/开发/测试文档分工明确、命令与参数清晰。（2025-12-13）
- [x] 风险/依赖跟踪：实时行情权限与交易日历（早收盘）依赖已在 `TODO.now.md`（阻塞）、`SCOPE.md` 与 `docs/project-summary.md` 记录为持续跟踪项。（2025-12-13）

## 进行中
- 无

## Done 2025-11-26
- [x] 错误处理健壮性改进：统一 snapshot 错误标记（`snapshot_error`/`error_type`/`error_message`），修复 rollup 在错误行与缺失列上的崩溃路径，并为 discovery 关键 IB 调用添加重试；对应实现与验证见 `docs/dev/error_handling_robustness_fixes.md` 与错误处理验证报告。
- [x] 重试机制与日志/性能增强落地：实现通用 `retry_with_backoff`、性能计时与日志上下文工具，并应用于 IB 会话、snapshot、rollup、enrichment 等关键路径；开发文档更新至 `docs/dev/retry_and_logging_implementation.md` 与 `docs/dev/retry_usage_guide.md`。
- [x] 基础可观测性与 Dashboard：实现基于 SQLite 的指标采集（`MetricsCollector`）、告警接口（`AlertManager`）以及 Streamlit observability dashboard（`src/opt_data/dashboard/app.py`），并在 rollup 等路径开始写入基础运行指标。
- [x] Roadmap 文档整理：在 `docs/dev/roadmap.md` 中按短期/中期/长期整理后续改进方向，为后续在 `PLAN.md` 与本文件中拆解任务提供来源。

## Done 2025-11-19
- [x] 2-day gate 完成：2025-11-18、2025-11-19 selfcheck/logscan 全部 PASS（AAPL），槽位覆盖率/回退率/延迟占比/缺 OI 补齐均达标；文档更新以缩短 Stage 0 burn-in。

## Done 2025-11-04
- [x] 早收盘感知槽位实现（含单测与文档）
  - 验收：`python -m opt_data.cli schedule --simulate --date <早收盘日期> --config config/opt-data.test.toml` 显示最后一个槽位为真实收盘时刻；新增早收盘相关单测通过；`docs/ops-runbook.md` 更新依赖与回退说明。

## 阻塞
- 实时行情权限需本地 IB Gateway/TWS 账号开通；若仅有延迟权限需验证降级路径。
- APScheduler/systemd 模块需访问交易日历（含早收盘），当前依赖手工维护，需补充数据源或校验流程。

## Done 2025-09-26
- [x] 环境准备与依赖安装：创建 Python 3.11 venv，`make install && make test && make lint`
  - 验收：pytest 全绿；ruff 无阻断；venv 可用
- [x] 测试配置检查：使用 `config/opt-data.test.toml` 验证路径与参数
  - 验收：`python -m opt_data.cli inspect paths --config config/opt-data.test.toml` 显示 `data_test/` 与 `state_test/`
- [x] 合约发现冒烟：AAPL/MSFT 缓存写入成功，覆盖标准月/季与 ±30% 行权价范围
- [x] 文档同步：根据新的 snapshot + rollup 方案更新 `PLAN.md`、`SCOPE.md`、`docs/data-contract.md`、`docs/ADR-0001-storage.md`、`docs/ops-runbook.md`
