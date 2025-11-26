# 错误处理验证指南

本指南说明如何完成验证清单中的两项任务：
1. 在实际环境中测试各种错误场景
2. 确认错误数据行不影响下游处理

## 前提条件

- ✅ IB Gateway 或 TWS 正在运行
- ✅ 项目已安装：`pip install -e .[dev]`
- ✅ 测试配置文件存在：`config/opt-data.test.toml`

---

## 任务 1: 在实际环境中测试各种错误场景

### 方法 A: 使用自动化测试脚本（推荐）

#### 1.1 运行所有错误场景测试

```bash
python scripts/test_error_scenarios.py --scenario all
```

这将测试以下场景：
- **subscription_failed**: 订阅无效合约
- **timeout**: 使用极短超时导致数据未就绪
- **partial_failure**: 混合有效和无效合约

#### 1.2 运行单个场景测试

```bash
# 测试订阅失败场景
python scripts/test_error_scenarios.py --scenario subscription_failed

# 测试超时场景
python scripts/test_error_scenarios.py --scenario timeout

# 测试部分失败场景
python scripts/test_error_scenarios.py --scenario partial_failure
```

#### 1.3 检查输出

查看日志输出中的以下关键信息：

```
✓ Error correctly flagged
  Error type: subscription_failed
  Error message: ConnectionError: IB Gateway not connected

✓ Timeout correctly detected
  Price ready: False
  Greeks ready: False

✓ Successful contracts: 2
✓ Failed contracts: 1
```

### 方法 B: 手动测试关键场景

#### 场景 1: 测试无效合约

```python
from opt_data.config import load_config
from opt_data.ib.session import IBSession
from opt_data.ib.snapshot import collect_option_snapshots

cfg = load_config()
with IBSession(cfg.ib) as ib:
    # 使用明显无效的合约
    results = collect_option_snapshots(
        ib,
        [{
            "symbol": "INVALID_XYZ",
            "strike": 999999.0,
            "right": "C",
            "expiry": "19900101",
            "exchange": "SMART",
        }],
        timeout=5.0,
    )
    
    # 检查结果
    for r in results:
        if r.get("snapshot_error"):
            print(f"✓ Error detected: {r['error_type']}")
            print(f"  Message: {r['error_message']}")
```

#### 场景 2: 测试超时

```python
# 使用真实合约但设置很短的超时
results = collect_option_snapshots(
    ib,
    [{
        "symbol": "AAPL",
        "strike": 150.0,
        "right": "C",
        "expiry": "20251231",
        "exchange": "SMART",
    }],
    timeout=0.1,  # 100ms - 几乎肯定超时
    require_greeks=True,
)

# 检查是否超时
if results[0].get("snapshot_timed_out"):
    print("✓ Timeout correctly detected")
```

#### 场景 3: 测试资源清理

```python
import logging
logging.basicConfig(level=logging.INFO)

# 运行会产生错误的场景
# 检查日志中是否有 "Failed to cancel market data" 警告
# 如果没有，说明资源清理正常工作
```

### 验收标准

完成后应验证：

- ✅ **订阅失败**: `error_type = "subscription_failed"`
- ✅ **超时**: `snapshot_timed_out = True` 或 `error_type = "timeout"`
- ✅ **部分失败**: 成功和失败的合约都正确返回
- ✅ **错误日志**: 每个错误都有清晰的日志记录
- ✅ **资源清理**: 没有 "Failed to cancel" 警告（或警告后继续正常）
- ✅ **无崩溃**: 错误不导致程序崩溃

---

## 任务 2: 确认错误数据行不影响下游处理

### 方法 A: 使用自动化测试脚本（推荐）

#### 2.1 运行下游处理测试

```bash
python scripts/test_error_row_downstream.py
```

这将：
1. 创建包含错误行的测试快照数据
2. 运行 QA 指标计算
3. 测试数据质量标记传播
4. 运行 Rollup 管道

#### 2.2 检查测试输出

```
Testing: QA metrics accounting for error rows
  - Successful rows: 1
  - Error rows: 2
  - Timeout rows: 1
  - Error rate: 66.7%
✓ QA metrics correctly account for errors

Testing: Data quality flag propagation
Error row 1:
  - Error type: subscription_failed
  - Quality flags: ['snapshot_error']
  ✓ All market data fields are None/NaN

Testing: Rollup handling of error rows
Rollup completed:
  - Rows written: 1
  - Symbols processed: 1
✓ Error rows were correctly excluded from rollup
```

### 方法 B: 手动端到端测试

#### 2.1 创建测试数据

```python
import pandas as pd
from pathlib import Path
from datetime import datetime

# 创建包含错误行的数据
data = [
    # 正常行
    {
        "symbol": "AAPL", "strike": 150.0, "right": "C",
        "bid": 5.00, "ask": 5.10, "iv": 0.25, "delta": 0.55,
        "snapshot_error": False, "slot_30m": 13,
    },
    # 错误行
    {
        "symbol": "AAPL", "strike": 155.0, "right": "C",
        "bid": None, "ask": None, "iv": None, "delta": None,
        "snapshot_error": True, "error_type": "subscription_failed",
        "slot_30m": 13,
    },
]

df = pd.DataFrame(data)

# 保存到测试目录
test_path = Path("data_test/clean/ib/chain/view=intraday/date=2025-11-26/underlying=AAPL/exchange=SMART")
test_path.mkdir(parents=True, exist_ok=True)
df.to_parquet(test_path / "test_with_errors.parquet")
```

