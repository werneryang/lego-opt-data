# 运维手册：30 分钟快照与日终归档

> 本手册面向**生产环境运维与调度**：描述 `opt_data.cli` 相关命令在正式配置上的使用方式与故障排查流程。开发/测试脚本（`data_test/*`）与实验性配置请参阅 `docs/dev/ops-runbook-dev.md`。

## 运行前准备
1. 启动 IB Gateway/TWS（默认：`127.0.0.1:7497`），确认登录账号具备美股期权**实时行情**权限；若仅有延迟权限，允许自动降级。
2. 推荐使用项目专用虚拟环境（避免污染 base Conda 并触发 NumPy 升级冲突）：
   - venv 路径：`python3.11 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -e '.[dev]'`
   - 或 Conda 隔离：`conda create -n opt-data python=3.11 && conda activate opt-data && pip install -e '.[dev]'`
   - 也可运行 `make install`（确保 `python3` 指向 3.11）。
3. 依赖与 SDK 规范：
   - 统一使用 `ib_insync` 作为 IBKR Python 接入层；项目不直接使用 `ibapi` 原生包。
   - 安装：`pip install -e .[dev]` 已包含 `ib-insync`；无需额外安装 `ibapi`。
4. Snapshot 配置与合约发现（2025 升级）：
   - 发现阶段（Discovery）：使用 `reqSecDefOptParams()` + 批量 `qualifyContracts/qualifyContractsAsync`（仅 `SMART`）。不再调用 `reqContractDetails`；不对发现阶段施加应用层限流，采用批量（建议每批 25–50 个）资格化并遵循 IB pacing。
   - 采集阶段（Snapshot）：`exchange` / `fallback_exchanges` 为订阅首选与备用路由（默认 `SMART`，必要时回退 `CBOE`,`CBOEOPT`）。
   - `generic_ticks`：默认 `100,101,104,105,106,165,221,225,233,293,294,295`，务必覆盖 IV、Greeks、rtVolume。
   - `strikes_per_side`：围绕现价采样的行权价数（每侧 N 个）。
   - `subscription_timeout_sec` / `subscription_poll_interval`：单合约订阅超时与轮询间隔。
   - `require_greeks`：是否强制等待模型 Greeks；延迟/无权限时可设为 `false`。
   - CLI 可临时覆盖：`python -m opt_data.cli snapshot --exchange CBOE --fallback-exchanges CBOEOPT --strikes 2 --ticks 100,233 --timeout 15 --poll-interval 0.5`。
5. 配置 `.env` / 环境变量：
   - `IB_HOST`（默认 `127.0.0.1`）
   - `IB_PORT`（默认 `7497`）
   - `IB_CLIENT_ID`（默认 `101`）
   - `IB_MARKET_DATA_TYPE=1`（盘中默认实时；如需强制延迟改为 `3/4`）
   - **收盘快照**：运行前将 `IB_MARKET_DATA_TYPE=2`（盘后/回放模式），命令内部也会强制 `reqMarketDataType(2)` 以读取当日收盘数据
   - `TZ=America/New_York`（统一调度时区）
6. 配置文件准备：
   - **本地/生产配置**：`cp config/opt-data.toml config/opt-data.local.toml`，在此文件中修改本地特定配置（如端口、路径），该文件已加入 `.gitignore`。
   - **测试配置**：`cp config/opt-data.toml config/opt-data.test.toml`，并将 `paths.raw/clean/state/contracts_cache/run_logs` 指向 `data_test/`、`state_test/`。
7. 核对核心配置：
   - `[acquisition] mode="snapshot"`、`market_data_type=1`（默认实时，enrichment 必需）、`allow_fallback_to_delayed=true`
   - `slot_grace_seconds=120`、`rate_limits.snapshot.per_minute=30`、`max_concurrent_snapshots=10`
   - `[discovery] policy="session_freeze"`、`pre_open_time="09:25"`；若启用增量刷新，设 `midday_refresh_enabled=true` 且仅新增合约，并依赖已存在的当日缓存（不刷新/重建已有合约，发现缺失需先修复缓存再开启增量）
   - `intraday_retain_days=60`、`weekly_compaction_enabled=true`、`same_day_compaction_enabled=false`
