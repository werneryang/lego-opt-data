# 文档目录（Docs Index）

本项目文档按用途分为：**生产运维**、**开发/实验**、**架构/决策**、**验收/报告**与**研究/历史资料**。

## 项目级（Project）
- 计划与阶段：`PLAN.md`
- 本周任务：`TODO.now.md`
- 采集范围与约定：`SCOPE.md`

## 生产运维（Ops）
- 阶段性总结（当前状态/命令/验收）：`docs/ops/project-summary.md`
- 值班/调度入口：`docs/ops/ops-runbook.md`
- 常见故障排查：`docs/ops/troubleshooting.md`
- 迁移与零停机手册：`docs/ops/migration-minimal-downtime.md`
- 历史数据（IBKR HMDS）说明：`docs/ops/ibkr-historical-data-guide.md`
- launchd 定时器模板：`docs/ops/launchd/com.legosmos.opt-data.timer.plist`

## 开发与实验（Dev）
- 开发文档入口：`docs/dev/README.md`
- 开发侧运维/实验 runbook：`docs/dev/ops-runbook-dev.md`
- 运维与采集补充说明（开发/诊断）：`docs/dev/ops-notes.md`
- 重试与日志实现/用法：`docs/dev/retry_and_logging_implementation.md`、`docs/dev/retry_usage_guide.md`
- 错误处理健壮性修复摘要：`docs/dev/error_handling_robustness_fixes.md`
- QA 自检与测试冒烟：`docs/dev/qa.md`
- Roadmap：`docs/dev/roadmap.md`

## 架构与决策（Architecture & ADR）
- 数据契约（字段/分区/主键）：`docs/architecture/data-contract.md`
- 双 Universe / close view 实现说明：`docs/architecture/dual-universe-implementation.md`
- 存储 ADR：`docs/adr/ADR-0001-storage.md`
- 并发/批处理 ADR：`docs/adr/ADR-0002-SPY-snapshot-batch-concurrency.md`

## 变更记录（Changelog）
- 变更归档目录：`docs/changelog/`
- 近期收尾记录：`docs/changelog/2025-12-13.md`

## 本地归档（Local Only）
- 研究与报告类资料已移出仓库，仅保留在本地目录：`docs/research/`、`docs/reports/`。
