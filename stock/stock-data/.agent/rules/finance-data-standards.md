# 金融数据处理标准 (股票数据)

- **宇宙与窗口**: 默认 Universe 定义在 `config/stock-universe.csv`。交易时段 09:30–16:00 ET。调度/时间一律遵循 `America/New_York` 时区。
- **行情采集要求**: 优先使用 `market_data_type=1` (实盘)。如果使用延迟数据，必须记录 `delayed_fallback` 标记。
- **数据层级与布局**:
    - `data/raw`: 原始 API 响应。
    - `data/clean`: 清洗后的规范化数据。
    - 分区键: `date/symbol/exchange/view` (view 可选 `intraday`, `daily`)。
- **数据质量**: 
    - 检查买卖价差 (Spread) 是否合理。
    - 记录数据采集过程中的限速 (Pacing) 或连接异常。
- **存储策略**: Parquet 格式，Snappy 压缩。冷数据使用 ZSTD。
- **公司行动**: 针对拆分 (Splits) 和股息 (Dividends) 的调整逻辑需在 `pipelines` 中明确定义，并在 `daily_adjusted` 视图中体现。