8. 确认交易日历（含早收盘）可用；调度器/cron 中必须显式设置 `America/New_York`。项目使用 `pandas-market-calendars` 获取 XNYS 会话时间：若运行环境缺少该依赖或无法访问历年日历，将自动回退到固定 09:30–16:00 槽位，并在日志标记 `early_close=False`。
9. **合约缓存预检与自动重建（新）**  
   - `python -m opt_data.cli schedule` 在启动时会对本次运行的所有 symbols 预检 `paths.contracts_cache/<SYM>_<trade_date>.json`。  
   - 缺失/空/损坏时会用 IBSession 拉取标的收盘价，再调用 `discover_contracts_for_symbol` 重建缓存；重建失败将直接终止，不会跳过或继续运行。  
   - 如需强制严格模式（不自动重建），使用 `--fail-on-missing-cache`；默认自动重建以避免半程才发现缓存缺失。  
   - 若 `config/universe.csv` 未填写 conid，预检阶段会自动尝试资格化标的以获取标准 conid（Stock@SMART，常见指数如 SPX/NDX/VIX 还会尝试 `Index@CBOE`）；成功后用该 conid 获取收盘价并重建缓存。
   - 调度前可手工跑 `python -m opt_data.cli schedule --simulate --config config/opt-data.test.toml --symbols AAPL,MSFT`，以确保缓存可用并验证调度计划。

## 常用命令
- 基础：`make install`、`make fmt lint test`
- Snapshot（单槽）：
  - `python -m opt_data.cli snapshot --date 2025-09-29 --slot 09:30 --symbols AAPL --config config/opt-data.test.toml`
  - `python -m opt_data.cli close-snapshot --date 2025-11-24 --symbols AAPL,MSFT --config config/opt-data.test.toml`（仅采集当日收盘槽，默认 16:00/早收盘取实际最后槽；运行前会预检并自动重建缺失/空的 contracts cache，可用 `--fail-on-missing-cache` 禁用自动重建；不提供/不支持 `--force-refresh`）
  - 收盘快照请设置 `IB_MARKET_DATA_TYPE=2`（盘后/回放模式，便于收盘后读取当日数据），命令内部也会强制 `reqMarketDataType(2)`；盘中快照/调度则按配置 `ib.market_data_type`（默认 1 实时，如需延迟改为 3/4）。
- 每日调度（整天所有槽位 + 日终）：
  - 生产模拟运行（不常驻 scheduler，只一次性跑完当日所有 snapshot/rollup/enrichment 任务）：  
    - `python -m opt_data.cli schedule --simulate --config config/opt-data.toml`
  - 生产实际调度（常驻 APScheduler，按 30 分钟间隔触发盘口快照，并在收盘后执行 rollup/enrichment）：  
    - `python -m opt_data.cli schedule --live --config config/opt-data.toml`
  - 测试环境（仅 AAPL/MSFT 冒烟）：  
    - `python -m opt_data.cli schedule --simulate --config config/opt-data.test.toml --symbols AAPL,MSFT`