#### 2.2 运行 Rollup 管道

```bash
python -m opt_data.cli rollup \
    --date 2025-11-26 \
    --symbols AAPL \
    --config config/opt-data.test.toml
```

检查：
- 是否成功完成（不崩溃）
- 错误行是否被正确排除或标记
- 日志中是否有关于错误行的提示

#### 2.3 检查 Rollup 输出

```python
# 查看 daily_clean 视图
daily_path = Path("data_test/clean/ib/chain/view=daily_clean/date=2025-11-26/underlying=AAPL/exchange=SMART")
if daily_path.exists():
    for f in daily_path.glob("*.parquet"):
        df = pd.read_parquet(f)
        print(f"Daily clean rows: {len(df)}")
        print(f"Error rows in daily: {df['snapshot_error'].sum() if 'snapshot_error' in df.columns else 0}")
```

#### 2.4 运行 Enrichment 管道

```bash
python -m opt_data.cli enrichment \
    --date 2025-11-26 \
    --symbols AAPL \
    --config config/opt-data.test.toml
```

检查：
- Enrichment 是否跳过错误行
- 或者是否正确标记无法enriched的错误行

#### 2.5 运行 QA 检查

```bash
python -m opt_data.cli selfcheck \
    --date 2025-11-26 \
    --config config/opt-data.test.toml
```

检查 QA 报告中关于错误的统计：
- 错误率
- 数据完整性
- 是否有针对错误行的特殊处理

### 验收标准

完成后应验证：

- ✅ **Rollup 不崩溃**: 能正常处理包含错误行的数据
- ✅ **错误行处理策略明确**: 
  - 选项 A: 错误行被排除在 daily 视图外
  - 选项 B: 错误行被包含但有明确标记
- ✅ **数据质量标记传播**: `snapshot_error`, `error_type` 等字段在下游可见
- ✅ **Enrichment 容错**: 不会尝试 enrich 错误行
- ✅ **QA 指标正确**: 
  - 错误率被正确计算
  - 槽位覆盖率考虑错误行
  - selfcheck 能识别高错误率
- ✅ **日志清晰**: 下游处理日志中有关于错误行的信息

---

## 快速验证检查清单

### 实际环境错误场景测试

```bash
# 1. 运行自动化错误场景测试
python scripts/test_error_scenarios.py --scenario all

# 2. 检查日志输出
# ✓ 每个场景都有明确的 ✓ 或 ✗ 标记
# ✓ 错误类型正确分类
# ✓ 错误消息包含足够信息
# ✓ 没有未捕获的异常崩溃

# 3. 如有IB连接，运行集成测试
pytest tests/test_snapshot_error_handling.py -m integration -v
```

### 下游处理验证

```bash
# 1. 运行下游处理测试
python scripts/test_error_row_downstream.py

# 2. 检查输出
# ✓ QA 指标正确统计错误
# ✓ 数据质量标记正确传播
# ✓ Rollup 正确处理错误行

# 3. 手动检查生成的文件
ls -lh data_test/clean/ib/chain/view=daily_clean/date=*/
# 验证文件存在且大小合理

# 4. 检查 selfcheck 输出
python -m opt_data.cli selfcheck --date $(date +%Y-%m-%d) --config config/opt-data.test.toml
```

---

## 常见问题

### Q1: 如果所有错误场景测试都因为 IB 连接失败而失败怎么办？

**A**: 这实际上验证了一个重要错误场景！检查：
- 错误类型是否为 `RuntimeError`
- 错误消息是否清晰说明连接问题
- 是否有合适的日志输出

### Q2: Rollup 是否应该包含错误行？

**A**: 取决于业务逻辑，但建议：
- **不包含**: 错误行代表无效数据，不应出现在日终视图中
- **包含但标记**: 如果需要追踪错误，可以包含但保留 `snapshot_error` 标记

当前实现应该选择其中一种策略并在代码中明确。

### Q3: 如何模拟权限不足的错误？

**A**: 尝试订阅需要特殊权限的合约（如某些指数期权），或使用 market data type 4（frozen delayed）。

### Q4: 错误率多高算异常？

**A**: 建议阈值：
- **正常**: < 5% 错误率
- **警告**: 5-10% 错误率
- **严重**: > 10% 错误率

在 QA 配置中设置相应阈值。

---

## 完成确认

当以下所有项都完成时，可以勾选验证清单：

- [ ] ✅ 运行 `test_error_scenarios.py --scenario all` 且所有场景都正确标记
- [ ] ✅ 手动测试至少一个错误场景并观察日志输出
- [ ] ✅ 运行 `test_error_row_downstream.py` 且所有检查通过
- [ ] ✅ 确认 Rollup 不会因错误行崩溃
- [ ] ✅ 确认 QA 指标正确统计错误
- [ ] ✅ 在测试环境跑完整管道（snapshot → rollup → enrichment → selfcheck）
- [ ] ✅ 查看 selfcheck 报告确认错误被正确追踪

---

## 参考文件

- 错误场景测试: `scripts/test_error_scenarios.py`
- 下游处理测试: `scripts/test_error_row_downstream.py`
- 单元测试框架: `tests/test_snapshot_error_handling.py`
- 错误处理实现: `src/opt_data/ib/snapshot.py`
- 完成报告: `walkthrough.md`
