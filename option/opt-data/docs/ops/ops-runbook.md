# 运维手册：30 分钟快照与日终归档

> 本手册面向**生产环境运维与调度**：描述 `opt_data.cli` 相关命令在正式配置上的使用方式与故障排查流程。开发/测试脚本（`data_test/*`）与实验性配置请参阅 `docs/dev/ops-runbook-dev.md`。

## TL;DR：明日值班一屏清单（生产）
> 目标：一条命令启动当天调度；一条命令打开 UI；收盘后两条命令完成验收。

- 环境前置：
- IB Gateway/TWS 已启动并登录；端口/账号与 `config/opt-data.snapshot.local.toml` 一致（默认 `IB_HOST=127.0.0.1`、`IB_PORT=4001`）。
  - 调度时区必须是 ET：`TZ=America/New_York`（launchd/systemd 也要显式设置）。
  - 使用本地生产配置：`config/opt-data.snapshot.local.toml`（从 `config/opt-data.toml` 复制并按本机修改；已在 `.gitignore`）。

- 启动调度（推荐在 09:20–09:29 ET 启动）：
  - 手动值守（仅调度单个交易日，进程需保持到次日 04:30 enrichment 结束）：`python -m opt_data.cli schedule --live --config config/opt-data.snapshot.local.toml`
  - 无人值守（一次启动，交易日每天自动初始化 09:20 ET）：`python -m opt_data.cli schedule --live --continuous --config config/opt-data.snapshot.local.toml`
  - 定时器模式（适配 launchd/systemd timer/cron：跑完当日任务自动退出，第二天由定时器重启）：`python -m opt_data.cli schedule --live --exit-when-idle --config config/opt-data.snapshot.local.toml`
  - 常用参数：`--symbols AAPL,MSFT`（临时缩小范围）、`--date 2025-12-15`（跑指定交易日；不适用于 `--continuous`）
- 启动盘中 streaming 订阅（交易日 09:35–16:15 ET，独立进程）：推荐用 `scripts/ops/streaming_loop.py` 长期运行；或由 timer 在 09:35 ET 拉起 `python -m opt_data.cli streaming --config config/opt-data.streaming.local.toml --duration 23100`
- 纯终端长期值守（不依赖 launchd，需开两个终端窗口）：
  - 终端 1（snapshot 调度）：`TZ=America/New_York .venv/bin/python -m opt_data.cli schedule --live --continuous --config config/opt-data.snapshot.local.toml`
  - 终端 2（streaming）：`./scripts/ops/streaming_loop.py`

- 开始前快速预演（只打印计划并立即执行当日任务，适合验证配置；不建议每天都跑）：
  - `python -m opt_data.cli schedule --simulate --config config/opt-data.snapshot.local.toml`

- 打开 UI（Dashboard/Operations 面板）：
  - `streamlit run src/opt_data/dashboard/app.py`
  - `streamlit run src/opt_data/dashboard/app.py --server.address 0.0.0.0`

- 收盘后验收（生成 selfcheck/logscan/metrics 输出；失败会返回非零退出码）：
  - `python -m opt_data.cli selfcheck --date today --config config/opt-data.snapshot.local.toml --log-max-total 1`
  - `python -m opt_data.cli logscan --date today --config config/opt-data.snapshot.local.toml --max-total 1 --write-summary`

## 远程查看生产设备状态
> 目标：不登录桌面也能看调度/采集是否正常。

- 方案 A（推荐，Dashboard）：在生产机启动 UI，并通过 SSH 端口转发访问
  - 生产机：`streamlit run src/opt_data/dashboard/app.py --server.address 0.0.0.0`
  - 本机：`ssh -N -L 8501:127.0.0.1:8501 <user>@<prod_host>`
  - 浏览器访问：`http://127.0.0.1:8501`
- 方案 B（日志 + 快照）：用 SSH 直查运行日志
  - 本机：terminal运行：ssh datareader@100.71.7.100
  - 调度 stdout/stderr：`state/run_logs/launchd_stdout.log` / `state/run_logs/launchd_stderr.log`
  - 任务日志：`state/run_logs/<task>/`（snapshot/rollup/enrichment）
  - 错误汇总：`state/run_logs/errors/errors_YYYYMMDD.log` 与 `state/run_logs/errors/summary_YYYYMMDD.json`
