# UI 设计规范

- **平台与入口**: 仅维护 Streamlit 控制台 `src/opt_data/dashboard/app.py`，宽屏布局、标题 “Opt-Data Dashboard”。启动命令 `streamlit run src/opt_data/dashboard/app.py`（或 `.venv/bin/…`），依赖 `OPT_DATA_METRICS_DB`（默认 `data/metrics.db`）与 `OPT_DATA_CONFIG`。
- **数据来源**: 指标从 SQLite `metrics` 表读取；错误/状态从 `state/run_logs/`；链路数据从 Parquet 分区（通过 `pyarrow.dataset`，ET/UTC 字段按契约展示）。新增视图需复用同样的数据契约与分区路径。
- **交互约束**: UI 操作为同步执行，长任务会阻塞界面；后台跑批仍由 CLI/调度器负责。为避免与 CLI 冲突，UI 使用独立 IB clientId（200–250 范围，见运维手册）。
- **缓存与性能**: 读取磁盘/DB 时使用 `st.cache_data`（现有 TTL：指标 10–60s）；图表采用 Altair，表格用 `st.dataframe`。新增查询需控制加载范围（按日期/标的过滤）以免大分区爆内存。
- **一致性与风格**: 遵循现有分栏/标签结构（Overview 展示指标与趋势，Console 提供控制与日志浏览）；统一使用项目配置/日历逻辑（ET 时区、槽位定义），不要在 UI 硬编码凭据或路径。
- **安全与审计**: 不在前端暴露真实凭据或未清洗数据；所有操作应写日志/指标（沿用 `state/run_logs`、metrics 模式），与 CLI 行为保持一致以便审计。

