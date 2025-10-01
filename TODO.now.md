# 本周任务（滚动更新）

## 待办
- [ ] 完成 IB 基础连接联调（本地 Gateway）
- [ ] 清洗流水线与公司行动调整模块占位与实现
- [ ] 小规模端到端集成测试（AAPL/MSFT 回填一日，真实 IB 接入）
- [ ] 根据运行结果更新 `docs/ops-runbook.md` 与 `PLAN.md`

## 进行中
- IB 会话连接测试（需要本地 Gateway/权限）

## 阻塞
- [ ] `make test` 依赖本地虚拟环境（运行 `make install` 后重试）

## 阻塞
- （空）

## Done 2025-09-26
- [x] 依赖入库（pyproject：pandas/pyarrow/typer/ib-insync/APScheduler/dotenv/pmc）
- [x] 配置与 CLI 雏形（`src/opt_data/config.py`, `src/opt_data/cli.py`）
- [x] IB 会话与合约发现缓存接口（`ib/session.py`, `ib/discovery.py` 占位）
- [x] 工具模块：限速器/日历/队列（`util/ratelimit.py`, `util/calendar.py`, `util/queue.py`）
- [x] 存储：分区与写入（`storage/layout.py`, `storage/writer.py`），冷热压缩策略
- [x] 单元测试：配置加载、分区路径与编解码策略、限速器（`tests/*`）
- [x] 到期过滤工具与合约筛选（`util/expiry.py`, `ib/discovery.filter_by_scope`）
- [x] Universe 加载与回填计划队列（`universe.py`, `pipeline/backfill.py`, CLI backfill 集成）
- [x] 新增单测：到期过滤、Universe 解析、回填队列生成（`tests/test_expiry.py`, `tests/test_universe.py`, `tests/test_backfill_planner.py`）
- [x] IB 合约发现实现（`ib/discovery.discover_contracts_for_symbol`），含缓存与过滤
- [x] 回填执行器骨架写入 raw 数据（`pipeline/backfill.BackfillRunner`，CLI `backfill --execute`）
- [x] 新增单测：合约发现缓存、BackfillRunner 写入 parquet（`tests/test_discovery.py`, `tests/test_backfill_runner.py`）
