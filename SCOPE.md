# 数据采集范围与约定

## 标的范围
- 默认宇宙：S&P 500 成分股（可通过 `config/universe.csv` 缩减或扩展），包含 `symbol` 与可选 `conid`。
- 成分调整或扩容需更新 `config/universe.csv` 并在 `PLAN.md`、`TODO.now.md` 留痕；上线前建议按 AAPL → AAPL,MSFT → Top 10 → 全量的节奏逐步放量。

## 时间范围与采样频率
- 日内采集：美国交易日 09:30–16:00（America/New_York），每 30 分钟一个槽位，共 14 槽，包含 16:00 收盘槽；早收盘按交易日历截断。
- 槽位时间按 ET 定义，存储时 `sample_time` 使用 UTC，另存 `slot_30m`（0–13）；单槽允许 ±120 秒宽限并重试。
- 日终归档：当日 17:00 ET 运行 rollup，优先使用 16:00 槽快照（回退规则详见下文）；不再执行历史回填。
- T+1 补全：次日 07:30 ET（可配置）执行 `open_interest` enrichment。

## 合约发现与过滤规则（2025 升级）
- 会话冻结：每日 09:25 ET 基于上一交易日收盘价的 ±30% 行权价范围及标准月度/季度到期合约生成目标集合，默认整日固定；可选单次中午（12:00 ET）增量刷新，仅新增不删除。
- 行权价过滤：以会话基准价（默认前收）计算；可通过配置启用“动态跟随标的价格”策略。
- 交易所（发现阶段）：只使用 `SMART`。从 `reqSecDefOptParams()` 返回的多 venue 参数中筛选到 `SMART`，其余 venue 不参与“发现”。如需在采集阶段尝试备选 venue（如 `CBOE`/`CBOEOPT`），在快照订阅阶段由降级逻辑处理。
- 发现实现（IB API v10.26+）：
  - 使用 `reqSecDefOptParams()` 获取全量 `expirations` 与 `strikes`（SMART 路由）。
  - 直接构造 `Option(symbol, expiryYYYYMMDD, strike, right, exchange='SMART')` 合约集合。
  - 采用批量 `qualifyContracts`/`qualifyContractsAsync` 一次性补齐 `conId` 等核心字段。
  - 不再在发现阶段调用 `reqContractDetails`。
- 其他筛选：`max_strikes_per_expiry`、`exclude_weekly=true` 等可在配置中调整。

## 字段要求
- 必填字段（intraday/daily 通用）：`conid`, `symbol`, `expiry`, `right`, `strike`, `multiplier`, `exchange`, `tradingClass`, `bid`, `ask`, `mid`, `last`, `volume`, `iv`, `delta`, `gamma`, `theta`, `vega`, `market_data_type`, `asof_ts`, `sample_time`, `slot_30m`, `source`, `ingest_id`, `ingest_run_type`, `data_quality_flag`（可为空列表）。
- 日终额外字段：`rollup_source_time`, `rollup_source_slot`, `rollup_strategy`, `underlying_close`, `underlying_close_adj`, `strike_adj`, `moneyness_pct`, `moneyness_pct_adj`。
- 可选字段（有则保留）：`rho`, `bid_size`, `ask_size`, `hist_volatility`, `sample_time_et`, `first_seen_slot`, 以及公司行动维度。
- `open_interest`：视为 EOD/T+1 字段；intraday 默认空值并加 `missing_oi` 标记；日终在 enrichment 完成后补齐。T+1 回补优先通过 `reqMktData` + generic tick `101`（读取 `callOpenInterest`/`putOpenInterest` 或 `openInterest`）获取上一交易日收盘 OI；如未来启用 `OPTION_OPEN_INTEREST` 历史权限，可作为备选校验源。
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
- 限速默认值：snapshot 30 req/min；发现阶段（`qualifyContracts*` 批量）不再额外施加应用层限速，采用批量资格化（建议每批 25–50 个）并遵循 IB pacing（如出现 pacing 告警再行调优）。并发 `max_concurrent_snapshots=10` 起步，逐步调优。
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

## 期权链拉取简要清单（优先实践）
- SDK 选择：全局采用 `ib_insync`；不直接使用 `ibapi` 原生接口。
- 行情类型：优先 `marketDataType=1`（实时）；无实时权限时允许回退 3/4。
- Generic ticks（必选）：`100,101,104,105,106,165,221,225,233,293,294,295`，其中 `100` 提供模型 IV/Greeks，`233` 为实时成交量。
- 交易所：默认 `SMART`；若长时间无报价，尝试 `CBOE`/`CBOEOPT` 并重新资格化。
- 到期与行权价：选最近到期 `near_exp`；围绕现价选择最近 N 个行权价（建议 2–5）。
- 订阅策略：逐合约 `reqMktData(snapshot=False)` 并传入上面的 ticks；单个合约就绪后立刻 `cancelMktData`，降低 pacing 压力。
- 就绪判定：需同时满足“至少一个价格字段非 NaN”与“模型 IV/Greeks 非 NaN”（优先从 `ticker.modelGreeks` 读取）。
- 字段采集：`bid/ask/mid`、解析 `rtVolume`、`modelGreeks.{impliedVol,delta,gamma,theta,vega,optPrice,undPrice}`、`marketDataType`、`time`。
- 并发与限速：顺序最稳；如并发，使用信号量限 20–40，批间休眠 ≥1s，并对异常/超时降级。
- 常见问题：
  - `MarketDataType=1` 即实时被自动提升（即使设置 3/4）。
  - 无 bid/ask 多为权限或时段问题；可仅依赖模型 Greeks 或切换交易所。
  - DataFrame 为空：检查 entitlement、generic ticks 是否传入、交易所与 tradingClass 是否正确。

参考：详见 docs/ops-runbook.md 中“IBKR 期权链拉取最佳实践（AAPL/SPX）”。
