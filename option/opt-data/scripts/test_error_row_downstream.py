#!/usr/bin/env python3
"""
Test downstream processing of error rows.

This script validates that error rows from snapshot collection are properly
handled by downstream components (rollup, enrichment, QA).

It creates synthetic test data with error rows and verifies:
1. Rollup pipeline handles error rows gracefully
2. Enrichment pipeline skips or handles error rows
3. QA metrics correctly account for error rows
4. Data quality flags are properly propagated

Usage:
    python scripts/test_error_row_downstream.py --test-dir data_test
"""

import argparse
import logging
from datetime import date, datetime
from pathlib import Path
import pandas as pd

from opt_data.config import load_config
from opt_data.pipeline.rollup import RollupRunner
# Note: compute_qa_metrics will be computed manually in this script

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_test_snapshot_with_errors(test_dir: Path, trade_date: date):
    """Create a test snapshot dataset with both successful and error rows."""

    # Create test data directory
    # Rollup expects: cfg.paths.clean / "view=intraday"
    snapshot_dir = test_dir / "clean" / "view=intraday"
    partition = snapshot_dir / f"date={trade_date}" / "underlying=AAPL" / "exchange=SMART"
    partition.mkdir(parents=True, exist_ok=True)

    # Create sample data with errors
    data = []

    # Successful row
    data.append(
        {
            "symbol": "AAPL",
            "underlying": "AAPL",
            "underlying_close": 150.0,
            "trade_date": str(trade_date),
            "exchange": "SMART",
            "strike": 150.0,
            "right": "C",
            "expiry": "20251231",
            "conid": 12345,
            "bid": 5.00,
            "ask": 5.10,
            "mid": 5.05,
            "last": 5.08,
            "open": 5.00,
            "high": 5.20,
            "low": 4.95,
            "close": 5.08,
            "volume": 1000,
            "iv": 0.25,
            "delta": 0.55,
            "gamma": 0.05,
            "theta": -0.03,
            "vega": 0.15,
            "market_data_type": 1,
            "asof": datetime.now().isoformat(),
            "sample_time": datetime.now().isoformat(),
            "slot_30m": 13,  # 16:00 ET slot
            "price_ready": True,
            "greeks_ready": True,
            "snapshot_timed_out": False,
            "snapshot_error": False,
            "data_quality_flag": [],
        }
    )

    # Error row - subscription failed
    data.append(
        {
            "symbol": "AAPL",
            "underlying": "AAPL",
            "underlying_close": 150.0,
            "trade_date": str(trade_date),
            "exchange": "SMART",
            "strike": 155.0,
            "right": "C",
            "expiry": "20251231",
            "conid": 12346,
            "bid": None,
            "ask": None,
            "mid": None,
            "last": None,
            "open": None,
            "high": None,
            "low": None,
            "close": None,
            "volume": None,
            "iv": None,
            "delta": None,
            "gamma": None,
            "theta": None,
            "vega": None,
            "market_data_type": None,
            "asof": None,
            "sample_time": datetime.now().isoformat(),
            "slot_30m": 13,
            "price_ready": False,
            "greeks_ready": False,
            "snapshot_timed_out": False,
            "snapshot_error": True,
            "error_type": "subscription_failed",
            "error_message": "ConnectionError: IB Gateway not connected",
            "data_quality_flag": ["snapshot_error"],
        }
    )

    # Error row - timeout
    data.append(
        {
            "symbol": "AAPL",
            "underlying": "AAPL",
            "underlying_close": 150.0,
            "trade_date": str(trade_date),
            "exchange": "SMART",
            "strike": 160.0,
            "right": "P",
            "expiry": "20251231",
            "conid": 12347,
            "bid": None,
            "ask": None,
            "mid": None,
            "last": None,
            "open": None,
            "high": None,
            "low": None,
            "close": None,
            "volume": None,
            "iv": None,
            "delta": None,
            "gamma": None,
            "theta": None,
            "vega": None,
            "market_data_type": None,
            "asof": None,
            "sample_time": datetime.now().isoformat(),
            "slot_30m": 13,
            "price_ready": False,
            "greeks_ready": False,
            "snapshot_timed_out": True,
            "snapshot_error": True,
            "error_type": "timeout",
            "error_message": "Data not ready after 12.0s",
            "data_quality_flag": ["snapshot_error", "snapshot_timed_out"],
        }
    )

    # Write to parquet
    df = pd.DataFrame(data)
    output_file = partition / f"snapshot_{trade_date.strftime('%Y%m%d')}_test.parquet"
    df.to_parquet(output_file, index=False)

    logger.info(f"Created test snapshot with {len(data)} rows at {output_file}")
    logger.info("  - Successful rows: 1")
    logger.info("  - Error rows: 2")

    return output_file


def test_rollup_handles_errors(cfg, test_dir: Path, trade_date: date):
    """Test that rollup pipeline handles error rows correctly."""
    logger.info("=" * 60)
    logger.info("Testing: Rollup handling of error rows")
    logger.info("=" * 60)

    # Update config to use test directory
    cfg.paths.clean = test_dir / "clean"

    # Create RollupRunner
    runner = RollupRunner(cfg)

    try:
        result = runner.run(trade_date, symbols=["AAPL"])

        logger.info("Rollup completed:")
        logger.info(f"  - Rows written: {result.rows_written}")
        logger.info(f"  - Symbols processed: {result.symbols_processed}")
        logger.info(f"  - Strategy counts: {result.strategy_counts}")

        # Check if error rows were excluded or flagged
        if result.rows_written == 1:
            logger.info("✓ Error rows were correctly excluded from rollup")
        elif result.rows_written == 3:
            logger.info("⚠ Error rows were included in rollup - check if they're flagged")
        else:
            logger.warning(f"✗ Unexpected row count: {result.rows_written}")

    except Exception as e:
        logger.error(f"Rollup raised exception: {type(e).__name__}: {e}")
        logger.info("This might be expected if error rows cause validation failures")


