# 运维手册：调度、限速与故障恢复

## 运行前准备
1. 启动 IB Gateway/TWS，确认登录账户具有美股期权实时或延迟行情权限。
2. 确保 `.env`（或环境变量）配置以下变量：
   - `IB_HOST`（默认 `127.0.0.1`）
   - `IB_PORT`（默认 `7497` / 纸面账户，真账户为 `7496`）
   - `IB_CLIENT_ID`（默认 `101`）
   - `IB_MARKET_DATA_TYPE`（`1=实时`, `2=冻结`, `3=延迟`, `4=延迟冻结`）
3. 根据需要更新 `config/opt-data.toml` 中的限速、并发、路径与调度窗口。

## 常用命令
- `make install`：创建/更新虚拟环境并安装依赖。
- `make fmt lint test`：代码风格、静态检查、测试。
- `make backfill START=2024-10-01 SYMBOLS=AAPL,MSFT`：执行回填任务。
- `make update`：执行当天 17:00 ET 日更任务（需保证交易日时间）。
- `make compact DAYS=14`：对超过指定天数的分区执行合并与压缩转换。

## 调度配置
### macOS（开发环境）
1. 生成 `plist` 文件（模板参考 `docs/templates/launchd-opt-data.plist` 若后续添加）。
2. 调整执行路径、环境变量。
3. 使用 `launchctl load -w <plist>` 注册。

### Linux（生产环境）
1. 创建 `systemd` 服务与定时器（模板将在开发完成后添加至 `docs/`）。
2. 单元示例：
   - `opt-data.service` 调用 `make update`。
   - `opt-data.timer` 设定 `OnCalendar=Mon-Fri 22:00`（UTC）。
3. 使用 `systemctl daemon-reload && systemctl enable --now opt-data.timer`。

## 限速与重试
- 速率控制采用令牌桶机制，配置项包括：
  - `rate_limits.discovery.per_minute`
  - `rate_limits.snapshot.per_minute`
  - `rate_limits.historical.per_minute`
  - `max_concurrent_snapshots`
- 触发 IB pacing violation：
  - 首次等待 30 秒，随后指数退避（60s、120s...），记录在 `state/run_logs/`。
  - 若连续 3 次失败，任务进入“待人工处理”队列。

## 故障处理
| 情况 | 诊断步骤 | 解决方案 |
| --- | --- | --- |
| IB 连接失败 | 检查 Gateway/TWS 状态；确认端口、Client ID 是否冲突 | 重启 IB Gateway，释放旧 session；调整 Client ID |
| 数据缺失（OI/Greeks） | 查看运行日志 `state/run_logs/`，确认是否为权限或延迟行情 | 重跑当日补采任务；若权限不足需联络 IBKR |
| 分区写入失败 | 查阅 `state/backfill_progress.parquet`，确认断点 | 清理部分临时文件后重跑对应 symbol/date |
| 周度合并失败 | 查看合并日志；确定是否文件锁冲突 | 手动调用 `make compact` 重试；必要时拆分分区运行 |
| 调度未执行 | 查看调度器日志（launchd/systemd） | 修正时区或 Holiday 过滤；手动补跑一次 |

## 恢复流程
1. 根据日志定位失败的 symbol/date。
2. 调用 `opt-data backfill --start <date> --symbols <list>` 或 `opt-data update --date <date>` 进行补跑。
3. 重跑后检查数据目录分区是否新增，校验 QA 指标（记录缺失率、行数）。
4. 更新 `TODO.now.md` 与 `PLAN.md`，说明故障原因与处理方式。

## 例行维护
- 每周检查 `data/raw` 与 `data/clean` 的分区数量、文件大小，确保合并生效。
- 月度验证 `config/universe.csv` 是否与最新 S&P 500 成分一致。
- 定期备份 `config/`、`docs/`、`state/` 目录，防止操作失误导致模板/日志丢失。

## 其他注意事项
- 所有运行命令默认在虚拟环境激活后执行。
- 若切换到真实账户，需评估 IBKR 成本与权限文件，并在 `SCOPE.md` 留存记录。
- 敏感配置必须通过环境变量或本地未提交文件管理。
