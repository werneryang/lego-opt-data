# 运维与采集补充说明（开发/诊断）

> 本文用于开发/诊断与后续优化记录；生产调度与日常值班入口以 `docs/ops-runbook.md` 为准。

## IBKR 期权链拉取最佳实践（AAPL/SPX）

以下经验来自 AAPL/SMART 成功拿到期权链报价与 Greeks 的实测，供采集器与内部诊断脚本参考。

### 核心配置
- 端口与会话
  - TWS：默认使用 `7497`；IB Gateway 常见为 `4002=Paper`、`4001=Live`（以本机设置为准）。
  - 连接后以账户号快速自检：`DU*` 多为纸盘，`U*` 多为实盘。
- 行情类型优先级
  - `marketDataType=1`（实时）优先；若无实时权限会自动回退到延迟（3/4）。
- 必要订阅勾子（generic ticks）
  - 期权建议包含：`100,101,104,105,106,165,221,225,233,293,294,295`。
  - 其中 `100`（OptionComputation）对模型 IV/Greeks 关键；`233` 提供 `rtVolume`。
- 交易所选择
  - 默认 `SMART`；无报价/权限差异时可尝试 `CBOE` / `CBOEOPT`。

### 订约与订阅流程（2025 升级）
- 标的资格化：`Stock('AAPL','SMART','USD')` 并 `ib.qualifyContracts(...)`。
- 期权链发现：
  - 使用 `reqSecDefOptParams(exchange='SMART')` 获取 expirations/strikes；
  - 行权价围绕现价取最近 N 个（常用 2–5）或按窗口过滤（如 ±$15）；
  - 批量构造 `Option(...)` 后用 `qualifyContracts/qualifyContractsAsync` 获取 `conId`；
  - 不使用 `reqContractDetails`。
- 逐合约订阅（更稳）：
  - `reqMktData(option, genericTickList=..., snapshot=False)`；
  - 等“就绪”后立刻 `cancelMktData`，降低 pacing 压力；
  - “就绪”建议：有任一价格字段（bid/ask/last/close）且非 NaN，且 Greeks/IV 非 NaN（优先读 `ticker.modelGreeks`）。

### 就绪判定与容错
- 过滤无效 IV：`None/-1/0/NaN` 视为未就绪；无 `ticker.impliedVolatility` 时回退 `ticker.modelGreeks.impliedVol`。
- mid 价仅在 bid/ask 均有效时计算；否则留空。
- 对批量模式允许部分合约失败，不以“就绪率门槛”阻断全量输出。

### 并发与限速
- 遵守 IBKR pacing（消息/秒、订阅总量）；实测更稳的是“逐合约顺序订阅 + 采样即取消”。
- 若必须并发：用信号量限制并发（如 20–40），批间休眠 ≥1s，对超时做降级处理。

### 常见问题排查
- `marketDataType` 显示 1 而脚本设置为 3/4：账户有实时权限被自动提升，属正常。
- 始终无 bid/ask：缺少期权顶级行情或非交易时段；尝试切换 `CBOE/CBOEOPT`，或仅依赖模型 Greeks。
- DataFrame 为空：检查 entitlement、交易时段、generic ticks、是否取消过早、tradingClass（如 SPX vs SPXW）。
- 端口不通：确认 TWS/Gateway API 设置、Socket Port、`Read Only API`、`clientId` 冲突。

## OI Enrichment 优化路线图

当前 OI enrichment 以 tick-101 为主、必要时降级 historical（受 IBKR 规则限制）。以下为分阶段优化建议（仅开发侧规划，非生产承诺）：

### 立即可做
1. OI 来源记录：在 enrichment 结果中记录来源（`tick101` / `historical`），便于统计成功率分布。
2. 配置化参数：将 OI 相关超时与 duration 提取到 `config/opt-data.toml` 的 `[enrichment]` 配置段，便于不同环境调参。

### 短期优化（1–2 周）
3. 运行观测：收集一周 enrichment 日志，分析 tick-101 成功率、historical fallback 触发频率、长期失败 conId 列表（必要时标记跳过）。
4. 文档明确：区分 `opt_data.cli enrichment`（生产）与 `data_test/*` 验证脚本（本地诊断）。

### 中期增强（按需）
5. 有限并发：在内部按批次处理（例如 5–10 合约/批），仍受 TokenBucket 控制，避免完全串行。
6. 智能重试：区分 IB 420/321 等错误，对 pacing 做有限次指数退避重试。

### 观望
7. 完全异步化：仅在高并发必要时重构 pipeline 为 async。
8. 第三层 fallback：若 IBKR 废弃 `OPTION_OPEN_INTEREST` bars，评估其他保底字段/路径。

