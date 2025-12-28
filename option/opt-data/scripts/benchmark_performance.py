"""
Performance benchmark script for opt-data optimizations.

This script provides benchmarks for:
1. Contract verification (discovery)
2. Cache operations
3. Memory usage (DataFrame operations)
"""

import time
from pathlib import Path
from datetime import date
import pandas as pd
import numpy as np

from opt_data.util.cache_manager import CacheManager
from opt_data.util.memory import optimize_dataframe_dtypes, get_memory_usage_summary


def benchmark_cache_operations(num_contracts: int = 1000):
    """Benchmark cache read/write performance."""
    print(f"\n{'=' * 60}")
    print(f"Cache Performance Benchmark ({num_contracts} contracts)")
    print(f"{'=' * 60}")

    # Create test data
    test_data = [
        {
            "symbol": "AAPL",
            "strike": 100.0 + i * 2.5,
            "expiry": "2025-12-31",
            "right": "C" if i % 2 == 0 else "P",
            "conid": 400000000 + i,
            "exchange": "SMART",
            "tradingClass": "AAPL",
            "multiplier": 100,
        }
        for i in range(num_contracts)
    ]

    cache_root = Path("/tmp/cache_benchmark")
    cache_root.mkdir(exist_ok=True)
    manager = CacheManager(cache_root)
    test_date = date(2025, 11, 26)

    # Benchmark JSON write
    start = time.time()
    json_path = manager.save("TEST", test_date, test_data, use_compression=False)
    json_write_time = time.time() - start
    json_size = json_path.stat().st_size

    # Benchmark JSON read
    start = time.time()
    manager.load("TEST", test_date, use_memory_cache=False)
    json_read_time = time.time() - start

    # Benchmark Pickle+Gzip write
    start = time.time()
    pkl_path = manager.save("TEST2", test_date, test_data, use_compression=True)
    pkl_write_time = time.time() - start
    pkl_size = pkl_path.stat().st_size

    # Benchmark Pickle+Gzip read
    start = time.time()
    manager.load("TEST2", test_date, use_memory_cache=False)
    pkl_read_time = time.time() - start

    # Results
    print("\nJSON Format:")
    print(f"  Write: {json_write_time * 1000:.2f}ms")
    print(f"  Read:  {json_read_time * 1000:.2f}ms")
    print(f"  Size:  {json_size:,} bytes")

    print("\nPickle+Gzip Format:")
    print(f"  Write: {pkl_write_time * 1000:.2f}ms")
    print(f"  Read:  {pkl_read_time * 1000:.2f}ms")
    print(f"  Size:  {pkl_size:,} bytes")

    print("\nImprovement:")
    write_speedup = json_write_time / pkl_write_time if pkl_write_time > 0 else 0
    read_speedup = json_read_time / pkl_read_time if pkl_read_time > 0 else 0
    size_reduction = 100 * (json_size - pkl_size) / json_size if json_size > 0 else 0

    print(f"  Write: {write_speedup:.1f}x faster")
    print(f"  Read:  {read_speedup:.1f}x faster")
    print(f"  Size:  {size_reduction:.1f}% reduction")

    # Cleanup
    import shutil

    shutil.rmtree(cache_root)


def benchmark_memory_optimization(num_rows: int = 100000):
    """Benchmark DataFrame memory optimization."""
    print(f"\n{'=' * 60}")
    print(f"Memory Optimization Benchmark ({num_rows:,} rows)")
    print(f"{'=' * 60}")

    # Create test DataFrame
    df = pd.DataFrame(
        {
            "symbol": np.random.choice(["AAPL", "MSFT", "GOOG", "AMZN"], num_rows),
            "strike": np.random.uniform(100, 500, num_rows),
            "delta": np.random.uniform(-1, 1, num_rows),
            "gamma": np.random.uniform(0, 0.1, num_rows),
            "theta": np.random.uniform(-5, 0, num_rows),
            "vega": np.random.uniform(0, 50, num_rows),
            "iv": np.random.uniform(0.1, 1.0, num_rows),
            "bid": np.random.uniform(1, 100, num_rows),
            "ask": np.random.uniform(1, 100, num_rows),
            "volume": np.random.randint(0, 10000, num_rows),
            "conid": np.random.randint(400000000, 500000000, num_rows),
            "slot_30m": np.random.randint(0, 14, num_rows),
        }
    )

    # Before optimization
    before = get_memory_usage_summary(df)

    # Optimize
    start = time.time()
    df_optimized = optimize_dataframe_dtypes(df, verbose=False)
    optimize_time = time.time() - start

    # After optimization
    after = get_memory_usage_summary(df_optimized)

    # Results
    print("\nBefore Optimization:")
    print(f"  Memory: {before['total_mb']:.2f} MB")
    print(f"  Per row: {before['bytes_per_row']:.1f} bytes")

    print("\nAfter Optimization:")
    print(f"  Memory: {after['total_mb']:.2f} MB")
    print(f"  Per row: {after['bytes_per_row']:.1f} bytes")
    print(f"  Time: {optimize_time * 1000:.2f}ms")

    reduction = 100 * (before["total_mb"] - after["total_mb"]) / before["total_mb"]
    print("\nImprovement:")
    print(f"  Memory saved: {reduction:.1f}%")
    print(f"  Absolute: {before['total_mb'] - after['total_mb']:.2f} MB")


def benchmark_adaptive_batch_size():
    """Demonstrate adaptive batch size logic."""
    print(f"\n{'=' * 60}")
    print("Adaptive Batch Size Strategy")
    print(f"{'=' * 60}")

    test_cases = [10, 25, 50, 100, 250, 500, 1000, 2000]

    print(f"\n{'Contracts':<12} {'Batch Size':<12} {'Batches':<10}")
    print("-" * 40)

    for total in test_cases:
        # Adaptive logic (matches discovery.py)
        if total <= 25:
            batch_size = total
        elif total <= 100:
            batch_size = 50
        elif total <= 500:
            batch_size = 75
        else:
            batch_size = 100

        num_batches = (total + batch_size - 1) // batch_size
        print(f"{total:<12} {batch_size:<12} {num_batches:<10}")


if __name__ == "__main__":
    print("=" * 60)
    print("OPT-DATA PERFORMANCE BENCHMARKS")
    print("=" * 60)

    try:
        benchmark_cache_operations(1000)
    except Exception as e:
        print(f"\nCache benchmark failed: {e}")

    try:
        benchmark_memory_optimization(100000)
    except Exception as e:
        print(f"\nMemory benchmark failed: {e}")

    try:
        benchmark_adaptive_batch_size()
    except Exception as e:
        print(f"\nBatch size benchmark failed: {e}")

    print(f"\n{'=' * 60}")
    print("Benchmarks Complete")
    print(f"{'=' * 60}\n")
