import pandas as pd
from pathlib import Path
import sys
import os
import pyarrow.dataset as ds

# Add src to path
sys.path.append(os.path.abspath("src"))


def load_parquet_data_debug(path_str):
    try:
        path = Path(path_str)
        if not path.exists():
            print(f"Path does not exist: {path}")
            return pd.DataFrame()

        print(f"Loading from {path} using pyarrow.dataset...")
        # Use pyarrow dataset for robust partitioned loading
        dataset = ds.dataset(path, partitioning="hive")

        # We can try to consolidate schema if needed, but default might work better than pandas
        table = dataset.to_table()
        df = table.to_pandas()
        return df
    except Exception as e:
        print(f"ERROR loading {path_str}: {e}")
        return pd.DataFrame()


def test_data_loading():
    date_str = "2025-11-26"  # Known date with data

    # 1. Intraday
    intraday_path = f"data/clean/ib/chain/view=intraday/date={date_str}"
    print(f"Testing Intraday Path: {intraday_path}")
    df_intraday = load_parquet_data_debug(intraday_path)
    print(f"Intraday Rows: {len(df_intraday)}")

    # 2. Daily
    daily_path = f"data/clean/ib/chain/view=daily_clean/date={date_str}"
    print(f"\nTesting Daily Path: {daily_path}")
    df_daily = load_parquet_data_debug(daily_path)
    print(f"Daily Rows: {len(df_daily)}")

    # 3. Direct File Test
    direct_file = f"data/clean/ib/chain/view=daily_clean/date={date_str}/underlying=AAPL/exchange=SMART/part-000.parquet"
    print(f"\nTesting Direct File: {direct_file}")
    df_direct = load_parquet_data_debug(direct_file)
    print(f"Direct Rows: {len(df_direct)}")


if __name__ == "__main__":
    test_data_loading()
