# 本周任务（滚动更新）

## 待办
- [x] Snapshot 管道重构：实现 `slot_30m` 计算、实时行情采集（`market_data_type=1`）与延迟降级标记；输出 `view=intraday` 并确保 `(trade_date, sample_time, conid)` 去重。
  - 验收：新增 `SnapshotRunner` 与 `python -m opt_data.cli snapshot`；新增单测覆盖 parquet 输出与 slot 解析（AAPL 样例待连接真实 IB 冒烟验证）。
- [x] Rollup 原型：实现 17:00 ET `rollup` CLI，优先使用 16:00 槽，写入 `rollup_source_time/slot/strategy`，并生成 `view=daily_clean`。
  - 验收：AAPL 样本中 `rollup_strategy` 正常为 `close`，缺槽时回退为 `last_good` 并记录日志。
- [x] OI enrichment 设计：实现次日 07:30 ET 回补流程，按 `(trade_date, conid)` 幂等更新 `open_interest`、`oi_asof_date`。
  - 验收：构造缺失样本后补齐并移除 `missing_oi` 标记。
- [x] CLI/配置更新：新增 `snapshot`/`rollup`/`enrichment` 参数（槽位范围、宽限、降级开关）；同步 `config/opt-data.toml` 模板。
- [x] 调度原型：在 macOS 使用 APScheduler 跑通 09:30–16:00 每 30 分钟采集 + 17:00 rollup + 次日 07:30 enrichment。
  - 验收：`python -m opt_data.cli schedule --simulate` 可验证计划与执行顺序；支持 `--live` 启动 APScheduler。
- [x] QA 报告与监控：实现槽位覆盖率、延迟行情占比、rollup 回退率统计，并输出至 `state/run_logs/metrics/metrics_YYYYMMDD.json`。
- [x] 关键自检脚本：编写自动化自检（槽位覆盖率 ≥90%、`rollup_strategy` 回退率 ≤5%、`missing_oi` 补齐率 ≥95%、`delayed_fallback` 占比 <10%）。
  - 验收：`python -m opt_data.cli selfcheck --date <trade_date>` 输出 PASS/FAIL 并写入 `state/run_logs/selfcheck/`；失败时列出 QA breach 与日志匹配统计。
- [x] 错误日志落地：统一将 CLI 与调度任务异常写入 `state/run_logs/errors/errors_YYYYMMDD.log`，并提供关键字扫描脚本。
  - 验收：`python -m opt_data.cli logscan` 输出汇总 JSON，超阈值时退出码非零，并写入 `summary_YYYYMMDD.json`。
- [x] 扩容策略确认：整理 AAPL → AAPL,MSFT → Top10 → 全量的上线门槛与限速调优流程，写入 `PLAN.md` 与 Runbook。

## 进行中
- 无

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
