# 测试与安全

- **基本流程**: 开发遵循 `.agent/workflows/development_cycle.md`；需求变更同步 `TODO.now.md`/`PLAN.md`。提交前运行 `make fmt lint test`（或 `make qa`），环境基于 Python 3.11 venv，依赖按 `pip install -e .[dev]` 安装。
- **隔离环境**: 冒烟/回归优先使用测试配置 `config/opt-data.test.toml` 指向 `data_test/`、`state_test/`，以 AAPL/MSFT 闭环验证 snapshot → rollup → enrichment；生产配置前先在测试目录完成同样流程。
- **专项验证**: 错误处理用 `python scripts/test_error_scenarios.py --scenario all`；下游容错用 `python scripts/test_error_row_downstream.py`；ops 日常 QA 使用 `python -m opt_data.cli qa --date <trade_date>` 和 `python -m opt_data.cli logscan --date <trade_date> --write-summary`。
- **数据与合同约束**: 绝不将凭据或原始敏感数据入库；按数据契约保持主键唯一、必填字段完整、IV/Greeks 合理范围，槽位覆盖率≥90%。延迟/缺失/回退必须写入 `data_quality_flag`，错误行保留但标记 `snapshot_error`。
- **IB 安全与限速**: 统一用 `ib_insync`（禁止直接 `ibapi`），默认 `IB_HOST=127.0.0.1`, `IB_PORT=7496`, `IB_CLIENT_ID=101`，市场数据类型与权限在测试前确认。遵循 pacing：snapshot 30 req/min + 并发 10（可调）；发现阶段依赖 IB pacing 不自限。
- **回归与发布**: 扩容或大规模回填前复制配置到测试目录验证，通过后再切换正式目录；生产故障/告警需在 QA 报告与日志中留痕，并更新 `TODO.now.md` 跟踪。每日/每周执行保留与压缩任务时检查 `state/run_logs/compaction_*`。

