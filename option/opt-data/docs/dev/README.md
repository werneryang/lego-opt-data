# Developer Documentation

This directory (`docs/dev/`) contains technical documentation for developers working on the `opt-data` project.

Documents here主要面向**开发/测试与实验性工作流**，包括：
- data_test/ 下脚本的使用说明与调优经验；
- 非生产配置（如 `config/opt-data.test.toml`）的运行说明；
- 错误处理验证、重试机制等内部实现与 QA 报告。

生产运维与正式调度流程请以 `docs/ops/ops-runbook.md` 及相关正式方案文档为准。

## Available Guides

### Implementation Documentation
- **[Retry and Logging Implementation](./retry_and_logging_implementation.md)** - Detailed technical documentation of the retry mechanism and logging enhancements
- **[Error Handling Robustness Fixes](./error_handling_robustness_fixes.md)** - Summary of error handling improvements and bug fixes
- **[Ops Notes (Dev/Diagnostics)](./ops-notes.md)** - IBKR best practices and enrichment roadmap (non-production)

### Usage Guides
- **[Retry Mechanism Usage Guide](./retry_usage_guide.md)** - How to use the `@retry_with_backoff` decorator effectively
- **[QA & Smoke Tests](./qa.md)** - Daily selfcheck/logscan usage and test smoke procedures
- **[Dev Ops Runbook](./ops-runbook-dev.md)** - data_test scripts and dev-only operational workflow
- **[Weekend History Backfill (Experimental)](./history-weekend-backfill.md)** - Batch-pull IBKR option historical bars using contracts cache (dev-only)

## Additional Resources

- [Troubleshooting Guide](../troubleshooting.md) - Common issues and solutions
- [Docs Index](../README.md) - High-level documentation navigation

- [Error Handling Verification Guide](../error-handling-verification-guide.md) - Guide on how to verify error handling capabilities.
- [Error Handling Verification Report](../error-handling-verification-report.md) - Verification results from 2025-11-26.

---

*最后更新: 2025-12-13*