- 日终归档：`python -m opt_data.cli rollup --date 2025-09-29 --config config/opt-data.test.toml`
- OI 回补：`python -m opt_data.cli enrichment --date 2025-09-29 --fields open_interest --config config/opt-data.test.toml`（T+1 通过 `reqMktData` + tick `101` 读取上一交易日收盘 OI；**注意**：enrichment 需要 `market_data_type=1`（实时数据）才能成功获取 OI，否则 tick-101 方法会失败并降级到历史数据方法，而历史数据方法会被 IBKR 拒绝）
- 历史数据（日线）：`python -m opt_data.cli history --symbols AAPL --days 30 --config config/opt-data.toml`（使用 8-hour bar 聚合获取日线数据，支持 `--force-refresh` 强制刷新合约缓存）
- 存储维护：`make compact`（周度合并）、`python -m opt_data.cli retention --view intraday --older-than 60`
- **Console UI（Web 控制台）**：`streamlit run src/opt_data/dashboard/app.py` 或 `.venv/bin/streamlit run src/opt_data/dashboard/app.py`
  - 在浏览器访问 http://localhost:8501
  - **Overview 标签**：查看系统指标、快照活动趋势、延迟分布、最近错误
  - **Console 标签**：数据状态面板、盘中快照控制、EOD 操作（收盘快照、Rollup、Enrichment）、错误日志查看
  - **注意**：Console UI 使用独立的 client ID (200-250 范围)，不会与 CLI 进程冲突；UI 操作为同步执行，长时间操作会阻塞界面

> 若 CLI 尚未提供对应子命令，可调用等价脚本；命令命名需与实现同步。

## 冒烟验证（测试目录）
1. 测试配置仅保留 AAPL，`max_strikes_per_expiry=2`，`slot_range=["09:30","11:00"]`。
2. 启动 Gateway，执行 `python -m opt_data.cli snapshot --date today --slot now --symbols AAPL --config config/opt-data.test.toml`，采集 ≥2 个槽位。
3. 检查输出目录：
   - `data_test/raw/ib/chain/view=intraday/date=YYYY-MM-DD/underlying=AAPL/...`
   - `data_test/clean/ib/chain/view=intraday/...`
   - 字段包含 `sample_time`（UTC）、`slot_30m`、`market_data_type=1`；`data_quality_flag` 为空或包含 `[]`。
4. 模拟无实时权限：临时设置 `market_data_type=3` 再采集一槽，确认输出标记 `delayed_fallback`。
5. 收盘后运行 `python -m opt_data.cli rollup --date today --config ...`，验证 `rollup_source_slot=13`（或 fallback）与 `rollup_strategy` 字段。
6. 查看 `state_test/run_logs/` 的 snapshot/rollup 日志，确保记录槽位、回退、延迟等信息。
7. **历史数据验证**：执行 `python -m opt_data.cli history --symbols AAPL --days 5 --config config/opt-data.test.toml --force-refresh`，确认 `data_test/clean/ib/chain/ib/history` 下生成 JSON 文件。

## 收盘快照独立 View 与双 Universe 配置

### 概述

系统支持将盘中快照与收盘快照分离存储和采用不同的 symbol 清单，以优化 API 负载和数据管理：

| 快照类型 | 写入路径 | 默认 Universe | 用途 |
|----------|----------|---------------|------|
| 盘中 `snapshot` | `view=intraday` | `universe.intraday.csv` | 高频监控，精简清单 |
| 收盘 `close-snapshot` | `view=close` | `universe.csv` | 日终归档，全量清单 |

### 配置项

**Universe 配置** (`config/opt-data.toml`)：
```toml
[universe]
file = "config/universe.csv"                    # 默认全量清单
intraday_file = "config/universe.intraday.csv"  # 盘中快照专用（可选）
close_file = ""                                 # 收盘快照专用（为空则回退到 file）
```

**Rollup 配置**：
```toml
[rollup]
close_slot = 13                     # 16:00 槽位
fallback_slot = 12                  # 15:30 备用槽位
allow_intraday_fallback = false     # close view 缺失时是否回退到 intraday
```

**Snapshot 默认参数**：
- fetch_mode 默认 `reqtickers`（生产/compare 配置）；测试配置如未指定，请补 `fetch_mode=reqtickers` 以对齐。
- strikes_per_side：生产模板 50，测试模板如为 0 代表不截取行权价。
- 收盘 `close-snapshot` 强制 `market_data_type=2`；盘中按配置 `ib.market_data_type`。

### 存储路径

```
data/
├── raw/ib/chain/
│   ├── view=intraday/date=YYYY-MM-DD/...   # 盘中快照
│   └── view=close/date=YYYY-MM-DD/...      # 收盘快照
├── clean/ib/chain/
│   ├── view=intraday/...
│   ├── view=close/...
│   ├── view=daily_clean/...                # Rollup 输出
│   └── view=daily_adjusted/...
```

