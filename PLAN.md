# 4 周项目计划

## 背景
本项目聚焦 S&P 500（可配置）标的的期权链日内采集与日终归档：在交易日 09:30–16:00（America/New_York）每 30 分钟记录一次实时快照，17:00 ET 聚合为日级视图（含回退规则），并维护清洗/调整层数据。目标是在 macOS 环境验证后迁移到 Linux 定时执行，确保快照与日终数据可恢复、可审计，且不再执行历史回填。

## 范围与里程碑
- **M1（第 1 周）**：落地实时 snapshot 采集骨架（`acquisition.mode=snapshot`，`IB_MARKET_DATA_TYPE=1`），完成 09:25 ET 会话合约发现与冻结策略、槽位计算（含 16:00 槽宽限）、单标的冒烟（AAPL）并写入 `view=intraday` 数据。
- **M2（第 2 周）**：实现 17:00 ET EOD rollup（收盘快照优先、回退策略、公司行动调整）、T+1 `open_interest` enrichment、数据契约与 QA 指标更新（slot 覆盖率、回退率、IV/Greeks 合规）。
- **M3（第 3 周）**：完善调度与运维（APScheduler/launchd/systemd）、实时限速与退避、监控告警、日志与状态记录；周度 compaction 支持 intraday+daily 视图；加入延迟行情降级与标记。
- **M4（第 4 周）**：扩容至多标的（≥50）并评估限速调优，完善文档（Runbook、数据契约、配置模板、渐进扩容指南）、Linux 环境试运行与验收。

## 关键任务拆解
- **槽位与调度**：定义 14 个 30 分钟槽（含 16:00），处理夏/冬令时与早收盘，ET 调度、UTC 存储、宽限窗口重试。
- **合约发现策略**：09:25 ET 冻结一日合约集合（基于前收 ±30%、标准月/季到期），支持单次中午增量刷新（默认关闭）。
- **实时采集管道**：使用 `ib_insync` `reqMktData` 拉取实时快照，记录 `sample_time`/`slot_30m`，保存 `market_data_type` 与降级标记，按槽幂等写入 `data/raw|clean/ib/chain/view=intraday`。
- **日终归档**：17:00 rollup 按策略选取快照，补写 `rollup_source_*`、公司行动调整，产出 `view=daily_clean|daily_adjusted` 并处理幂等覆盖。
- **延迟字段补全**：维护次日 07:30 ET `open_interest` enrichment 任务，按 `(trade_date, conid)` 幂等更新日级数据。
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
- 不执行历史回填；仅维护 09:30–16:00 30 分钟快照与 17:00 日终 rollup。
- 默认宇宙为 S&P 500，可通过 `config/universe.csv` 缩减或扩展；上线前分批扩容。
- 初期仅覆盖本地/macOS 环境与指定 Linux 主机；不包含云端部署。

## 风险与缓解
- **实时行情权限不足**：提供延迟行情降级（自动/手动）、记录 `delayed_fallback` 标记，并在 Runbook 中列出申请/排查步骤。
- **槽位缺失或回退频繁**：配置宽限重试、slot 覆盖率监控；连续缺槽触发告警并支持补采。
- **Greeks/字段缺失**：记录 `missing_greeks` 等标记；QA 抽样确保核心字段合理。
- **open_interest 延迟**：次日 enrichment 异常时标记 `missing_oi` 并保持追踪；超过 SLA 进入人工处理。
- **限速与并发**：初始令牌桶保守（30 req/min），观察 pacing violation；必要时调低并发或拆分宇宙。
- **存储膨胀**：周度 compaction + 60 天 intraday 保留策略，磁盘占用阈值监控。
- **调度失败**：提供 launchd/systemd runbook、状态文件断点续跑与手动补采指南。

## 里程碑验收标准
- M1：实时 snapshot 冒烟（AAPL）覆盖 ≥12 个槽，`data_test/.../view=intraday` 生成，槽位去重与字段校验通过，日志/状态可追溯。
- M2：EOD rollup + T+1 OI enrichment 连续 3 日成功运行；daily 视图字段符合契约；回退率低于 5%，QA 报告更新。
- M3：macOS 与 Linux 调度均可自动运行；限速/告警齐备；周度 compaction 生成目标大小文件；延迟行情降级路径验证。
- M4：≥50 标的连续运行一周、槽位覆盖率 ≥90%、无 pacing 违规；文档/Runbook 更新完成，Linux 试运行验收通过。

## 进展快照（2025-09-26）
- 实现 snapshot 模式设计确认：槽位模型、实时行情默认值、rollup 回退策略、OI enrichment 流程、存储/QA 原则达成共识。
- 现有回填骨架与清洗管道将在 M1 重构为 snapshot + rollup 流程；配置与 CLI 拟新增 `snapshot`/`rollup`/`enrichment` 子命令。
- 测试基线（`make install && make test`）已通过；接下来按新方案更新数据契约、Runbook、配置，并完成单标的冒烟。

## 本周目标（2025-09-29 当周）
- **M1 · snapshot 骨架与冒烟**
  - 更新配置与 CLI：默认 `mode=snapshot`、`market_data_type=1`，新增 `slot_30m` 计算与 per-slot 幂等写入。
  - 在 `data_test/`、`state_test/` 环境对 AAPL 执行完整交易日模拟：生成 ≥12 个槽；验证 `sample_time`（UTC）与 `slot_30m` 正确。
  - 校验延迟行情降级逻辑：无权限时降级到 `market_data_type=3` 并加 `delayed_fallback` 标记。
  - 在 `docs/` 与 `SCOPE.md` 对齐设计，审阅数据契约与 Runbook 更新。
- **M2 · EOD rollup 预研**
  - 原型实现 `rollup` 命令：16:00 槽优先、回退策略、`rollup_source_*` 元数据写入。
  - 设计次日 07:30 OI enrichment 流程，确认 `(trade_date, conid)` 幂等更新方式。
- **依赖 & 风险同步**
  - 实时行情 entitlement 与 pacing 限制需线下确认；若持续受阻，评估降级到延迟行情 + 标记策略。
  - 逐步扩容计划（AAPL → AAPL,MSFT → Top 10）待槽位稳定后执行；相关限速调参在 Runbook 留痕。