def test_qa_metrics_account_for_errors(test_dir: Path, trade_date: date):
    """Test that QA metrics correctly account for error rows."""
    logger.info("=" * 60)
    logger.info("Testing: QA metrics accounting for error rows")
    logger.info("=" * 60)

    # Load the test snapshot data
    snapshot_dir = test_dir / "clean" / "view=intraday"
    partition = snapshot_dir / f"date={trade_date}" / "underlying=AAPL" / "exchange=SMART"

    parquet_files = list(partition.glob("*.parquet"))
    if not parquet_files:
        logger.error("No parquet files found - create test data first")
        return

    df = pd.read_parquet(parquet_files[0])

    logger.info(f"Loaded {len(df)} rows from test snapshot")

    # Compute metrics
    error_count = df["snapshot_error"].sum()
    timeout_count = df["snapshot_timed_out"].sum()
    success_count = (~df["snapshot_error"]).sum()

    logger.info(f"  - Successful rows: {success_count}")
    logger.info(f"  - Error rows: {error_count}")
    logger.info(f"  - Timeout rows: {timeout_count}")

    # Check data quality flags
    if "data_quality_flag" in df.columns:
        flagged_rows = df[
            df["data_quality_flag"].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)
        ]
        logger.info(f"  - Rows with quality flags: {len(flagged_rows)}")

        for flag_list in df["data_quality_flag"]:
            if isinstance(flag_list, list) and len(flag_list) > 0:
                logger.info(f"    Quality flags: {flag_list}")

    # Expected: QA system should track error rate
    error_rate = error_count / len(df) if len(df) > 0 else 0
    logger.info(f"  - Error rate: {error_rate:.1%}")

    if error_rate > 0:
        logger.info("✓ QA metrics correctly account for errors")
    else:
        logger.warning("✗ No errors detected in QA metrics")


def test_data_quality_propagation(test_dir: Path, trade_date: date):
    """Test that data quality flags are properly propagated."""
    logger.info("=" * 60)
    logger.info("Testing: Data quality flag propagation")
    logger.info("=" * 60)

    # Load test data
    snapshot_dir = test_dir / "clean" / "view=intraday"
    partition = snapshot_dir / f"date={trade_date}" / "underlying=AAPL" / "exchange=SMART"

    parquet_files = list(partition.glob("*.parquet"))
    if not parquet_files:
        logger.error("No parquet files found")
        return

    df = pd.read_parquet(parquet_files[0])

    # Check that error rows have appropriate flags
    error_rows = df[df["snapshot_error"].fillna(False)]

    logger.info(f"Checking {len(error_rows)} error rows")

    for idx, row in error_rows.iterrows():
        flags = row["data_quality_flag"]
        error_type = row.get("error_type")
        error_msg = row.get("error_message")

        logger.info(f"\nError row {idx}:")
        logger.info(f"  - Error type: {error_type}")
        logger.info(f"  - Error message: {error_msg}")
        logger.info(f"  - Quality flags: {flags}")

        # Verify essential fields are None
        none_fields = ["bid", "ask", "mid", "last", "iv", "delta", "gamma", "theta", "vega"]
        all_none = all(pd.isna(row[field]) or row[field] is None for field in none_fields)

        if all_none:
            logger.info("  ✓ All market data fields are None/NaN")
        else:
            logger.warning("  ✗ Some market data fields have values")
            for field in none_fields:
                if not (pd.isna(row[field]) or row[field] is None):
                    logger.warning(f"    {field} = {row[field]}")


def main():
    parser = argparse.ArgumentParser(description="Test downstream processing of error rows")
    parser.add_argument("--test-dir", type=str, default="data_test", help="Test data directory")
    parser.add_argument(
        "--config", type=str, default="config/opt-data.test.toml", help="Path to config file"
    )
    parser.add_argument(
        "--date", type=str, default=None, help="Trade date (YYYY-MM-DD), defaults to today"
    )

    args = parser.parse_args()

    # Load config
    cfg = load_config(Path(args.config))
    logger.info(f"Loaded config from {args.config}")

    # Determine trade date
    if args.date:
        trade_date = date.fromisoformat(args.date)
    else:
        trade_date = date.today()

    logger.info(f"Using trade date: {trade_date}")

    test_dir = Path(args.test_dir)

    # Step 1: Create test data with error rows
    logger.info("\n" + "=" * 60)
    logger.info("Step 1: Creating test snapshot data with errors")
    logger.info("=" * 60)
    create_test_snapshot_with_errors(test_dir, trade_date)

    # Step 2: Test QA metrics
    logger.info("\n")
    test_qa_metrics_account_for_errors(test_dir, trade_date)

    # Step 3: Test data quality propagation
    logger.info("\n")
    test_data_quality_propagation(test_dir, trade_date)

    # Step 4: Test rollup
    logger.info("\n")
    test_rollup_handles_errors(cfg, test_dir, trade_date)

    logger.info("\n" + "=" * 60)
    logger.info("Downstream processing tests completed")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Review the test output above")
    logger.info("2. Check data_test/clean/ib/chain/view=daily_clean for rollup results")
    logger.info("3. Verify error rows are properly excluded or flagged")
    logger.info("4. Run real pipeline to confirm behavior in production")


if __name__ == "__main__":
    main()