### Rollup 行为

| 场景 | 行为 |
|------|------|
| `view=close` 存在 | 使用 close 数据进行 rollup |
| `view=close` 缺失 + `allow_intraday_fallback=false` | **报错退出**，需先运行 close-snapshot |
| `view=close` 缺失 + `allow_intraday_fallback=true` | 回退到 intraday 末槽，添加 `fallback_intraday` 标记 |

### 命令示例

```bash
# 盘中快照（使用 universe.intraday.csv，写入 view=intraday）
python -m opt_data.cli snapshot --date today --slot now --config config/opt-data.toml

# 收盘快照（使用 universe.csv，写入 view=close）
python -m opt_data.cli close-snapshot --date 2025-12-05 --config config/opt-data.toml

# 覆盖默认 universe（临时使用全量清单采集盘中）
python -m opt_data.cli snapshot --date today --slot now --universe config/universe.csv

# compare 配置（独立目录，便于对比）
python -m opt_data.cli close-snapshot --date today --config config/opt-data.test.compare.toml --universe config/universe.csv

# 清理并重跑 compare（需要先删除 compare 目录）
rm -rf data_test_compare state_test_compare
python -m opt_data.cli close-snapshot --date today --config config/opt-data.test.compare.toml --universe config/universe.csv

### 运行时参数回显

`snapshot` / `close-snapshot` 在执行前会打印 `[snapshot:params]` / `[close-snapshot:params]`，展示实际生效的配置与路径：config、universe、view、slot、symbols、fetch_mode、strikes_per_side、generic_ticks、market_data_type、paths.raw/clean/state/run_logs，便于核对是否使用了预期的清单与模式。

### 参考价获取与重试

- 参考价获取使用 `fetch_underlying_close`（`reqMktData` snapshot），收盘/盘后默认 `market_data_type=2`。若首次返回 None/NaN，会等待 1 秒再重试一次，并尝试 last/close/bid/ask 回退。
- 若仍失败，日志中会出现 `reference_price_failed`，该标的会被跳过。可单独重跑：  
  `python -m opt_data.cli close-snapshot --date <date> --symbols SPY,QQQ --config ...`

# Rollup（优先读取 view=close）
python -m opt_data.cli rollup --date 2025-12-05 --config config/opt-data.toml
```

### 运维流程

1. **正常流程**：
   - 盘中：调度器按 30 分钟间隔执行 `snapshot`（精简清单）
   - 16:00 后：执行 `close-snapshot`（全量清单，写入 `view=close`）
   - 17:00：执行 `rollup`（优先读取 `view=close`）

2. **收盘快照缺失处理**：
   - **推荐**：重跑 `close-snapshot` 补数据
   - **不推荐**：启用 `allow_intraday_fallback`（会导致数据质量下降）
   - 若启用 fallback，需在日报中注明 `fallback_intraday` 比例

3. **历史数据迁移**：
   - 已有历史数据保持在 `view=intraday` 不变
   - 新数据自动写入对应 view
   - Rollup 已处理过的历史日期无需重跑


## 调度配置
### APScheduler（开发环境）
- `BackgroundScheduler(timezone="America/New_York")`。
- 注册任务：
  - `discover_contracts`：09:25 ET。
  - `snapshot_job`：cron `minute=0,30`、`hour=9-15`；根据早收盘表动态裁剪。
  - `rollup_job`：17:00 ET。
  - `oi_enrichment_job`：次日 07:30 ET（周二至周五；周一处理上周五）。
- 在 scheduler 启动时预计算当日槽列表（考虑早收盘），并写入 `state/run_logs/apscheduler/*.jsonl`。

