# 本周任务（滚动更新）

## 待办
- [ ] 完成 IB 基础连接联调（本地 Gateway）
- [ ] 实现期权合约发现逻辑（±30% 与月度/季度过滤），写入缓存
- [ ] 清洗流水线与公司行动调整模块占位与实现
- [ ] 小规模端到端集成测试（AAPL/MSFT 回填一日）
- [ ] 根据运行结果更新 `docs/ops-runbook.md` 与 `PLAN.md`

## 进行中
- IB 会话连接测试（需要本地 Gateway/权限）

## 阻塞
- （空）

## Done 2025-09-26
- [x] 依赖入库（pyproject：pandas/pyarrow/typer/ib-insync/APScheduler/dotenv/pmc）
- [x] 配置与 CLI 雏形（`src/opt_data/config.py`, `src/opt_data/cli.py`）
- [x] IB 会话与合约发现缓存接口（`ib/session.py`, `ib/discovery.py` 占位）
- [x] 工具模块：限速器/日历/队列（`util/ratelimit.py`, `util/calendar.py`, `util/queue.py`）
- [x] 存储：分区与写入（`storage/layout.py`, `storage/writer.py`），冷热压缩策略
- [x] 单元测试：配置加载、分区路径与编解码策略、限速器（`tests/*`）
