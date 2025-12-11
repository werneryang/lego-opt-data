# 金融数据处理标准

- **宇宙与窗口**: 默认 S&P 500（`config/universe.csv`），09:30–16:00 ET 每 30 分钟槽位（14 槽，±120 秒宽容），17:30 ET close-snapshot → rollup，次日 04:30 ET OI enrichment。调度/时间一律按 `America/New_York`。
- **合约发现（2025 升级）**: 09:25 ET 会话冻结基于前收 ±30% 行权价、标准月/季到期；仅 `reqSecDefOptParams()` + 批量 `qualifyContracts*`，路由强制 `SMART`，禁止 `reqContractDetails`，发现阶段不加应用层限速。采集阶段可按 `fallback_exchanges` 降级。
- **行情采集要求**: 默认 `generic_ticks=100,101,104,105,106,165,221,225,233,293,294,295`，`market_data_type=1`（实时；延迟 3/4 需标记 `delayed_fallback`），`require_greeks` 可配置。OI 日内默认缺失并打 `missing_oi` 标记；日终由 enrichment 补齐。
- **数据层级与布局**: `data/raw` 保留 IB 原样；`data/clean` 清洗/槽位去重；`daily_adjusted` 应用公司行动；`enrichment` 记录慢字段补全。分区键 `date/underlying/exchange/view`，主键 Intraday `(trade_date, sample_time, conid)`、Daily `(trade_date, conid)`。
- **字段与质量**: 必填字段覆盖合约标识、行情、Greeks、路由、时间戳、来源与质量标签；IV ∈ [0,10]、Delta ∈ [-1,1] 等范围校验，延迟/缺失/回退需写入 `data_quality_flag`。日终字段包含 rollup 源槽与公司行动调整（`strike_adj`, `moneyness_pct_adj` 等）。
- **公司行动与参考价**: 调整表本地维护；日终视图按表调整行权价/乘数/收盘价，日内保持原值。参考价优先 IB，外部源需记录来源。
- **存储策略**: Parquet Snappy（热 14 天）/ZSTD（冷），周度合并目标 128–256MB；保留策略 `intraday_retain_days` 默认 60 天，操作记录写入 `state/run_logs/compaction_*`。
- **数据质量与验收**: 槽位覆盖率每日 ≥90%；rollup 回退率、延迟占比、OI 补齐率纳入 QA 报告。错误行保留但标记 `snapshot_error`；`logscan` 汇总关键错误并触发告警。扩容/范围变化需更新 `PLAN.md`、`TODO.now.md` 与相关契约文档。
- **限速现状**: Stage 1 生产运行采用 `snapshot per_minute=30`、`max_concurrent_snapshots=14`；提升至 45/12 需额外评审与监控。