- 方案 C（验收信号）：远程运行验收命令并观察退出码
  - `python -m opt_data.cli selfcheck --date today --config config/opt-data.snapshot.local.toml --log-max-total 1`
  - `python -m opt_data.cli logscan --date today --config config/opt-data.snapshot.local.toml --max-total 1 --write-summary`

## 无人值守运行（推荐）
> 目标：机器重启/进程崩溃后自动拉起；无需每天手动重启调度。

- 方案 A（**单进程常驻**）：使用 `--continuous`，进程每天 09:20 ET 自动初始化当日任务；再用 launchd/systemd 设置崩溃自动重启。
  - `python -m opt_data.cli schedule --live --continuous --config config/opt-data.snapshot.local.toml`
- 方案 B（**每日一次性任务**）：使用 `--exit-when-idle`，跑完当日任务自动退出；用 launchd/systemd timer/cron 每天 09:20 ET 拉起一次。
  - `python -m opt_data.cli schedule --live --exit-when-idle --config config/opt-data.snapshot.local.toml`

运维提示（两种方案都适用）：
- launchd/systemd 必须显式设置 `TZ=America/New_York`，避免调度时区漂移。
- 推荐将 `universe.file` 指向本机专用文件（如 `config/universe.local.csv`，受 `.gitignore` 保护），避免调度自动补 conId 时污染仓库文件。

### macOS launchd（方式 B）最小配置
- 复制模板：`docs/ops/launchd/com.legosmos.opt-data.timer.plist` → `~/Library/LaunchAgents/com.legosmos.opt-data.timer.plist`，如路径与本机不一致请替换为你的仓库绝对路径。
- 确保脚本可执行：`chmod +x scripts/launchd/opt-data-daily.sh`
- 启用（当前用户会话）：`launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.legosmos.opt-data.timer.plist`
- 立刻跑一次：`launchctl kickstart -k gui/$(id -u)/com.legosmos.opt-data.timer`
- 查看状态：`launchctl print gui/$(id -u)/com.legosmos.opt-data.timer`
- 停用：`launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.legosmos.opt-data.timer.plist`
- 可选：在 plist 的 `EnvironmentVariables` 里设置 `OPT_DATA_ROOT`（仓库根目录），脚本会优先使用它；终端里也可临时 `export OPT_DATA_ROOT=/Users/michaely/projects/legosmos/option/opt-data`。

注意：
- `StartCalendarInterval` 使用**系统本地时区**；若机器不在 ET，请将启动时间换算到本地时间，或将系统时区设为 `America/New_York`。
- 若 `launchctl print gui/$(id -u)/com.legosmos.opt-data.timer` 提示 “Could not find service …”，通常是 plist 已复制但尚未加载：重新执行 `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.legosmos.opt-data.timer.plist`（或注销/登录一次）。
- 若看到 “lock exists” 报错，说明上一次任务未结束（或异常退出遗留锁目录）；可检查进程后清理 `state/run_locks/opt-data-daily.lock` 再重试。

## Streaming 订阅无人值守运行
> 目标：交易日 09:35–16:15 ET 启动，收盘后自动退出。

- 方式 A（纯 Python 常驻）：运行 `scripts/ops/streaming_loop.py`，每天 09:35 ET 自动启动，并调用 `scripts/ops/streaming_duration.py` 计算 `--duration` 在收盘后退出。
- 方式 B（定时器）：使用 launchd/systemd timer/cron 在 09:35 ET 拉起 `scripts/launchd/opt-data-streaming.sh`，脚本会调用 `scripts/ops/streaming_duration.py` 自动计算 `--duration` 并在收盘后退出。
- macOS launchd：复制模板 `docs/ops/launchd/com.legosmos.opt-data.streaming.plist` 到 `~/Library/LaunchAgents/` 并按本机路径调整。
- 手动运行示例：`python -m opt_data.cli streaming --config config/opt-data.streaming.local.toml --duration 23100`
- 交易日控制：timer/cron 需配合交易日历（节假日/早收盘）跳过或缩短运行；早收盘识别依赖 `pandas-market-calendars`。
- 时区：与调度一样，确保运行环境显式设置 `TZ=America/New_York`。

