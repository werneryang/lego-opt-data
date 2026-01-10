# 项目阶段性总结（Snapshot + Rollup）

## 当前状态
- **生产范围**：已覆盖 `config/universe.csv` 全量清单（相当于原 Stage 2 已完成）；更高并发/分批调度的 Stage 3 调优暂缓。
- **运行参数（现行）**：`rate_limits.snapshot.per_minute=30`、`max_concurrent_snapshots=14`、槽位间隔 30 分钟、单槽宽限 `±120s`。
- **调度链路（ET）**：09:30–16:00 `snapshot`（每 30 分钟） → 17:30 `close-snapshot` 后紧接 `rollup` → 次日 04:30 `enrichment` → `selfcheck`/`logscan` 验收。

## 架构与数据落地
- **Snapshot**：采集期权链实时/延迟行情快照，输出 `view=intraday`（盘中）与 `view=close`（收盘）。
- **Rollup**：优先使用 `view=close` 生成 `view=daily_clean`（并可生成 `view=daily_adjusted`），记录 `rollup_source_*` 与回退策略。
- **Enrichment**：T+1 回补慢字段（如 `open_interest`），按 `(trade_date, conid)` 幂等更新。
- **数据契约/分区/主键**：见 `docs/architecture/data-contract.md`。
- **日志与状态**：统一在 `state/run_logs/`（errors/selfcheck/metrics 等）。

## 生产日常操作（值班）
- 启动常驻调度：`python -m opt_data.cli schedule --live --config config/opt-data.snapshot.local.toml`
- 打开 UI：`streamlit run src/opt_data/dashboard/app.py`
- 收盘后验收：
  - `python -m opt_data.cli selfcheck --date today --config config/opt-data.snapshot.local.toml --log-max-total 1`
  - `python -m opt_data.cli logscan --date today --config config/opt-data.snapshot.local.toml --max-total 1 --write-summary`
- 生产运维入口：`docs/ops/ops-runbook.md`（包含“一屏清单”、常见故障与数据/日志位置）。

## 验收标准（当前）
- 槽位覆盖率 ≥90%
- `rollup_strategy` 回退率 ≤5%
- `missing_oi` 补齐率 ≥95%
- `delayed_fallback` 占比 <10%
- `logscan/selfcheck` 退出码为 0（允许少量已知 warn/参考价类错误，需在 run_logs 备注）

## 已知风险/依赖（持续跟踪）
- **实时行情权限**：无权限时会降级延迟行情，需关注 `delayed_fallback` 占比与 OI 获取能力。
- **交易日历/早收盘**：依赖 `pandas-market-calendars`；缺失时回退固定 09:30–16:00 槽位，需人工核对。
- **IB pacing**：发现阶段不加应用层限速，需通过指标与日志持续观察 pacing 告警。

## 文档入口
- 文档总目录：`docs/README.md`
- 生产运维：`docs/ops/ops-runbook.md`
- QA/测试：`docs/dev/qa.md`
- 开发/诊断补充：`docs/dev/ops-notes.md`
- 计划与范围：`PLAN.md`、`SCOPE.md`、`TODO.now.md`