### launchd（macOS）
- `com.optdata.snapshot.plist`：`StartCalendarInterval` 覆盖 09:30–16:00 每 30 分钟，调用 `python -m opt_data.cli snapshot --run-once --config ...`。
- `com.optdata.rollup.plist`：17:00 执行 rollup。
- `com.optdata.oi-enrichment.plist`（可选）：次日 07:30 执行 enrichment。
- 在 plist `EnvironmentVariables` 中设置 `TZ`, `IB_*`, `PATH`（包含虚拟环境）。
- 日志输出重定向到 `state/run_logs/launchd/*.log`。

### systemd（Linux）
- 使用 systemd ≥249，支持 `Timezone=`。三个 timer：
  - `opt-data-snapshot.timer`: `OnCalendar=Mon-Fri 09:30:00..16:00:00/00:30`, `Timezone=America/New_York`。
  - `opt-data-rollup.timer`: `OnCalendar=Mon-Fri 17:00`, `Timezone=America/New_York`。
  - `opt-data-enrichment.timer`: `OnCalendar=Tue-Fri 07:30`, `Timezone=America/New_York`。
- 对应 service 调用虚拟环境脚本，并将 stdout/stderr 写入 `state/run_logs/systemd/`。
- 早收盘：timer 触发脚本需检查日历并自行跳过闭市后的槽位。

## 限速与重试
- 令牌桶配置：`rate_limits.snapshot.per_minute=30`、`max_concurrent_snapshots=10`（放量后调优）。
  - *注*：发现阶段（Discovery）不再施加应用层限速，完全依赖 IB Pacing。
- Pacing violation 处理：
  - 首次等待 30s，随后指数退避 `60s → 120s → 240s`；
  - 超过阈值后将槽位加入补采队列，标记 `slot_retry_exceeded`。
- 实时权限缺失：IB 返回 `No market data permissions` 时自动切换至延迟行情（若允许），写入 `market_data_type=3` 与 `delayed_fallback`；同时在告警渠道提示。
- 合约发现失败：重试前确认 Gateway 状态；若在交易时间内仍失败，临时复用上一日缓存并标记 `discovery_stale`。

## 日志与错误收集
- 日志目录：所有运行日志写入 `state/run_logs/<task>/`；错误日志统一追加到 `state/run_logs/errors/errors_YYYYMMDD.log`。
- 标的参考价：snapshot 获取的 `reference_price` 事件会追加到 `state/run_logs/reference_prices/reference_prices_YYYYMMDD.jsonl`，字段含 `trade_date/slot/symbol/reference_price/ingest_id`，用于后续 IV/Greeks 校验。
- CLI/调度脚本需捕获未处理异常并写入错误日志，内容包含时间戳、任务、`ingest_id`、堆栈。
- 每日 17:30 ET 运行 `python -m opt_data.cli logscan --date today --keywords ERROR,CRITICAL,PACING --write-summary --max-total 0` 生成摘要（`state/run_logs/errors/summary_YYYYMMDD.json`），若匹配条数 >0 则退出码非零并触发告警。
- 保留策略：错误日志默认保留 30 天，可通过 `python -m opt_data.cli retention --view errors --older-than 30` 清理。
- 告警钩子：当 `logscan` 检测到关键字或回退率超阈值时，触发通知（邮件/Slack）并在 `TODO.now.md` 建立跟踪条目。

## 故障处理
| 情况 | 诊断步骤 | 解决方案 |
| --- | --- | --- |
| Gateway 连接失败 | 查看 API 日志、`netstat`、是否有旧 session | 重启 Gateway，调整 `clientId`，确保端口未占用 |
| 槽位缺失 | 查 `state/run_logs/snapshot_*`，确认错误码 | 通过 `snapshot --slot HH:MM --retry-missed` 补采；补采后验证去重 |
| 收盘槽未采集 | 检查 16:00 槽日志，确认超时或降级原因 | 扩大宽限、提前 15:55 触发额外采集或降低并发 |
| Rollup 回退过多 | 查看 `rollup_strategy` 字段；确认是否因槽位缺失 | 补齐缺失槽，再重跑 rollup；必要时优化宽限或补采逻辑 |
| OI 回补失败 | `state/run_logs/enrichment_*` 中查看错误 | 次日重试；连续 3 次失败标记 `oi_enrichment_failed` 并通知运营 |

