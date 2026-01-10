# 开发/测试运行手册（data_test）

> 适用范围：本地/沙箱环境的调试与实验脚本（`data_test/*`），不用于生产调度。生产运维请参阅 `docs/ops/ops-runbook.md`。

## 基本约定
- 环境：TWS/Gateway 已启动，默认 `host=127.0.0.1`，`port=4001`，`clientId` 默认按角色池自动分配（prod 0-99，remote 100-199，test 200-250）；如需固定 ID 可在配置或环境变量中显式设置。
- 配置：建议复制 `config/opt-data.toml` 为测试版（如 `config/opt-data.test.toml`），并将数据/状态目录指向 `data_test/`、`state_test/`。
- 行情类型：除特殊说明外，盘后/收盘实验请设 `IB_MARKET_DATA_TYPE=2`（Frozen），盘中/实时请设 `1`。

## 生产/开发设备配置对照表（IB Gateway 连接）

| 场景 | IB_HOST | IB_PORT | IB_CLIENT_ID | 配置位置 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 生产设备（本地 Gateway） | 127.0.0.1 | 4001 | 0-99（prod pool） | `config/opt-data.snapshot.local.toml` / 环境变量 | Gateway 在本机运行 |
| 开发设备（远程 Gateway） | 100.71.7.100 | 4001 | 100-199（remote pool） | `config/opt-data.snapshot.local.toml` / 环境变量 | 直连远端 |
| 开发设备（SSH 转发） | 127.0.0.1 | 4001 | 100-199（remote pool） | `config/opt-data.snapshot.local.toml` / 环境变量 | 通过 SSH 本地端口转发到远端 |

## 常用 data_test 脚本
- AAPL 诊断/快照示例：
  - `python data_test/aapl_delayed_chain_async.py --exchange SMART --strikes 3`
  - `python data_test/aapl_delayed_chain_async.py --exchange SMART`（逐合约抓取，保存 CSV）
  - `python data_test/aapl_delayed_chain_async.py --exchange CBOE`
  - `python data_test/test_from_ib_insync_grok.py`
- 说明：脚本自带通用 generic ticks（含 IV/Greeks/rtVolume），可用于验证权限、路由与就绪度判断逻辑。扩展到 SPX/0DTE 时，请留意 `tradingClass`（SPX/SPXW）与行权价窗口调整。

## MCP 本地只读接口（开发/测试）
- 用途：仅在本地提供只读查询层，不影响生产采集与写入。
- 安装（可选）：先完成仓库根目录 `requirements-dev.lock` 安装，再执行 `pip install -e '.[mcp]'`
- 启动：`python -m opt_data.cli mcp-server --config config/opt-data.test.toml`
- 默认读取：`data/clean`、`data/raw`、`state/run_logs`、`data/metrics.db`
- 审计日志：`state/run_logs/mcp_audit.db`
- 快速验证：`python scripts/mcp_smoke_test.py --config config/opt-data.test.toml`

## SPY 收盘快照批并发实验（reqTickers，实验性）

> 脚本：`data_test/SPY_auto_test_snapshot.py`。仅供评估 Frozen 场景下批级并发的性能上限。生产调度仍使用顺序批模式。

### 场景与合约选择
- 标的：`SPY@SMART`，`IB_MARKET_DATA_TYPE=2`（Frozen）。
- 到期：近端 30 天内所有周五 + 若干远端月/季第三周五（约 15 个到期）。
- 行权价：围绕现价按 5 美元步长取 ±25 档（50 strikes），Call/Put 双边，理论约 1500 合约。
- 过滤：使用 `reqSecDefOptParams` 返回的 `strikes` 白名单，仅对存在的行权价发起请求，减少 “No security definition” 噪音。

### 基线（顺序批，对齐生产）
- 脚本：`data_test/SPY_auto_collect_snapshot.py` → `collect_option_snapshots(mode="reqtickers", batch_size=50)`。
- 特征：30 个批次顺序执行，总耗时约 426s（示例），行级超时出现在少数远端/冷门行权价。

### 实验（批并发 + fallback）
- 参数（环境变量可调）：`BATCH_SIZE=50`、`BATCH_CONCURRENCY=3`、`BATCH_SIZE_FALLBACK=25`、`SNAPSHOT_TIMEOUT=30s`、`IB_MARKET_DATA_TYPE=2`。
- 机制：批级 `Semaphore` 控制并发；批失败时按 25 拆分重试；批/行级统计会在收尾打印。
- 代表性结果（启用 strike 过滤）：约 1492/1500 行，批 30 个，耗时 ~170s，行级 `snapshot_error` 4/1492，批级错误 0。
- 对比基线：耗时缩短至约 40%，错误率未明显恶化。

### 建议与边界
- 仅在测试/沙箱环境使用；生产调度保持顺序批。
- 参数建议（实验区间）：`batch_size ∈ {25,50}`，`batch_concurrency ∈ {1,2,3}`（逐步提升并观察 pacing/超时），`timeout ∈ [30s,45s]`。
- 风险提示：IB 对 snapshot/reqTickers 仍有 pacing 限制；多标的叠加或更高并发需重新评估。若计划推广到生产，需按 ADR 流程决策并完成标的回归。

## 结构迁移（本地/测试最小停机）
详见独立手册：`docs/ops/migration-minimal-downtime.md`。

## 参考
- ADR：`docs/adr/ADR-0002-SPY-snapshot-batch-concurrency.md`（背景、决策与后续行动）。
- 生产运维：`docs/ops/ops-runbook.md`。 

## 开发/调试脚本（手工工具）
- `scripts/debug_parquet.py`：快速检查/打印 parquet 内容，辅助数据问题定位。
- `scripts/verify_dashboard_data.py`：核对观测面板相关数据汇总。
- `scripts/verify_et_time.py`：ET 时间/时区换算验证。
- `scripts/verify_overwrite.py`：验证写入覆盖/幂等行为的简单检查脚本。
