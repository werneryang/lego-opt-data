# Dual Universe Snapshot Configuration - Implementation Summary

**Date**: 2025-12-04  
**Status**: ✅ Complete

---

## Executive Summary

成功实现了双 Universe 配置和 Close View 独立存储路径，将盘中快照与收盘快照的 symbol 清单和存储路径分离，优化 API 负载并提高数据管理效率。

---

## Task Plan

### Phase 1: 盘中/收盘清单分离

#### Planning
- [x] Analyze current storage and rollup implementation
- [x] Create implementation plan
- [x] Get user approval

#### Execution
- [x] Config extension
  - [x] Add `intraday_file` and `close_file` to `UniverseConfig`
  - [x] Update `load_config()` to parse new fields
  - [x] Update TOML templates

- [x] SnapshotRunner changes
  - [x] Add `universe_path` parameter to `run()`
  - [x] Add `ingest_run_type` parameter to `run()` and `_enrich_rows()`

- [x] CLI changes
  - [x] Update `snapshot` with `--universe` option (defaults to intraday_file)
  - [x] Update `close-snapshot` with `--universe` option (defaults to file)

### Phase 2: Close View 和 Rollup 优先级

#### Execution
- [x] Config extension
  - [x] Add `RollupConfig` dataclass with `allow_intraday_fallback`
  - [x] Update `load_config()` for new rollup section
  - [x] Update TOML templates

- [x] SnapshotRunner changes
  - [x] Add `view` parameter to `run()` (default: "intraday")
  - [x] Parameterize write paths based on view

- [x] CLI changes
  - [x] Update `close-snapshot` to pass `view="close"`

- [x] Rollup changes
  - [x] Add `_load_close()` method to read from `view=close`
  - [x] Update `run()` to prioritize close, fallback to intraday if allowed
  - [x] Add `fallback_intraday` flag to data_quality_flag

#### Documentation (Pending)
- [ ] Update `docs/ops-runbook.md` with close view section
- [ ] Update `SCOPE.md` with dual list explanation

#### Verification
- [x] Run existing tests (14 passed)
- [ ] Manual verification of view paths

---

## Walkthrough: Modified Files

### Phase 1: 盘中/收盘清单分离

| 文件 | 改动 |
|------|------|
| `src/opt_data/config.py` | `UniverseConfig` 增加 `intraday_file`, `close_file` |
| `config/opt-data.toml` | 新增 `intraday_file`, `close_file` 配置项 |
| `src/opt_data/pipeline/snapshot.py` | `run()` 增加 `universe_path`, `ingest_run_type` |
| `src/opt_data/cli.py` | `snapshot`/`close-snapshot` 增加 `--universe` |

### Phase 2: 独立 Close View 和 Rollup 优先级

| 文件 | 改动 |
|------|------|
| `src/opt_data/config.py` | 新增 `RollupConfig` dataclass |
| `config/opt-data.toml` | 新增 `[rollup]` 配置节 |
| `src/opt_data/pipeline/snapshot.py` | `run()` 增加 `view` 参数 |
| `src/opt_data/cli.py` | `close-snapshot` 传递 `view="close"` |
| `src/opt_data/cli.py` | `_precheck_contract_caches` 新增 `universe_path` 参数 |
| `src/opt_data/pipeline/rollup.py` | `__init__` 使用 `cfg.rollup`; 新增 `_load_close()`; `run()` 优先读 close |

---

## Verification Results

```
14 tests passed ✓
- test_config.py: 9 passed
- test_snapshot_runner.py: 4 passed  
- test_close_snapshot_cli.py: 1 passed
```

---

## Configuration Reference

### Universe Configuration

```toml
[universe]
file = "config/universe.csv"                    # 默认全量标的清单
intraday_file = "config/universe.intraday.csv"  # 盘中快照精简版
close_file = ""                                 # 收盘快照专用（为空则使用 file）
refresh_days = 30
```

### Rollup Configuration

```toml
[rollup]
close_slot = 13                     # 16:00 槽位（默认收盘）
fallback_slot = 12                  # 15:30 槽位（备选）
allow_intraday_fallback = false     # close view 缺失时是否回退到 intraday
```

### Compare 配置与验证

- 目的：在不污染主测试目录的前提下，对收盘快照使用全量 universe + `reqtickers` 进行对比测试。
- 配置：`config/opt-data.test.compare.toml`，paths 指向 `data_test_compare/`、`state_test_compare/`，fetch_mode 已设为 `reqtickers`。
- 运行示例：
  ```bash
  rm -rf data_test_compare state_test_compare  # 如需重跑先清理
  python -m opt_data.cli close-snapshot --date today \
    --config config/opt-data.test.compare.toml \
    --universe config/universe.csv
  ```
- 验证要点：检查 `data_test_compare/clean/ib/chain/view=close/date=YYYY-MM-DD` 标的覆盖与行数；查看 `state_test_compare/run_logs/errors_*` 是否存在 `reference_price_failed` / `snapshot_error`。
- 使用范围：仅供对比/实验，不计入正式 QA，正式结果仍以 `data_test/` 或生产目录为准。

---

## Usage Guide

### 存储路径

| 命令 | 写入路径 |
|------|----------|
| `opt-data snapshot` | `data/clean/ib/chain/view=intraday/...` |
| `opt-data close-snapshot` | `data/clean/ib/chain/view=close/...` |

### Rollup 行为

| 场景 | 行为 |
|------|------|
| `view=close` 存在 | 使用 close 数据 |
| `view=close` 缺失 + fallback=false | **报错退出** |
| `view=close` 缺失 + fallback=true | 回退到 intraday，添加 `fallback_intraday` 标记 |

### 示例命令

```bash
# 盘中快照（使用 universe.intraday.csv，写入 view=intraday）
opt-data snapshot --date today --slot now

# 收盘快照（使用 universe.csv，写入 view=close）
opt-data close-snapshot --date today

# 强制使用全量清单
opt-data snapshot --universe config/universe.csv

# Rollup（优先读 view=close）
opt-data rollup --date today
```

---

## Next Steps

1. **手动验证**: 运行 `close-snapshot` 确认数据写入 `view=close`
2. **文档更新**: 补充 `docs/ops-runbook.md` 中的收盘快照章节
3. **运维流程**: 确保调度器按时执行 `close-snapshot`
