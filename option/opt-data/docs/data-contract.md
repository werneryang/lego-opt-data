# 数据契约：日内快照与日终视图

## 总览
- **数据视图**：
  - `data/raw/ib/chain/view=intraday`：IB 快照原始字段。
  - `data/clean/ib/chain/view=intraday`：清洗后日内视图（含槽位、降级标记）。
  - `data/clean/ib/chain/view=daily_clean`：按 17:30 ET rollup 的日级快照。
  - `data/clean/ib/chain/view=daily_adjusted`：公司行动调整后的日级视图。
  - `data/clean/ib/chain/view=enrichment`（可选）：T+1 `open_interest` 等慢字段增补记录。
- **分区键**：`date`（交易日，ET）、`underlying`（标的符号）、`exchange`（主要交易所）、`view`。
- **主键**：
  - Intraday：`trade_date(ET) + sample_time(UTC) + conid`。
  - Daily/Adjusted/Enrichment：`trade_date(ET) + conid`。
- **文件格式**：Parquet；热分区 Snappy，冷分区 ZSTD。
- **时间戳**：
  - `asof_ts`：UTC（去时区）；
  - `sample_time`：UTC（槽位中心时间）；可选 `sample_time_et` 记录 ET 文本。

## 字段定义

### 共享字段（intraday & daily）
| 字段名 | 类型 | 描述 | 允许为空 | 备注 |
| --- | --- | --- | --- | --- |
| `trade_date` | `date` | 交易日（ET，去时区） | 否 | 与分区字段 `date` 一致 |
| `underlying` | `string` | 标的符号 | 否 | 大写字母 |
| `conid` | `int64` | IB 合约 ID | 否 | 主键组成部分 |
| `symbol` | `string` | IB 期权代码 | 否 | e.g. `AAPL  240621C00180000` |
| `expiry` | `date` | 合约到期日 | 否 | ISO-8601 |
| `right` | `string` | 权利类型 `C` / `P` | 否 | |
| `strike` | `double` | 行权价 | 否 | |
| `multiplier` | `double` | 合约乘数 | 否 | 通常 100 |
| `exchange` | `string` | IB 交易所/路由 | 否 | 默认 `SMART` |
| `tradingClass` | `string` | IB 交易类别 | 否 | |
| `bid` | `double` | 买价 | 否 | |
| `ask` | `double` | 卖价 | 否 | |
| `mid` | `double` | 中间价 | 是 | `(bid + ask)/2` |
| `last` | `double` | 最新成交价 | 是 | |
| `volume` | `int64` | 当日成交量 | 否 | 若减小则截断为 0 |
| `iv` | `double` | 隐含波动率 | 否 | 校验范围 [0,10] |
| `delta` | `double` | Delta | 否 | |
| `gamma` | `double` | Gamma | 否 | |
| `theta` | `double` | Theta | 否 | |
| `vega` | `double` | Vega | 否 | |
| `rho` | `double` | Rho | 是 | IB 返回则保留 |
| `bid_size` | `int64` | 买量 | 是 | |
| `ask_size` | `int64` | 卖量 | 是 | |
| `hist_volatility` | `double` | 历史波动率 | 是 | 权限依赖 |
| `market_data_type` | `int32` | IB 行情类型 | 否 | 默认 `1`（实时）；降级为 `3/4` 时需标记 |
| `source` | `string` | 数据来源 | 否 | 固定 `IBKR` |
| `asof_ts` | `timestamp[ns]` | 数据采集时间（UTC） | 否 | 精度微秒 |
| `ingest_id` | `string` | 本次采集批次 ID | 否 | UUID |
| `ingest_run_type` | `string` | 运行类型 | 否 | `intraday` / `eod_rollup` / `enrichment` |
| `data_quality_flag` | `list<string>` | 数据质量标签 | 是 | 允许多个，如 `delayed_fallback` |
| `snapshot_error` | `boolean` | 是否发生快照错误 | 是 | 默认为 False；同时也会在 `data_quality_flag` 中出现同名标记以便筛选 |
| `error_type` | `string` | 错误类型 | 是 | 如 `timeout`, `subscription_failed` |
| `error_message` | `string` | 详细错误信息 | 是 | |