## 当前生产范围与运行参数
- 覆盖范围：`config/universe.csv` 全量清单（已超过原 Stage 2/Top 10 目标）。
- 速率与并发：`rate_limits.snapshot.per_minute=30`、`max_concurrent_snapshots=14`（提高并发/分批调度的方案暂缓，需额外评审）。
- 调度链路（ET）：09:30–16:00 每 30 分钟 `snapshot` → 17:30 `close-snapshot` 后紧接 `rollup` → 次日 04:30 `enrichment` → 自检/日志扫描。
- 环境前置：IB Gateway/TWS 实时行情权限（若降级至延迟需关注 `delayed_fallback` 占比）、`pandas-market-calendars` 交易日历可用、`TZ=America/New_York`。
- 输出与日志：数据写入 `data/raw|clean/ib/chain/`（分 view/parquet），状态与日志位于 `state/run_logs/`（errors/selfcheck/metrics）。

## 运行前准备
1. 启动 IB Gateway/TWS（默认：`127.0.0.1:4001`），确认登录账号具备美股期权**实时行情**权限；若仅有延迟权限，允许自动降级。
2. 推荐使用项目专用虚拟环境（避免污染 base Conda 并触发 NumPy 升级冲突）：
   - venv 路径（仓库根目录执行）：`python3.11 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements-dev.lock && .venv/bin/pip install -e option/opt-data --no-deps`
   - 或 Conda 隔离：`conda create -n opt-data python=3.11 && conda activate opt-data && pip install -r requirements-dev.lock && pip install -e option/opt-data --no-deps`
   - 也可运行仓库根目录 `make install`（确保 `python3` 指向 3.11）。
3. 依赖与 SDK 规范：
   - 统一使用 `ib_insync` 作为 IBKR Python 接入层；项目不直接使用 `ibapi` 原生包。
   - 安装：仓库根目录 `requirements-dev.lock` 已包含 `ib-insync`；无需额外安装 `ibapi`。
4. Snapshot 配置与合约发现（2025 升级）：
   - 发现阶段（Discovery）：使用 `reqSecDefOptParams()` + 批量 `qualifyContracts/qualifyContractsAsync`（仅 `SMART`）。不再调用 `reqContractDetails`；不对发现阶段施加应用层限流，采用批量（建议每批 25–50 个）资格化并遵循 IB pacing。
   - 采集阶段（Snapshot）：`exchange` / `fallback_exchanges` 为订阅首选与备用路由（默认 `SMART`，必要时回退 `CBOE`,`CBOEOPT`）。
   - `generic_ticks`：默认 `100,101,104,105,106,165,221,225,233,293,294,295`，务必覆盖 IV、Greeks、rtVolume。
   - `strikes_per_side`：围绕现价采样的行权价数（每侧 N 个）。
   - `subscription_timeout_sec` / `subscription_poll_interval`：单合约订阅超时与轮询间隔。
   - `require_greeks`：是否强制等待模型 Greeks；延迟/无权限时可设为 `false`。
   - CLI 可临时覆盖：`python -m opt_data.cli snapshot --exchange CBOE --fallback-exchanges CBOEOPT --strikes 2 --ticks 100,233 --timeout 15 --poll-interval 0.5`。
5. 配置 `.env` / 环境变量：
   - `IB_HOST`（默认 `127.0.0.1`；remote IB Gateway: `100.71.7.100`）
   - `IB_PORT`（默认 `4001`）
   - `IB_CLIENT_ID`（留空/未设时，按 `client_id_pool` 自动分配；默认范围：prod 0-99，remote 100-199，test 200-250；显式设置则固定使用该值）
   - `IB_MARKET_DATA_TYPE=1`（盘中默认实时；如需强制延迟改为 `3/4`）
   - **收盘快照**：运行前将 `IB_MARKET_DATA_TYPE=2`（盘后/回放模式），命令内部也会强制 `reqMarketDataType(2)` 以读取当日收盘数据
   - `TZ=America/New_York`（统一调度时区）
