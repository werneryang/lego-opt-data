# 数据采集范围与约定

## 标的范围
- 默认宇宙：S&P 500 成分股（可通过 `config/universe.csv` 缩减或扩展），包含 `symbol` 与可选 `conid`。
- 成分调整或扩容需更新 `config/universe.csv` 并在 `PLAN.md`、`TODO.now.md` 留痕；上线前建议按 AAPL → AAPL,MSFT → Top 10 → 全量的节奏逐步放量。

## 时间范围与采样频率
- 日内采集：美国交易日 09:30–16:00（America/New_York），每 30 分钟一个槽位，共 14 槽，包含 16:00 收盘槽；早收盘按交易日历截断。
- 槽位时间按 ET 定义，存储时 `sample_time` 使用 UTC，另存 `slot_30m`（0–13）；单槽允许 ±120 秒宽限并重试。
- 日终归档：当日 17:00 ET 运行 rollup，优先使用 16:00 槽快照（回退规则详见下文）；不再执行历史回填。
- T+1 补全：次日 07:30 ET（可配置）执行 `open_interest` enrichment。

## 合约发现与过滤规则
- 会话冻结：每日 09:25 ET 基于上一交易日收盘价的 ±30% 行权价范围及标准月度/季度到期合约生成目标集合，默认整日固定；可选单次中午（12:00 ET）增量刷新，仅新增不删除。
- 行权价过滤：以会话基准价（默认前收）计算；可通过配置启用“动态跟随标的价格”策略。
- 交易所：默认使用 IB `SMART` 路由；若返回具体交易所名称则保留该值。
- 其他筛选：`max_strikes_per_expiry`、`exclude_weekly=true` 等可在配置中调整。

## 字段要求
- 必填字段（intraday/daily 通用）：`conid`, `symbol`, `expiry`, `right`, `strike`, `multiplier`, `exchange`, `tradingClass`, `bid`, `ask`, `mid`, `last`, `volume`, `iv`, `delta`, `gamma`, `theta`, `vega`, `market_data_type`, `asof_ts`, `sample_time`, `slot_30m`, `source`, `ingest_id`, `ingest_run_type`, `data_quality_flag`（可为空列表）。
- 日终额外字段：`rollup_source_time`, `rollup_source_slot`, `rollup_strategy`, `underlying_close`, `underlying_close_adj`, `strike_adj`, `moneyness_pct`, `moneyness_pct_adj`。
- 可选字段（有则保留）：`rho`, `bid_size`, `ask_size`, `hist_volatility`, `sample_time_et`, `first_seen_slot`, 以及公司行动维度。
- `open_interest`：视为 EOD/T+1 字段；intraday 默认空值并加 `missing_oi` 标记；日终在 enrichment 完成后补齐。
- 若实时行情降级为延迟（`market_data_type=3/4`），需在 `data_quality_flag` 中记录 `delayed_fallback`。

## 数据层级
- 原始层（Raw）：记录 IB 快照原样字段及槽位信息，按 `date/underlying/exchange/view=intraday` 分区；保留 `market_data_type` 与任何错误码。
- 清洗层（Clean）：标准化字段类型、落槽去重、填充缺失标记；包含 `view=intraday` 与 `view=daily_clean`。
- 调整层（Adjusted）：在 daily_clean 基础上应用公司行动调整（拆分、特别分红、乘数变化等），输出 `view=daily_adjusted`。
- 附加层：`view=enrichment` 可选记录 T+1 OI 回填及其他慢字段。

## 公司行动与参考数据
- 来源：本地维护的公司行动表（CSV/Parquet），字段包含 `symbol`, `event_date`, `event_type`, `ratio`, `notes`。
- 生效策略：
  - 日内视图保持原始价格与行权价，不做调整。
  - 日终 rollup 与 adjusted 层按公司行动表应用调整（拆分/乘数变更/特别分红），未匹配到规则时保留原值并记录说明。
- 参考数据（如标的收盘价）优先使用 IB 数据，必要时引入外部源并在文档中记录。

## 限速与调度
- 限速默认值：snapshot 30 req/min，合约发现 5 req/min，可通过配置调节；并发 `max_concurrent_snapshots=10` 起步，逐步调优。
- 调度：开发机使用 APScheduler/launchd，生产使用 systemd timer；统一设置时区 `America/New_York`，维护交易日历及早收盘表。
- 失败重试：槽位请求失败即时重试（指数退避），超过阈值记录 `slot_retry_exceeded` 并进入人工处理队列。

## 数据质量校验
- Intraday 主键：`(trade_date(ET), sample_time(UTC), conid)`；Daily 主键：`(trade_date(ET), conid)`。
- 槽位覆盖：每标的每日≥90% 槽成功；不足时标记并在 QA 报告中说明。
- 数值范围：IV ∈ [0,10]；Greeks 按金融常识校验；异常写入 `data_quality_flag`。
- 延迟标识：`delayed_fallback`、`missing_greeks`、`eod_rollup_fallback`、`eod_rollup_stale` 等需在清洗层记录。
- QA 抽样：每日随机抽 1% 合约检查快照一致性与 rollup 策略正确性。

## 不在范围内
- 非美股股票期权、指数期权、期货期权等其他衍生品。
- 实时逐笔/毫秒级行情、自动交易信号与仓位管理。
- 历史大规模回填或外部数据源混合（除非在 PLAN/ADR 中重新批准）。
