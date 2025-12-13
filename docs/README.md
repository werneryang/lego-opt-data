# 文档目录（Docs Index）

本项目文档按用途分为：**生产运维**、**测试/验收**、**开发说明**、**数据契约/存储设计**与**研究/历史资料**。

## 项目级（Project）
- 计划与阶段：`PLAN.md`
- 本周任务：`TODO.now.md`
- 采集范围与约定：`SCOPE.md`

## 生产运维（Production）
- 阶段性总结（当前状态/命令/验收）：`docs/project-summary.md`
- 值班/调度入口：`docs/ops-runbook.md`
- 常见故障排查：`docs/troubleshooting.md`
- 历史数据（IBKR HMDS）说明：`docs/ibkr-historical-data-guide.md`

## 测试与验收（QA/Test）
- QA 自检与测试冒烟：`docs/dev/qa.md`
- 错误处理验证指南/报告：`docs/error-handling-verification-guide.md`、`docs/error-handling-verification-report.md`

## 开发与实验（Dev）
- 开发文档入口：`docs/dev/README.md`
- 开发侧运维/实验 runbook：`docs/dev/ops-runbook-dev.md`
- 运维与采集补充说明（开发/诊断）：`docs/dev/ops-notes.md`
- 双 Universe / close view 实现说明：`docs/dual-universe-implementation.md`
- 重试与日志实现/用法：`docs/dev/retry_and_logging_implementation.md`、`docs/dev/retry_usage_guide.md`
- 错误处理健壮性修复摘要：`docs/dev/error_handling_robustness_fixes.md`
- Roadmap：`docs/dev/roadmap.md`

## 数据契约与设计（Contracts & ADR）
- 数据契约（字段/分区/主键）：`docs/data-contract.md`
- 存储 ADR：`docs/ADR-0001-storage.md`
- 并发/批处理 ADR：`docs/ADR-0002-SPY-snapshot-batch-concurrency.md`

## 变更记录（Changelog）
- 变更归档目录：`docs/changelog/`
- 近期收尾记录：`docs/changelog/2025-12-13.md`

## 研究/历史资料（Legacy / Research）
> 以下文档多为方案演进过程中的记录，可能与当前 Snapshot+Rollup 架构存在差异；生产以 `docs/ops-runbook.md` 为准。

- `docs/基于 ib_insync 的TWS 期权链数据拉取正式方案.md`
- `docs/基于 ib_insync 的 TWS 期权链数据拉取方案（增强版）.md`
- `docs/基于Python的IB TWS API期权链数据拉取方案分析.md`
- `docs/基于 ib_insync 的 TWS 历史数据模块设计文档.md`
- `docs/IB TWS API 数据拉取策略研究 - Google Docs.html`
- `docs/ui_optimization_report.md`
- `docs/周末可以先做.md`
