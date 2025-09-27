# AGENTS.md

## 角色定位
- **Codex/智能体**：作为协作型开发者，负责实现期权链数据采集、清洗与调度相关任务。
- **项目所有者**：定义业务目标、批准范围调整、提供 IBKR/TWS 接入凭据与运营决策。
- **协作原则**：保持双向沟通透明；重要假设需在实现前确认；所有代码需通过自动化检查后提交。

## 沟通与任务管理
- 所有需求、范围、优先级变化需在 `TODO.now.md` 与 `PLAN.md` 中同步。
- 发现阻塞、风险、外部依赖（如 IB 限速、权限）时，需即时反馈。
- 对于超过 1 天的任务，先拆分为可验证子任务，并在 PR 或合并说明中记录。

## 代码与数据规范
- Python 3.10+，遵循 `pyproject.toml` 中的 Ruff/pytest 配置，默认启用类型标注与 `from __future__ import annotations`。
- 模块布局：`src/opt_data/ib`、`pipeline`、`storage`、`cli`、`config` 等子包，测试放在 `tests/`，使用 `pytest`。
- 禁止将真实凭据、原始敏感数据写入仓库；本地 `.env` 与 `config/opt-data.local.toml` 由 `.gitignore` 保护。
- 数据输出区分：`data/raw` 保存 IB 原样数据；`data/clean` 保存清洗与公司行动调整后的 Parquet 数据。

## 默认配置与约束
- IB 连接默认值：`host=127.0.0.1`、`port=7497`（Paper）、`clientId=101`。
- 采集窗口：S&P 500 成分股（以 `config/universe.csv` 为准），行权价带 ±30%，标准月度/季度合约。
- 调度基于 `America/New_York` 时区，交易日 17:00 ET 运行每日更新。
- 存储：Parquet 分区 `date/underlying/exchange`，热数据（默认 14 天）使用 Snappy，冷数据使用 ZSTD；周度合并。

## 目录结构（摘要）
```
/                   # 仓库根目录
├─ AGENTS.md        # 协作规范
├─ PLAN.md          # 四周计划与范围
├─ TODO.now.md      # 当周/当日任务
├─ SCOPE.md         # 采集范围与字段约定
├─ docs/            # ADR、数据契约、运维手册
├─ config/          # 配置模板、标的清单
├─ data/            # 数据输出（受 .gitignore 控制）
├─ state/           # 运行状态、检查点
├─ src/             # 代码
└─ tests/           # 自动化测试
```

## 工作流程
1. 新需求 → 更新 `TODO.now.md` 并与 `PLAN.md` 对齐。
2. 设计决策 → 在 `docs/ADR-xxxx.md` 或 `SCOPE.md` 记录。
3. 开发 → 遵循模块化结构，提交前运行 `make fmt lint test`。
4. 数据/调度变更 → 更新 `docs/ops-runbook.md` 与配置模板。
5. 部署 → 按 `docs/ops-runbook.md` 操作，并记录结果或问题。

## 审核与验收
- 代码合并需 CI 通过、至少一次评审；关键路径变更需额外回归测试或数据抽样验证。
- 数据落地需验证分区完整性、主键唯一性、关键字段非空率，并记录于运行日志。
- 若外部依赖变更（IBKR API、S&P500 成分等），需更新 `SCOPE.md` 并在 `PLAN.md` 标记改动范围。