### Intraday 专属字段（view=intraday）
| 字段名 | 类型 | 描述 | 允许为空 | 备注 |
| --- | --- | --- | --- | --- |
| `sample_time` | `timestamp[ns]` | 槽位时间（UTC） | 否 | 30 分钟对齐 |
| `sample_time_et` | `string` | 槽位时间（ET 文本） | 是 | 便于审计 |
| `slot_30m` | `int32` | 槽位索引（09:30=0...16:00=13） | 否 | |
| `first_seen_slot` | `int32` | 合约当日首次出现槽 | 是 | 启用增量刷新时返回 |
| `open_interest` | `int64` | 持仓量 | 是 | 日内默认空，若返回则记录 |
| `delayed_quote_age_sec` | `double` | 延迟行情滞后（秒） | 是 | 仅在降级时填充 |

### 日终字段（view=daily_clean / daily_adjusted）
| 字段名 | 类型 | 描述 | 允许为空 | 备注 |
| --- | --- | --- | --- | --- |
| `rollup_source_time` | `timestamp[ns]` | 使用的快照时间（UTC） | 否 | 优先 16:00 槽 |
| `rollup_source_slot` | `int32` | 来源槽位 | 否 | |
| `rollup_strategy` | `string` | 选取策略 | 否 | `close` / `last_good` / `slot_1530` |
| `underlying_close` | `double` | 标的当日收盘价 | 否 | 可来自 IB 或外部行情 |
| `underlying_close_adj` | `double` | 公司行动调整后收盘价 | 是 | |
| `strike_adj` | `double` | 调整后行权价 | 是 | |
| `strike_per_100` | `double` | 行权价折算（每 100 股） | 是 | `strike * (100/multiplier)` |
| `moneyness_pct` | `double` | `(underlying_close/strike - 1)` | 否 | |
| `moneyness_pct_adj` | `double` | 调整后 moneyness | 是 | |
| `open_interest` | `int64` | 持仓量（EOD/T+1） | 是 | enrichment 后补齐 |
| `oi_asof_date` | `date` | OI 对应日期 | 是 | enrichment 时写入 |
| `derived_mid_high` | `double` | 采样 mid 最高值 | 是 | 默认不生成，启用时附 `derived_from_intraday_samples` 标记 |
| `derived_mid_low` | `double` | 采样 mid 最低值 | 是 | 同上 |
| `derived_mid_vwap` | `double` | 采样 mid 近似 VWAP | 是 | 启用后需槽位覆盖 ≥80% |

### Enrichment 视图（可选）
| 字段名 | 类型 | 描述 | 允许为空 | 备注 |
| --- | --- | --- | --- | --- |
| `update_ts` | `timestamp[ns]` | 回补执行时间（UTC） | 否 | |
| `fields_updated` | `list<string>` | 本次回补字段 | 否 | 例如 `["open_interest"]` |

## 质量校验
- **主键唯一**：Intraday `(trade_date, sample_time, conid)`；Daily `(trade_date, conid)`；冲突时以最新 `asof_ts` 覆盖旧值。
- **槽位覆盖**：每标的每日成功槽位数 ≥ 90%；不足时记录 `slot_coverage_breach` 并在 QA 报告中说明。
- **行情质量**：
  - 实时降级：`market_data_type` 非 1 时必须存在 `delayed_fallback` 标记。
  - `open_interest` 缺失：日内默认 `missing_oi`，日终在 enrichment 完成前维持标记。
- **数值范围**：
  - `iv` ∈ [0,10]；超界写入 `iv_out_of_range`。
  - `delta` ∈ [-1,1]；`gamma`、`theta`、`vega` 按业务规则校验。
- **派生指标**：`derived_*` 字段默认不写；启用时需 `derived_from_intraday_samples` 标记并校验槽位覆盖率 ≥ 80%，否则置空并记录 `derived_incomplete`。

## 兼容性与演进
- 新增字段需在此处登记，并在 `SCOPE.md`、`config/opt-data.toml`（或模板）保持同步；默认对缺失字段赋空值，不中断流程。
- 调整分区或视图命名需同步更新 `docs/ADR-0001-storage.md`、`SCOPE.md`、`PLAN.md`。
- `ingest_run_type` 取值规范：
  - `intraday`：30 分钟快照；
  - `eod_rollup`：17:30 日终归档；
  - `enrichment`：次日慢字段回补；
  - 后续新增任务需扩展列表并更新契约。
