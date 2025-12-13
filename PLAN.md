# 4 周项目计划

## 背景
本项目聚焦 S&P 500（可配置）标的的期权链日内采集与日终归档：在交易日 09:30–16:00（America/New_York）每 30 分钟记录一次实时快照，17:00 ET 先做收盘快照（close-snapshot）再 rollup 聚合为日级视图（含回退规则），次日 04:00 enrichment 补齐慢字段。目标是在 macOS 环境验证后迁移到 Linux 定时执行，确保快照与日终数据可恢复、可审计，且不再执行历史回填。

## 范围与里程碑
- **M1（第 1 周）**：落地实时 snapshot 采集骨架（`acquisition.mode=snapshot`，`IB_MARKET_DATA_TYPE=1`），完成 09:25 ET 会话合约发现与冻结策略、槽位计算（含 16:00 槽宽限）、单标的冒烟（AAPL）并写入 `view=intraday` 数据。
- **M2（第 2 周）**：实现 17:00 ET close-snapshot → rollup（收盘快照优先、回退策略、公司行动调整）、T+1 `open_interest` enrichment、数据契约与 QA 指标更新（slot 覆盖率、回退率、IV/Greeks 合规）。
- **M3（第 3 周）**：完善调度与运维（APScheduler/launchd/systemd）、实时限速与退避、监控告警、日志与状态记录；周度 compaction 支持 intraday+daily 视图；加入延迟行情降级与标记。
- **M4（第 4 周）**：扩容至多标的（≥50）并评估限速调优，完善文档（Runbook、数据契约、配置模板、渐进扩容指南）、Linux 环境试运行与验收。

## 关键任务拆解
- **槽位与调度**：定义 14 个 30 分钟槽（含 16:00），处理夏/冬令时与早收盘，ET 调度、UTC 存储、宽限窗口重试。
- **合约发现策略（2025 升级）**：09:25 ET 冻结一日合约集合（基于前收 ±30%、标准月/季到期），仅使用 `reqSecDefOptParams( exchange='SMART' )` 生成候选；直接批量 `qualifyContracts/Async` 获取 `conId` 并写入缓存；不再调用 `reqContractDetails`；发现阶段不施加应用层限流（采用批量资格化并遵循 IB pacing）。
- **实时采集管道**：使用 `ib_insync` `reqMktData` 拉取实时快照，记录 `sample_time`/`slot_30m`，保存 `market_data_type` 与降级标记，按槽幂等写入 `data/raw|clean/ib/chain/view=intraday`。
- **日终归档**：17:00 close-snapshot 后 rollup 按策略选取快照，补写 `rollup_source_*`、公司行动调整，产出 `view=daily_clean|daily_adjusted` 并处理幂等覆盖。
- **延迟字段补全**：维护次日 04:00 ET `open_interest` enrichment 任务，按 `(trade_date, conid)` 幂等更新日级数据。
- **存储与压缩**：Parquet `date/underlying/exchange` 分区；热数据 Snappy，冷数据 ZSTD，周度 compaction 目标 128–256MB；可选同日小文件合并（默认关闭）。
- **QA 与监控**：槽位覆盖率 ≥90%、去重（`trade_date, sample_time, conid`）、IV/Greeks 范围、rollup 回退告警、pacing 监控、延迟行情与缺失字段标记。
- **调度与运维**：CLI `snapshot`/`rollup`/`enrichment` 命令、配置模板、日志/状态目录、集中式错误日志（`state/run_logs/errors/`），故障恢复与扩容流程。

## 自我检查与验证
- **Snapshot 自检**
  - 每日确认槽位覆盖率 ≥90%，`slot_30m` 无缺号且重复键被剔除。
  - 抽查 3 个标的确保 `market_data_type` 默认为 1，若降级则存在 `delayed_fallback` 标记。
  - 统计 `data_quality_flag` 中 `slot_retry_exceeded` 是否为 0；如非 0 需追加补采。
- **Rollup 自检**
  - 检查 `rollup_strategy` 分布，`close` 占比 ≥95%；若出现 `last_good`/`slot_1530`，需记录原因。
  - 对比 `rollup_source_time` 与 16:00 槽快照，确认时间戳一致或在宽限内。
  - 验证 `daily_clean` 与 `intraday` 中 `(trade_date, conid)` 行数匹配，无丢失或重复。
- **Enrichment 自检**
  - 确认 enrichment 当日新增 `open_interest` 行数与 `missing_oi` 标记减少量一致。
  - 检查 `oi_asof_date` 是否与目标交易日一致（或按配置延迟）。
- **存储与保留**
  - 周度合并后，抽检 3 个分区文件大小是否在 128–256MB 目标区间内。
  - 每周核实 `intraday` 分区保留天数 ≤ `intraday_retain_days`，删除/迁移记录在 `state/run_logs/retention*.jsonl`。