### OI Enrichment 优化路线图

当前 OI enrichment 已实现生产级稳定性（tick-101 事件驱动 + historical 降级），以下为分阶段优化建议：

**✅ 立即可做（本周）**
1. **OI 来源记录**：在 enrichment 结果中记录 OI 来源（`tick101` / `historical`），便于分析成功率分布
2. **配置化参数**：将 `timeout=8.0` 和 `durationStr="3 D"` 提取到 `config/opt-data.toml` 的 `[enrichment]` 段，便于不同环境调参

**🔄 短期优化（1-2周）**
3. **运行观测**：收集一周 enrichment 日志，分析：
   - tick-101 成功率（通过新增的 debug 日志统计）
   - historical fallback 触发频率
   - 长期失败的 conId 列表（考虑标记跳过）
4. **文档更新**：在 `ops-runbook.md` 明确区分 `enrichment` 命令（生产）vs `data_test/aapl_oi_live_final.py`（本地验证）的用途

**🚀 中期增强（1-2月，根据需要）**
5. **有限并发**：在 `EnrichmentRunner.run()` 内批次处理 5-10 个合约（保持同步接口，内部用 asyncio worker 池），受 TokenBucket 控制，避免完全串行
6. **智能重试**：区分 IB 420/321 错误，针对 pacing 错误做 1-2 次指数退避重试

**🔮 观望（需要时再做）**
7. **完全异步化**：仅在高并发场景（如全量 S&P 500）必要时重构整个 pipeline 为 async
8. **第三层 fallback**：若 IBKR 真的废弃 `OPTION_OPEN_INTEREST` bar，可添加 TRADES bar + field 84 作为第三层保底

**参考脚本**：`data_test/aapl_oi_live_final.py` - 用于本地验证 tick-101 方法是否正常工作（1.1s 获取 10 个合约 OI）
| compaction 失败 | 检查 `state/run_logs/compaction_*.jsonl` | 确认无进程占用；必要时拆分分区或调整 `target_file_size_mb` |

## 恢复流程
1. 通过日志定位受影响的 `trade_date`、`slot_30m`、`underlying`。
2. 使用 `snapshot --slot` 或 `snapshot --replay-missed` 补采；重跑后确认 `(trade_date, sample_time, conid)` 无重复。
3. 重新执行 `rollup --date <trade_date>`；如需补全 OI，待 enrichment 成功后检查 `open_interest` 与 `data_quality_flag`。
4. 更新 QA 报告、`TODO.now.md`、`PLAN.md`，记录故障原因、处理步骤与残留风险。

## 扩容执行流程
1. **扩容申请与记录**
   - 扩容前在 `TODO.now.md` 添加任务，并在 `PLAN.md` 更新当前阶段与目标阶段。
   - 收集最近 5 个交易日的 `metrics_YYYYMMDD.json`、`selfcheck` 报告，确保槽位覆盖率 ≥90%、rollup 回退率 ≤5%、延迟行情占比 <10%、`missing_oi` 补齐率 ≥95%。
   - 核对 `state/run_logs/errors/errors_YYYYMMDD.log` 是否存在未关闭告警，若有需先完成补救。
