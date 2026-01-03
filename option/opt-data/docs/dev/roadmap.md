# Roadmap & Future Work

**最后更新**: 2025-11-27  
**说明**: 本文档用于整理已讨论的后续改进方向，按时间优先级和主题分组。  
真正的「当前计划 / 执行中的任务」仍以根目录的 `PLAN.md` 与 `TODO.now.md` 为准。

## 优先级分层（Phase 0–3）

- **Phase 0 · 立即可做（NOW）**  
  - 已进入 `TODO.now.md` 的具体任务，不在本文件重复维护；以当周/当前冲刺为准。
- **Phase 1 · 短期（SHORT，1–2 周）**  
  - 对应本文件中「短期改进」章节的条目，视为随时可以拉入下一轮 `TODO.now.md` 的候选。
- **Phase 2 · 中期（MID，1–2 个月）**  
  - 对应「中期改进」章节，通常需要跨模块设计或验证，进入 `PLAN.md` 某一里程碑后再拆分。
- **Phase 3 · 观望（WATCH，3–6 个月 / 探索）」**  
  - 对应「长期改进」章节，属于方向性或探索性工作，实施前需结合实际需求和成本再评估。

> 使用约定：  
> - 立即要做的事项先写入 `PLAN.md` 与 `TODO.now.md`（Phase 0），roadmap 只保留 Phase 1–3。  
> - 当某个短期/中期/观望项被正式排期时，应在 `PLAN.md` 标记阶段，并在 `TODO.now.md` 中拆分为可执行任务。

---

## 🎯 短期改进（1–2 周 · Phase 1 / SHORT）

短期项优先围绕「清理与优化」「测试覆盖增强」「性能与资源使用」三块，尽量能在 1–2 个迭代内完成并产生可观测收益。

### 1. 清理与优化

- [ ] 清理 `src/opt_data/pipeline/rollup.py` 中临时添加的调试日志，将需要保留的信息转为结构化日志或指标（如适用）。
- [ ] 对近期新增模块（如 `observability/*`、`dashboard/app.py`、错误处理与重试工具）做一轮边缘情况代码审查，补充必要的保护逻辑或 TODO 标记。
- [ ] 更新根目录 `README.md`：
  - 补充 Snapshot → Rollup → Enrichment 的端到端使用示例（当前已有基础示例，可加上自检/监控提示）。
  - 简要说明错误处理、自检（`selfcheck`）、日志扫描（`logscan`）与 QA 指标输出位置。
- [ ] 在 `docs/dev/retry_usage_guide.md` 中补充与 IB 相关的重试使用示例（如 discovery、snapshot、rollup），并与实现保持一致。
- [ ] 视需要在 `docs/ops/troubleshooting.md` 中追加与 snapshot/rollup 新错误场景相关的排查条目。

### 2. 测试覆盖增强

- [ ] 修复 `tests/test_snapshot_error_handling.py::TestSnapshotErrorHandling::test_subscription_failure_scenario` 中的 mock/异步行为问题，使其在本地与 CI 中稳定通过。
- [ ] 增加端到端快照采集集成测试（基于 `config/opt-data.test.toml`，在 `data_test/` 与 `state_test/` 上运行 snapshot → rollup → enrichment），验证最基本的日链路。
- [ ] 为 rollup 管道添加边界条件测试（缺列、空分区、有错误行时的行为），确保对 legacy/异常数据具有向后兼容性或明确失败路径。
- [ ] 增加「错误行在管道中的流转」测试：构造带 `snapshot_error=True` 的 intraday 样本，验证 rollup/enrichment 对错误行的过滤或标记行为符合预期。
- [ ] 设计一套基础压力测试脚本（可放在 `scripts/`），用于本地手动评估高负载下的重试机制、限速配置与内存占用（暂不纳入 CI）。

### 3. 性能与内存优化（探索性）

- [ ] 调研并设计 `src/opt_data/ib/discovery.py` 中合约资格校验（`qualifyContracts*`）的批处理优化方案，减少 round-trip 次数和单次请求体量。
- [ ] 评估并优化合约缓存的读写路径与 key 设计（`state/` 下缓存文件），在保证幂等和可审计的前提下降低重复 IO。
- [ ] 对 snapshot/rollup 过程中的大 DataFrame 做一次内存占用 profiling，结合 `optimize_dataframe_dtypes` 等工具形成优化建议（必要时再实施改动）。

---

## 🚀 中期改进（1–2 个月 · Phase 2 / MID）

中期项侧重「可观测性」「数据质量」「调度与自动化」，通常需要跨多个模块调整，适合按专题设计与实施。

### 4. 可观测性提升