6. 生产/开发设备配置对照表（IB Gateway 连接）：

| 场景 | IB_HOST | IB_PORT | IB_CLIENT_ID | 配置位置 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 生产设备（本地 Gateway） | 127.0.0.1 | 4001 | 0-99（prod pool） | `config/opt-data.snapshot.local.toml` / 环境变量 | Gateway 在本机运行 |
| 开发设备（远程 Gateway） | 100.71.7.100 | 4001 | 100-199（remote pool） | `config/opt-data.snapshot.local.toml` / 环境变量 | 直连远端 |
| 开发设备（SSH 转发） | 127.0.0.1 | 4001 | 100-199（remote pool） | `config/opt-data.snapshot.local.toml` / 环境变量 | 通过 SSH 本地端口转发到远端 |
7. 配置文件准备：
   - **本地/生产配置**：`cp config/opt-data.toml config/opt-data.snapshot.local.toml`，在此文件中修改本地特定配置（如端口、路径），该文件已加入 `.gitignore`。
   - **测试配置**：`cp config/opt-data.toml config/opt-data.test.toml`，并将 `paths.raw/clean/state/contracts_cache/run_logs` 指向 `data_test/`、`state_test/`。
8. 核对核心配置：
   - `[acquisition] mode="snapshot"`、`market_data_type=1`（默认实时，enrichment 必需）、`allow_fallback_to_delayed=true`
   - `slot_grace_seconds=120`、`rate_limits.snapshot.per_minute=30`、`max_concurrent_snapshots=14`
   - `[discovery] policy="session_freeze"`、`pre_open_time="09:25"`；若启用增量刷新，设 `midday_refresh_enabled=true` 且仅新增合约，并依赖已存在的当日缓存（不刷新/重建已有合约，发现缺失需先修复缓存再开启增量）
   - `intraday_retain_days=60`、`weekly_compaction_enabled=true`、`same_day_compaction_enabled=false`
9. 确认交易日历（含早收盘）可用；调度器/cron 中必须显式设置 `America/New_York`。项目使用 `pandas-market-calendars` 获取 XNYS 会话时间：若运行环境缺少该依赖或无法访问历年日历，将自动回退到固定 09:30–16:00 槽位，并在日志标记 `early_close=False`。
10. **合约缓存预检与自动重建（新）**  
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
- **Console UI（Web 控制台）**：`streamlit run src/opt_data/dashboard/app.py`
  - **Overview**: 系统状态监控（快照速率、错误率、延迟分布）。
  - **Operations**: 生产操作面板（快照、Rollup、Enrichment）。
  - **History**: 日线历史数据获取与可视化（支持 8-hour bar 聚合）。
  - **注意**：Console UI 使用独立的 client ID (200-250 范围)，不会与 CLI 进程冲突；UI 操作为同步执行，长时间操作会阻塞界面

> 若 CLI 尚未提供对应子命令，可调用等价脚本；命令命名需与实现同步。

## MCP 只读分析接口（本地）
- 目的：为模型/排障提供只读查询层（不直连 IB、不写库）。可读范围：`data/clean`、`data/raw`、`state/run_logs`、`data/metrics.db`。
- 依赖安装（可选）：先完成仓库根目录 `requirements-dev.lock` 安装，再执行 `pip install -e '.[mcp]'`
- 启动（stdio 模式）：`python -m opt_data.cli mcp-server --config config/opt-data.snapshot.local.toml`
- 常用参数：`--allow-raw/--allow-clean`、`--audit-db <path>`、`--log-level INFO|DEBUG`
- 审计落地：默认 `state/run_logs/mcp_audit.db`
- 工具清单（MVP）：`health_overview`、`run_status_overview`、`list_recent_runs`、`get_partition_issues`、`get_chain_sample`
- 默认限制：`limit=200`（max 2000）、`days=3`（max 14）；`list_recent_runs` 默认 20/max 200；`get_chain_sample` max 1000
- 返回元信息：工具响应包含 `meta`（limit/clamped/source）