2. **阶段推进指引**
   - **阶段 0 → 阶段 1（AAPL → AAPL,MSFT）**  
     更新 `config/universe.csv` 增加 MSFT，维持默认 `slot_range`；在 `config/opt-data.toml` 将 `rate_limits.snapshot.per_minute` 调整至 45，如 Gateway 负载允许将 `max_concurrent_snapshots` 提升至 12。运行 1 日全量模拟（snapshot + rollup + enrichment），确认 pacing 告警 ≤1 次。
   - **阶段 1 → 阶段 2（双标的 → Top10）**  
    追加前 10 权重标的并启用 `discovery.midday_refresh_enabled=true`（仅新增合约，依赖当日缓存，不刷新已存在的合约列表）；`rate_limits.snapshot.per_minute=60`、`max_concurrent_snapshots=16`，必要时开启 `snapshot.batch_size=3-4` 以分批执行。同样先在测试配置中跑通 1 日闭环后再切换正式配置。
   - **阶段 2 → 阶段 3（Top10 → 全量 S&P 500）**  
     将 universe 扩展至全量 S&P 500，启用调度分组（在配置文件内定义每批标的列表），并在 CLI 调用中传入批次参数。初始限速设 `rate_limits.snapshot.per_minute=90`、`max_concurrent_snapshots=20`，并监控 pacing 告警；若告警超过 3 次/周，及时调低限速或增加批次数。
3. **扩容上线步骤**
   - 在正式配置切换前，运行 `python -m opt_data.cli schedule --simulate --config <target>` 确认调度顺序及批次设置。
   - 扩容当日 09:00 ET 前执行一次 `snapshot --dry-run`（仅生成计划、不写数据）检查合约列表与槽位。
   - 当日采集期间密切关注 `state/run_logs/snapshot_*.jsonl` 的 pacing 字段与错误日志；17:30 ET 前运行 `logscan` 确认无新增严重告警。
   - 扩容后首周每日记录 QA 指标与异常，输出至 `state/run_logs/metrics/expansion_diary_YYYYMMDD.json` 并在周例会上复盘。
4. **扩容回退**
   - 若槽位覆盖率跌破阈值或 pacing 告警连续两日超限，立即将 universe 回滚至上一阶段配置，并在 `TODO.now.md` 创建专项条目。
   - 回退完成后重新执行自检，确认数据质量恢复，再评估重新扩容的时间窗口。

## 例行维护
- **每日**：rollup 后执行 `python -m opt_data.cli qa --date <trade_date>`，校验槽位覆盖率、延迟行情、rollup 回退率与 OI 补齐率并写入 `metrics_YYYYMMDD.json`；如 FAIL 立即补救。监控指标与 `logscan` 摘要一并纳入告警。
- **每周**：运行 `make compact`，审阅 compaction 日志；确认 intraday 分区文件数下降、冷分区采用 ZSTD。
- **每月**：复核 `config/universe.csv` 与实际宇宙；评估是否扩容并调整限速。
- **持续**：监控磁盘占用与保留策略执行结果；定期备份 `config/`、`docs/`、`state/`。

## 其他注意事项
- 调度命令需指定虚拟环境路径或使用 wrapper，避免系统 Python 与项目依赖冲突。
- 实时数据仅用于内部研究；若涉及再分发需提前评估许可限制。
- 任何配置调整必须在测试目录先跑完整闭环（snapshot + rollup + enrichment），再推广至正式环境。
- 敏感凭据禁止写入仓库，务必通过环境变量或受控文件管理。

## IBKR 期权链拉取最佳实践（AAPL/SPX）

以下经验来自 AAPL/SMART 成功拿到期权链报价与 Greeks 的实测，供采集器与内部诊断脚本参考。

**核心配置**
- 端口与会话
  - TWS：默认统一使用 `7497` 端口（原纸交易端口）；如本地 TWS 配置不同，请按实际调整（IB Gateway 常见为 `4002=Paper`，`4001=Live`）。
  - 连接后以账户号快速自检：`DU*` 多为纸盘，`U*` 多为实盘。
- 行情类型优先级
  - `marketDataType=1`（实时）优先；若无实时权限，IB 会自动回退到延迟（3/4）。即使显式设置 3/4，只要有实时权限仍可能返回 `1`。
- 必要订阅勾子（generic ticks）
  - 对期权必须带上：`100,101,104,105,106,165,221,225,233,293,294,295`。
  - 其中 `100`（OptionComputation）是模型 IV/Greeks 的关键；`233` 提供 `rtVolume`。
- 交易所选择
  - 默认 `SMART`，若长时间无报价可尝试 `CBOE` 或 `CBOEOPT`。同一账户在不同 venue 的可见性可能不同。