- [ ] 在现有 `MetricsCollector`（SQLite）基础上，评估是否需要引入 Prometheus 客户端或导出器，将延迟、错误率、吞吐量等关键指标暴露给外部监控系统。
- [ ] 为关键操作统一命名指标：如 `snapshot.fetch.*`、`rollup.run.*`、`enrichment.run.*`、`discovery.*`，并在 pipeline 中一致使用。
- [ ] 评估使用 OpenTelemetry 做跨模块链路追踪的可行性（可参考 `docs/dev/retry_and_logging_implementation.md` 中的「未来规划」条目），包括 trace id 传递与采样策略。
- [ ] 为日志输出增加结构化 JSON Lines 格式的可选开关，以便后续接入 ELK/Loki 等日志聚合与分析系统。
- [ ] 根据监控与日志实践，更新 `docs/ops/ops-runbook.md`，补充常见指标解释与告警处理流程。

### 5. 数据质量改进

- [ ] 引入数据 schema 校验框架（如 Pandera/Pydantic），在 snapshot → rollup → enrichment 各环节增加轻量 schema 校验（不阻塞主流程，但可输出 QA 报告）。
- [ ] 将核心数据质量检查（IV/Greeks 合理范围、价格异常、缺失字段占比等）标准化，并统一写入 QA 报告与 `selfcheck` 结果。
- [ ] 设计简单的规则或统计型异常检测逻辑，用于标记极端价格/Greeks 值，并与 `data_quality_flag` 体系打通（后续可升级为 ML 模型）。
- [ ] 为 T+1 OI enrichment 与其他慢字段补全定义更完整的质量指标与 SLA，并在 `PLAN.md`/`SCOPE.md` 中确认。

### 6. 调度与自动化

- [ ] 扩展 `opt_data.cli schedule` 与内部调度层，支持更灵活的调度策略（如标的分组、错峰执行、不同 view 的独立调度）。
- [ ] 在调度层增加任务依赖管理：明确 snapshot → rollup → enrichment → QA/selfcheck → logscan 的依赖关系和失败回退策略。
- [ ] 为调度任务增加失败自动重试配置（重试次数、间隔、上限），并记录到运行日志与指标中。
- [ ] 设计并实现通知机制（如 Slack/Webhook/Email 抽象接口），在关键错误、自检 FAIL 或指标越阈值时发送告警；具体通道实现可按运行环境逐步落地。
- [ ] 为每日数据采集与 QA 结果生成汇总报告（JSON/Markdown），便于人工审阅与归档。

---

## 🏗️ 长期改进（3–6 个月 · Phase 3 / WATCH）

长期项多为架构/能力层面的升级，需要结合实际需求、运维成本与团队节奏逐步评估，不一定全部实施。

### 7. 架构优化与扩展

- [ ] 评估引入 Kafka/Pulsar 等消息系统的成本与收益，将 Snapshot → Rollup → Enrichment 拆解为事件驱动流水线，以支持更大规模标的与实时消费需求。
- [ ] 探索使用 Dask/Ray 等分布式计算框架，对合约发现、快照清洗、日终聚合等阶段进行并行化，以支持多节点横向扩展。
- [ ] 设计并实现将清洗/调整后的数据导入 DuckDB/ClickHouse 等分析引擎的方案，支持下游复杂分析查询与交互式探索。

### 8. ML/AI 能力增强（探索）

- [ ] 研究在 Greeks 缺失时使用 ML 模型进行近似估计的可行性，严格区分「模型推断」与「真实行情」并做风险提示。
- [ ] 设计并训练异常检测模型（基于历史快照与日终数据），自动识别价格/Greeks 异常并生成告警或标记。
- [ ] 探索隐含波动率曲面建模、期权流动性分析等高阶分析能力，为后续量化研究或监控提供输入。

### 9. 用户界面与对外接口

- [ ] 在现有 Streamlit Dashboard（`src/opt_data/dashboard/app.py`）基础上，进一步丰富可视化内容：槽位覆盖率、延迟行情占比、rollup 回退率、缺 OI 补齐率等。
- [ ] 评估是否需要一个更正式的 Web Dashboard 或运维控制台（权限控制、任务重跑、在线配置查看等）。
- [ ] 设计 REST/GraphQL 等 API 层，向其他系统提供已清洗/调整数据的标准化访问接口（取决于下游集成需求）。

---

## 与现有文档的关系

- 本文档用于收集「已讨论的改进方向」，其中部分项可能尚未被批准或排期。  
- 一旦某个改进方向被纳入近期计划，应：
  - 在 `PLAN.md` 中更新对应阶段/周的范围与目标；
  - 在 `TODO.now.md` 中拆分为具体可执行的任务项（含验收标准）。  
- 重要架构或范围调整建议通过 ADR（例如 `docs/adr/ADR-0001-storage.md` 的方式）记录决策过程与取舍。
