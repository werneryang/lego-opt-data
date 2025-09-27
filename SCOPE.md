# 数据采集范围与约定

## 标的范围
- S&P 500 成分股，标的列表由 `config/universe.csv` 提供，带有 `symbol` 与可选 `conid`。
- 若成分发生调整，以回填批次开始时的名单为准；后续变更需更新此文件并记录于 `PLAN.md`。

## 时间范围
- 回填：自 2024-10-01 起至当前。
- 日常更新：每个美国交易日 17:00 ET（`America/New_York`）触发，补齐当日数据。

## 合约过滤规则
- 到期：标准月度合约（第三个星期五，遇假日顺延）与季度合约（3/6/9/12 月第三个星期五）。
- 行权价：以标的当日收盘价为基准，保留 ±30% 行权价范围内的合约。
- 交易所：保留主要可交易所（CBOE、NASDAQOM、NYSE、BATS 等），默认按数据接口返回。

## 字段要求
- 必须字段：
  - 合约元信息：`conid`, `symbol`, `expiry`, `right`, `strike`, `multiplier`, `exchange`, `tradingClass`。
  - 价格与行情：`bid`, `ask`, `mid`, `last`, `open`, `high`, `low`, `volume`, `open_interest`, `market_data_type`。
  - 波动率与希腊值：`iv`, `delta`, `gamma`, `theta`, `vega`（如可得，保持双精度浮点）。
  - 元数据：`asof_ts`, `source`, `data_quality_flag`（如有缺失或延迟时标记）。
- 可选字段（有则保留）：`rho`, `bid_size`, `ask_size`, `historical_volatility`, `option_implied_volatility` 等。

## 数据层级
- 原始层（Raw）：保持 IB 返回字段命名与类型，不做调整，按请求批次写入。
- 清洗层（Clean）：字段标准化、类型校验、缺失处理、去重；按 `date/underlying/exchange` 分区。
- 调整层（Adjusted）：在 Clean 基础上应用公司行动调整（拆分、特别分红、乘数变化等），额外字段 `underlying_close_adj`, `strike_adj`, `moneyness_pct_adj`。

## 公司行动与参考数据
- 公司行动来源：本地维护表（CSV/Parquet），字段包含 `symbol`, `event_date`, `event_type`, `ratio`, `notes`。
- 调整规则：
  - 拆分：按乘数调整行权价与标的参考价。
  - 现金分红：按配置决定是否对 moneyness 做调整；保持原始价格。
  - 复杂交割（并购、特别交割）需人工确认，无法自动调整时在 `data_quality_flag` 中标记。

## 限速与调度
- 默认限速：按请求类别设定；初始值谨慎（例如历史/快照 20 req/min，发现 5 req/min），可以通过配置调整。
- 调度：macOS 开发期使用 APScheduler 或 `launchd`，正式迁移后使用 Linux `systemd` 定时器。

## 数据质量校验
- Schema 校验：参考 `docs/data-contract.md`。
- 主键唯一：`trade_date + conid`。
- 必填字段：`bid`, `ask`, `last`, `iv`, `open_interest` 至少满足 70% 非空率；不足时记录缺失原因。
- QA 抽样：每批次随机抽 1% 合约核对 greeks/价格合理性。

## 不在范围内
- 非美股期权、指数期权或期货型合约。
- 高频实时推送（逐笔/毫秒级）数据。
- 自动化交易或仓位管理逻辑。