- **监控与告警**
  - 槽位覆盖率、rollup 回退率、延迟行情占比三项指标须纳入监控面板；阈值触发后 30 分钟内完成登记。
  - 日志目录与磁盘占用超过 80% 时需在 `TODO.now.md` 追加行动项。
  - 每日汇总错误日志（`errors_YYYYMMDD.log`）并进行关键字扫描；严重错误需在 1 小时内立项处理。

## 范围边界
- 日内数据源仅限 IBKR/TWS 实时或延迟行情；不提供逐笔或毫秒级数据。
- 不执行历史回填；仅维护 09:30–16:00 30 分钟快照与 17:00 日终 close-snapshot → rollup。
- 默认宇宙为 S&P 500，可通过 `config/universe.csv` 缩减或扩展；上线前分批扩容。
- 初期仅覆盖本地/macOS 环境与指定 Linux 主机；不包含云端部署。
- 旧回填/清洗相关测试基线已移除；后续测试将以 snapshot+rollup+enrichment 新管道为准重建。

## 风险与缓解
- **实时行情权限不足**：提供延迟行情降级（自动/手动）、记录 `delayed_fallback` 标记，并在 Runbook 中列出申请/排查步骤。
- **槽位缺失或回退频繁**：配置宽限重试、slot 覆盖率监控；连续缺槽触发告警并支持补采。
- **Greeks/字段缺失**：记录 `missing_greeks` 等标记；QA 抽样确保核心字段合理。
- **open_interest 延迟**：次日 enrichment 异常时标记 `missing_oi` 并保持追踪；超过 SLA 进入人工处理。
- **限速与并发**：初始令牌桶保守（30 req/min），观察 pacing violation；必要时调低并发或拆分宇宙。
- **存储膨胀**：周度 compaction + 60 天 intraday 保留策略，磁盘占用阈值监控。
- **调度失败**：提供 launchd/systemd runbook、状态文件断点续跑与手动补采指南。

## 扩容策略与门槛
- **阶段 0：AAPL（基线）**
  - 最近连续 2 个交易日通过自检/日志（2025-11-18、2025-11-19）：槽位覆盖率 ≥90%、`rollup_strategy` 回退率 ≤5%、延迟行情占比 <10%、`missing_oi` 补齐率 ≥95%。
  - 无 pacing violation 或仅出现 1 次且定位明确；`errors_YYYYMMDD.log` 中无未处理异常。
  - 保持默认限速：`snapshot per_minute=30`、`max_concurrent_snapshots=10`，扩容前需强调缩短 burn-in 带来的波动风险。
- **阶段 1：AAPL + MSFT（双标的）**
  - 阶段 0（2-day gate）完成后即可扩容，扩容后前 3 个交易日重点监控；若槽位覆盖率跌破 88% 或 pacing 告警 >2 次，回退调优或暂缓并发提升。
  - 令牌桶调整：`snapshot per_minute=45`，视 Gateway 负载将并发提升至 12；宽限与重试策略保持。
  - Runbook 需补充并发调节、Gateway session 健康检查与故障切换步骤。
  - 已批准偏差：当前 Stage 1 运行保持 `snapshot per_minute=30`、`max_concurrent_snapshots=14`，提升至 45/12 需额外评审。
- **阶段 2：Top 10（按 `config/universe.csv` 前十权重）**
  - 阶段 1 结束后在 Rollup/OI enrichment 上保持 7 个交易日零人工干预，QA 指标全部满足阈值。
  - 启用 `midday_refresh`（仅新增合约）并跟踪新增请求量；每周 pacing 告警不超过 3 次。
  - 令牌桶调整：`snapshot per_minute=60`、并发 16；必要时配置槽位分批执行（每批 3-4 个标的）。
  - 文档要求：Runbook 描述批次执行策略、pacing 告警处置；TODO 建立扩容周报。
- **阶段 3：全量 S&P 500**
  - Top 10 阶段连续 2 周稳定运行，`slot_retry_exceeded=0` 且 QA 指标全部达标。
  - 引入调度分组（至少 2 批），在 `state/run_logs/metrics/` 追踪各批延迟与降级比例。
  - 令牌桶起始目标：`snapshot per_minute=90`、并发 20；根据 IBKR pacing 限制动态调节，同时准备延迟槽补采策略。
  - 扩容前在 `PLAN.md`、`TODO.now.md`、Runbook 中记录批准与执行窗口；扩容后首周每日复盘指标与告警。