## 测试/验收（非生产）
- 本地测试目录冒烟与 QA 命令：`docs/dev/qa.md`。
- 实验脚本与开发调度说明：`docs/dev/ops-runbook-dev.md`。

## Close View 与 Universe（生产要点）
- 盘中 `snapshot`：默认写入 `view=intraday`（可用 `universe.intraday.csv` 精简清单）。
- 收盘 `close-snapshot`：写入 `view=close`（默认使用 `config/universe.csv` 全量清单）。
- `rollup`：默认优先读取 `view=close`；`allow_intraday_fallback=false` 时 close 缺失会失败（建议先补跑 `close-snapshot`）。
- 关键配置项：`[universe].file/intraday_file/close_file`、`[rollup].close_slot/fallback_slot/allow_intraday_fallback`。
- 详细设计与实现背景：`docs/architecture/dual-universe-implementation.md`。

## 调度与部署（生产）
- 推荐：直接在守护进程/终端常驻运行 `python -m opt_data.cli schedule --live --config config/opt-data.snapshot.local.toml`。
- 时间表（ET）：09:30–16:00 每 30 分钟 snapshot；17:30 close-snapshot → rollup；次日 04:30 enrichment；收盘后跑 `selfcheck/logscan`。
- 若需系统级守护：用 launchd/systemd 包装同一条命令，并在环境中设置 `TZ=America/New_York`、`IB_*` 与虚拟环境 `PATH`；日志指向 `state/run_logs/`。

## 限速与重试
- 令牌桶配置：当前生产（全量 `config/universe.csv`）运行 `rate_limits.snapshot.per_minute=30`、`max_concurrent_snapshots=14`；提高并发/分批调度（如 45/12 或更高）需额外评审与监控，当前暂缓。
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
 
> 开发侧的 IBKR 拉取 best practices 与 OI enrichment 路线图见 `docs/dev/ops-notes.md`。

## 恢复流程
1. 通过日志定位受影响的 `trade_date`、`slot_30m`、`underlying`。
2. 使用 `snapshot --slot` 或 `snapshot --replay-missed` 补采；重跑后确认 `(trade_date, sample_time, conid)` 无重复。
3. 重新执行 `rollup --date <trade_date>`；如需补全 OI，待 enrichment 成功后检查 `open_interest` 与 `data_quality_flag`。
4. 更新 QA 报告、`TODO.now.md`、`PLAN.md`，记录故障原因、处理步骤与残留风险。

## 扩容执行流程
> 当前生产已覆盖 `config/universe.csv` 全量且维持 30/14 限速；以下阶段划分用于未来提升并发/分批调度或出现回退需求时参考。
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

## 结构迁移（最小停机）
迁移步骤已整理为独立手册，见 `docs/ops/migration-minimal-downtime.md`。

## 例行维护
- **每日**：rollup 后执行 `python -m opt_data.cli qa --date <trade_date>`，校验槽位覆盖率、延迟行情、rollup 回退率与 OI 补齐率并写入 `metrics_YYYYMMDD.json`；如 FAIL 立即补救。监控指标与 `logscan` 摘要一并纳入告警。
- **每周**：运行 `make compact`，审阅 compaction 日志；确认 intraday 分区文件数下降、冷分区采用 ZSTD。
- **每月**：复核 `config/universe.csv` 与实际宇宙；评估是否扩容并调整限速。
- **持续**：监控磁盘占用与保留策略执行结果；定期备份 `config/`、`docs/`、`state/`。
- **监控**： teminal运行：ssh datareader@100.71.7.100

## 其他注意事项
- 调度命令需指定虚拟环境路径或使用 wrapper，避免系统 Python 与项目依赖冲突。
- 实时数据仅用于内部研究；若涉及再分发需提前评估许可限制。
- 任何配置调整必须在测试目录先跑完整闭环（snapshot + rollup + enrichment），再推广至正式环境。
- 敏感凭据禁止写入仓库，务必通过环境变量或受控文件管理。
 
## 深入参考（开发/诊断）
- IBKR 拉取 best practices、OI enrichment 优化路线图：`docs/dev/ops-notes.md`
- 双 Universe / close view 实现说明：`docs/architecture/dual-universe-implementation.md`