**订约与订阅流程（2025 升级）**
- 标的资格化
  - `stock = Stock('AAPL','SMART','USD')`；`ib.qualifyContracts(stock)`。
- 期权链发现
  - `reqSecDefOptParams` 选择 `exchange=SMART`（或 CLI 指定）；取最近到期 `near_exp`。
  - 行权价：围绕现价挑最近 N 个（推荐 2–5 个），或按窗口过滤（如 ±$15）。
  - 现价获取：优先 `reqHistoricalData(1 day, useRTH=True)` 的最近收盘；备选：对标的 `reqMktData` 后读 `marketPrice()`。
  - 资格化：构造 `Option(symbol, expiryYYYYMMDD, strike, right, exchange='SMART')` 列表，使用批量 `qualifyContracts`/`qualifyContractsAsync` 获取 `conId`；不使用 `reqContractDetails`。
- 逐合约订阅（推荐）
  - 对每个 `Option`：`reqMktData(option, genericTickList=上文, snapshot=False)`；等待单个合约“就绪”后立刻 `cancelMktData`，降低 IB pacing 压力。
  - “就绪”条件：
    - 有任一价格字段（bid/ask/last/close）且非 NaN，且
    - Greeks/IV 字段存在且非 NaN（优先从 `ticker.modelGreeks` 读取）。
  - 采集字段：bid/ask/mid、`rtVolume` 解析、`modelGreeks.{impliedVol,delta,gamma,theta,vega,optPrice,undPrice}`，以及 `marketDataType`、`time`。

**就绪判定与容错**
- 过滤无效 IV：将 `None/-1/0/NaN` 视为未就绪；无 `ticker.impliedVolatility` 时回退到 `ticker.modelGreeks.impliedVol`。
- mid 价仅在 bid/ask 均有效时计算；否则留空。
- 对批量模式，应允许部分合约失败，不应以“就绪率门槛”阻断全部输出。

**并发与限速**
- 遵守 IBKR pacing（消息/秒、订阅总量）。实测更稳的策略为“逐合约顺序订阅 + 采样即取消”。
- 若必须并发，使用信号量限制（如并发 20–40），批间休眠 ≥1s，并对异常/超时的任务做降级处理。

**常见问题排查**
- MarketDataType 显示 1 而脚本设置为 3/4：账户有实时权限，被自动提升，属正常。
- 始终无 bid/ask：账号缺少期权顶级行情，或非交易时段；尝试切换到 `CBOE/CBOEOPT`，或仅依赖模型 Greeks。
- DataFrame 为空：检查 entitlement、交易时段、generic ticks 是否传入、是否取消过早，以及是否订阅了正确的 tradingClass（如 SPX vs SPXW）。
- 端口不通：确认 TWS/Gateway API 设置、Socket Port、`Read Only API` 是否关闭，以及客户端 `clientId` 不冲突。
- 缓存强制：生产/测试运行必须复用 `paths.contracts_cache` 下对应日期的缓存文件，`--force-refresh` 已被禁用；若缓存缺失会报错终止，避免拉取未知行权价。调试时可开 DEBUG 查看 `SecDef strikes fetched` 日志（缓存对比），但不会自动 fallback 到 SecDef。调度入口会在启动前自动重建缺失/损坏缓存（获取标的收盘价后调用 `discover_contracts_for_symbol`），重建失败即终止，需先修复缓存再重试。
 - 缓存写入检查：发现阶段会将合约列表写入 `paths.contracts_cache` 对应文件，写入失败会直接报错；运行中若发现缓存缺失或空文件，需先修复缓存（重跑发现、检查目录权限）再继续 snapshot/rollup。

**开发/测试脚本与实验**
- data_test 脚本（AAPL 诊断、SPY 收盘批并发等）已整理到 `docs/dev/ops-runbook-dev.md`。生产调度仍按本手册的顺序批模式执行，实验性并发仅限测试配置。 