## 里程碑验收标准
- M1：实时 snapshot 冒烟（AAPL）覆盖 ≥12 个槽，`data_test/.../view=intraday` 生成，槽位去重与字段校验通过，日志/状态可追溯。
- M2：EOD rollup + T+1 OI enrichment 连续 3 日成功运行；daily 视图字段符合契约；回退率低于 5%，QA 报告更新。
- M3：macOS 与 Linux 调度均可自动运行；限速/告警齐备；周度 compaction 生成目标大小文件；延迟行情降级路径验证。
- M4：≥50 标的连续运行一周、槽位覆盖率 ≥90%、无 pacing 违规；文档/Runbook 更新完成，Linux 试运行验收通过。

## 进展快照（2025-11-19 更新）
- 2025-11-18/19 selfcheck 与 logscan 全部 PASS（AAPL），记作 2-day gate 完成，输出位于 `state_test/run_logs/selfcheck/selfcheck_20251118.json`、`selfcheck_20251119.json` 与对应 summary。
- 实现 snapshot 模式设计确认：槽位模型、实时行情默认值、rollup 回退策略、OI enrichment 流程、存储/QA 原则达成共识。
- 现有回填骨架与清洗管道将在 M1 重构为 snapshot + rollup 流程；配置与 CLI 拟新增 `snapshot`/`rollup`/`enrichment` 子命令。
- 测试基线（`make install && make test`）已通过；接下来按新方案更新数据契约、Runbook、配置，并完成单标的冒烟。

## 进展快照（2025-11-26 更新）
- 错误处理健壮性改进完成：统一 snapshot 错误行标记（`snapshot_error`/`error_type`/`error_message`）、修复 rollup 在错误行和缺失列上的崩溃路径，并为 discovery 关键 IB 调用补充重试机制；详见 `docs/dev/error_handling_robustness_fixes.md` 与错误处理验证报告。
- 重试与日志/性能监控基础设施落地：实现通用 `retry_with_backoff`、性能计时与日志上下文工具，并在 `snapshot`、`rollup`、`enrichment` 等关键路径启用；开发文档见 `docs/dev/retry_and_logging_implementation.md` 与 `docs/dev/retry_usage_guide.md`。
- 初步可观测性能力上线：新增基于 SQLite 的指标采集器（`MetricsCollector`）、告警接口（`AlertManager`）与 Streamlit Dashboard（`src/opt_data/dashboard/app.py`），rollup 已开始写入基础运行指标。
- 整理未来改进方向：在 `docs/dev/roadmap.md` 中按短期/中期/长期分类整理后续改进清单，为后续纳入 `PLAN.md`/`TODO.now.md` 提供来源。
- 新增历史 bars 探针需求：计划利用周五 contracts cache 采样少量合约，调用 IB historical API（TRADES/OI）做可行性验证，输出仅限日志/summary。

## 进展快照（2025-12-10 更新）
- Stage 1（AAPL+MSFT）已按 `snapshot per_minute=30`、`max_concurrent_snapshots=14` 配置上线运行，`schedule --simulate` 验证完成，首三日监控完成。
- 最近自检/日志：2025-12-08/09/10 已执行 selfcheck/logscan；2025-12-10 QA 指标达标，日志含 OI 缺失与参考价单条错误，已记录为已知告警。

## 进展快照（2025-12-12 更新）
- 增加远程 IB Gateway OI 脚本：新增 `data_test/OI3_remote.py`（支持 `--host/--port`/环境变量），`data_test/OI3.py` 保留为兼容入口。

## 本周目标（2025-11-03 当周）
- **M1 · 槽位与调度（早收盘感知）**
  - 在 `src/opt_data/util/calendar.py` 增加会话开/收盘获取（优先使用 `pandas-market-calendars`，无依赖则 Mon–Fri 回退）。
  - 更新 `src/opt_data/pipeline/snapshot.py` 的 `_slot_schedule` 以会话收盘裁剪槽位（含 16:00 以外早收盘）。
  - 在 `tests/` 增加早收盘用例，覆盖 `available_slots` 与 `schedule --simulate` 输出。
  - 在 `docs/ops-runbook.md` 补充依赖与早收盘说明。
- **M2 · 调度与验证**
  - 运行 `make fmt lint test`，并使用 `python -m opt_data.cli schedule --simulate --date <早收盘日>` 验证最后一个槽位为真实收盘时刻。
  - 执行一次 AAPL 冒烟（测试目录）：`snapshot` → `rollup` → `enrichment` → `qa/selfcheck`，记录指标文件路径。
- **依赖 & 风险同步**
  - 确认 IB 实时行情权限；若仅延迟权限，验证 `delayed_fallback` 标记链路。
  - 为后续 AAPL→AAPL+MSFT 扩容准备材料（近 2 个交易日 QA/selfcheck 与 `logscan` 摘要）。
