# 数据契约：清洗与调整层 Schema

## 总览
- **数据视图**：`data/raw/ib/chain`（原始）、`data/clean/ib/chain/view=clean`（标准化）、`view=adjusted`（公司行动调整）。
- **分区键**：`date`（交易日）、`underlying`（标的符号）、`exchange`（主要交易所）。
- **主键**：`trade_date + conid`。
- **文件格式**：Parquet（Snappy for hot partitions, ZSTD for cold partitions）。
- **时间戳**：`asof_ts` 统一转为 UTC 并去除时区信息。

## 字段定义
| 字段名 | 类型 | 描述 | 允许为空 | 备注 |
| --- | --- | --- | --- | --- |
| `trade_date` | `timestamp[ns]` | 交易日（ET，00:00） | 否 | 与分区字段 `date` 一致 |
| `asof_ts` | `timestamp[ns]` | 数据采集时间（UTC，去时区） | 否 | 精度微秒 |
| `underlying` | `string` | 标的符号 | 否 | 大写字母 |
| `underlying_close` | `double` | 标的当日收盘价 | 否 | 来自 IB 或外部行情 |
| `underlying_close_adj` | `double` | 公司行动调整后的收盘价 | 是 | 无调整时等于 `underlying_close` |
| `conid` | `int64` | IB 合约 ID | 否 | 主键之一 |
| `symbol` | `string` | IB 返回的期权代码 | 否 | e.g. `AAPL  240621C00180000` |
| `expiry` | `date` | 合约到期日 | 否 | ISO-8601 |
| `right` | `string` | `C` 或 `P` | 否 | |
| `strike` | `double` | 原始行权价 | 否 | |
| `strike_adj` | `double` | 调整后行权价 | 是 | 参考乘数/拆分 |
| `strike_per_100` | `double` | 行权价换算到每 100 股 | 是 | `strike * (100/multiplier)` |
| `multiplier` | `double` | 合约乘数 | 否 | 通常 100 |
| `exchange` | `string` | 交易所 | 否 | 与分区字段一致 |
| `tradingClass` | `string` | IB 交易类别 | 否 | |
| `bid` | `double` | 买价 | 否 | |
| `ask` | `double` | 卖价 | 否 | |
| `mid` | `double` | 中间价 | 是 | `(bid + ask)/2` |
| `last` | `double` | 最新成交价 | 是 | |
| `open` | `double` | 开盘价 | 是 | 若缺失保持空值 |
| `high` | `double` | 最高价 | 是 | |
| `low` | `double` | 最低价 | 是 | |
| `volume` | `int64` | 成交量 | 否 | |
| `open_interest` | `int64` | 持仓量 | 否 | 若缺失需在 QA 中标记 |
| `iv` | `double` | 隐含波动率 | 否 | 0-10 之间应在 QA 校验 |
| `delta` | `double` | Delta | 否 | |
| `gamma` | `double` | Gamma | 否 | |
| `theta` | `double` | Theta | 否 | |
| `vega` | `double` | Vega | 否 | |
| `rho` | `double` | Rho | 是 | IB 返回则保留 |
| `bid_size` | `int64` | 买量 | 是 | |
| `ask_size` | `int64` | 卖量 | 是 | |
| `hist_volatility` | `double` | 历史波动率 | 是 | 依赖权限 |
| `market_data_type` | `int32` | IB 行情类型 | 否 | 参考 IB API 文档 |
| `moneyness_pct` | `double` | `(underlying_close/strike - 1)` | 否 | |
| `moneyness_pct_adj` | `double` | 调整后 moneyness | 是 | |
| `data_quality_flag` | `string` | 数据质量标签 | 是 | e.g. `missing_oi`, `delayed` |
| `source` | `string` | 数据来源 | 否 | 固定 `IBKR` |
| `ingest_id` | `string` | 本次采集批次 ID | 否 | UUID |
| `ingest_run_type` | `string` | `backfill` 或 `daily` | 否 | |

## 质量校验
- 主键冲突：同一 `(trade_date, conid)` 只允许一行；冲突时保留最新 `asof_ts` 数据。
- 数值范围：
  - `iv` 在 0–10 之间，超界需记录 `data_quality_flag`。
  - `delta` ∈ [-1, 1]；`gamma`、`vega`、`theta` 等按金融常识校验。
- 空值策略：
  - 必填字段空值时，视为采集失败；在 `state/run_logs/` 中记录并标记。
  - 可选字段保留空值，避免误填默认值。

## 兼容性要求
- 添加新字段需在此处更新并保证向后兼容；清洗流程需默认为缺失字段赋空值而非报错。
- 任何分区规则调整需同步更新 `docs/ADR-0001-storage.md`、`SCOPE.md`、`config/opt-data.toml`。
