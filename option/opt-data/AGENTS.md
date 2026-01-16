# AGENTS.md

## 角色定位
- **Codex/智能体**：作为协作型开发者，负责实现期权链数据采集、清洗与调度相关任务。
- **项目所有者**：定义业务目标、批准范围调整、提供 IBKR/TWS 接入凭据与运营决策。
- **协作原则**：保持双向沟通透明；重要假设需在实现前确认；所有代码需通过自动化检查后提交。

## 沟通与任务管理
- 跨项目规则见根 `AGENTS.md`。
- 所有需求、范围、优先级变化需在 `TODO.now.md` 与 `PLAN.md` 中同步。
- 发现阻塞、风险、外部依赖（如 IB 限速、权限）时，需即时反馈。
- 对于超过 1 天的任务，先拆分为可验证子任务，并在 PR 或合并说明中记录。

## 代码与数据规范
- Python 3.10+，遵循 `pyproject.toml` 中的 Ruff/pytest 配置，默认启用类型标注与 `from __future__ import annotations`。
- 依赖锁定：以仓库根目录 `requirements.lock` / `requirements-dev.lock` 为唯一依赖来源；变更 `pyproject.toml` 后必须运行根目录 `make lock` 并提交锁文件。
- 模块布局：`src/opt_data/ib`、`pipeline`、`storage`、`cli`、`config` 等子包，测试放在 `tests/`，使用 `pytest`。
- 禁止将真实凭据、原始敏感数据写入仓库；本地 `.env`、`config/opt-data.snapshot.local.toml`、`config/opt-data.streaming.local.toml` 由 `.gitignore` 保护。
- 数据输出区分：`data/raw` 保存 IB 原样数据；`data/clean` 保存清洗与公司行动调整后的 Parquet 数据。

- IBKR 接入规范：统一使用 `ib_insync` 封装进行会话、订约与行情订阅；禁止在项目代码中直接依赖或导入 `ibapi.*`。如需底层特性，请通过 `ib_insync` 的 `IB.client` 暴露接口封装为内部工具后再使用。
 
 - 合约发现（2025 升级要求）：
   - 仅使用 `reqSecDefOptParams()` 获取到期与行权价（限制为 `exchange='SMART'`）。
   - 直接构造 `Option(...)` 集合并使用批量 `qualifyContracts/qualifyContractsAsync` 获取 `conId`。
   - 不得在发现阶段调用 `reqContractDetails`；不得在发现阶段施加应用层限流（改为批量资格化并遵循 IB pacing）。

- IB 连接默认值：`host=127.0.0.1`、`port=4001`，`clientId` 默认按角色池自动分配（prod 0-99，remote 100-199，test 200-250；如需固定可显式指定）。
- 运行环境：Python 3.11；开发时执行 `python3.11 -m venv .venv && pip install -r ../../requirements-dev.lock && pip install -e . --no-deps`（或从仓库根目录 `make install`）。
- 采集窗口：S&P 500 成分股（以 `config/universe.csv` 为准），行权价带 ±30%，标准月度/季度合约。
- 调度基于 `America/New_York` 时区：17:30 ET `close-snapshot` → `rollup`，次日 04:30 ET `enrichment`；盘中 09:30–16:00 每 30 分钟 `snapshot`。
- 当前 Stage 1（AAPL+MSFT）生产限速为 `snapshot per_minute=30`、`max_concurrent_snapshots=14`（45/12 为后续调优目标）。
- 存储：Parquet 分区 `date/underlying/exchange`，热数据（默认 14 天）使用 Snappy，冷数据使用 ZSTD；周度合并。

## 目录结构（摘要）
```
/                   # 仓库根目录
├─ AGENTS.md        # 协作规范
├─ PLAN.md          # 四周计划与范围
├─ TODO.now.md      # 当周/当日任务
├─ SCOPE.md         # 采集范围与字段约定
├─ docs/            # ADR、数据契约、运维手册（生产 + 开发）
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
4. 在执行大规模回填前，复制配置到测试目录（如 `config/opt-data.test.toml`），对 AAPL/MSFT 进行冒烟验证，确认输出完整后再切换正式目录。
5. 文档分类与更新：
   - 生产运维与正式流程：更新 `docs/ops/ops-runbook.md` 及相关正式方案文档（研究材料本地归档，不纳入仓库）。
   - 开发/测试与实验脚本：更新 `docs/dev/` 下文档（如 `docs/dev/ops-runbook-dev.md`），以及相关 ADR 中的“实验性/仅限 data_test”说明。
   - 文档双向同步：更新项目文档时，需同步维护 `.agent/` 下的对应规则/摘要；同理，更新 `.agent/` 内规则时需回写到正式文档或目录（如 `docs/`、`SCOPE.md` 等）以保持一致。
6. 部署 → 按 `docs/ops/ops-runbook.md` 操作，并记录结果或问题。

附注：拉取 IBKR 期权链时，优先遵循以下文档与清单：
- docs/ops/ops-runbook.md 中“IBKR 期权链拉取最佳实践（AAPL/SPX）”
- SCOPE.md 中“期权链拉取简要清单（优先实践）”

## 审核与验收
- 代码合并需 CI 通过、至少一次评审；关键路径变更需额外回归测试或数据抽样验证。
- 数据落地需验证分区完整性、主键唯一性、关键字段非空率，并记录于运行日志。
- 若外部依赖变更（IBKR API、S&P500 成分等），需更新 `SCOPE.md` 并在 `PLAN.md` 标记改动范围。

## AI 任务执行优化
- **Claude**: 在处理期权 Greeks 计算或复杂的异步采集逻辑时，要求其先输出 `<thinking>` 链。
- **Gemini**: 任务涉及配置项扩展或跨模块重构时，要求其扫描 `src/opt_data/config.py` 与各 pipeline 模块的关联。
- **GPT**: 适合用于编写单元测试用例和优化 CLI 工具的错误提示。
