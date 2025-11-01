# 运维手册：30 分钟快照与日终归档

## 运行前准备
1. 启动 IB Gateway/TWS（Paper：`127.0.0.1:7497`），确认登录账号具备美股期权**实时行情**权限；若仅有延迟权限，允许自动降级。
2. 准备 Python 3.11 环境：`python3.11 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -e '.[dev]'`，或运行 `make install`（确保 `python3` 指向 3.11）。
3. 配置 `.env` / 环境变量：
   - `IB_HOST`（默认 `127.0.0.1`）
   - `IB_PORT`（默认 `7497`）
   - `IB_CLIENT_ID`（默认 `101`）
   - `IB_MARKET_DATA_TYPE=1`（实时；若需强制延迟则设为 `3/4`）
   - `TZ=America/New_York`（统一调度时区）
4. 复制正式配置至测试版：`cp config/opt-data.toml config/opt-data.test.toml`，并将 `paths.raw/clean/state/contracts_cache/run_logs` 指向 `data_test/`、`state_test/`。
5. 核对核心配置：
   - `[acquisition] mode="snapshot"`、`market_data_type=1`、`allow_fallback_to_delayed=true`
   - `slot_grace_seconds=120`、`rate_limits.snapshot.per_minute=30`、`max_concurrent_snapshots=10`
   - `[discovery] policy="session_freeze"`、`pre_open_time="09:25"`；若启用增量刷新，设 `midday_refresh_enabled=true` 且仅新增合约
   - `intraday_retain_days=60`、`weekly_compaction_enabled=true`、`same_day_compaction_enabled=false`
6. 确认交易日历（含早收盘）可用；调度器/cron 中必须显式设置 `America/New_York`。

## 常用命令
- 基础：`make install`、`make fmt lint test`
- Snapshot（单槽或按计划）：
  - `python -m opt_data.cli snapshot --date 2025-09-29 --slot 09:30 --symbols AAPL --config config/opt-data.test.toml`
  - `python -m opt_data.cli snapshot --run-day --config config/opt-data.toml`（执行当日剩余槽位）
- 日终归档：`python -m opt_data.cli rollup --date 2025-09-29 --config config/opt-data.test.toml`
- OI 回补：`python -m opt_data.cli enrichment --date 2025-09-29 --fields open_interest --config config/opt-data.test.toml`
- 存储维护：`make compact`（周度合并）、`python -m opt_data.cli retention --view intraday --older-than 60`

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
- 令牌桶配置：`rate_limits.discovery.per_minute=5`、`rate_limits.snapshot.per_minute=30`、`max_concurrent_snapshots=10`（放量后调优）。
- Pacing violation 处理：
  - 首次等待 30s，随后指数退避 `60s → 120s → 240s`；
  - 超过阈值后将槽位加入补采队列，标记 `slot_retry_exceeded`。
- 实时权限缺失：IB 返回 `No market data permissions` 时自动切换至延迟行情（若允许），写入 `market_data_type=3` 与 `delayed_fallback`；同时在告警渠道提示。
- 合约发现失败：重试前确认 Gateway 状态；若在交易时间内仍失败，临时复用上一日缓存并标记 `discovery_stale`。

## 日志与错误收集
- 日志目录：所有运行日志写入 `state/run_logs/<task>/`；错误日志统一追加到 `state/run_logs/errors/errors_YYYYMMDD.log`。
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
| compaction 失败 | 检查 `state/run_logs/compaction_*.jsonl` | 确认无进程占用；必要时拆分分区或调整 `target_file_size_mb` |

## 恢复流程
1. 通过日志定位受影响的 `trade_date`、`slot_30m`、`underlying`。
2. 使用 `snapshot --slot` 或 `snapshot --replay-missed` 补采；重跑后确认 `(trade_date, sample_time, conid)` 无重复。
3. 重新执行 `rollup --date <trade_date>`；如需补全 OI，待 enrichment 成功后检查 `open_interest` 与 `data_quality_flag`。
4. 更新 QA 报告、`TODO.now.md`、`PLAN.md`，记录故障原因、处理步骤与残留风险。

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
