"""
Memory optimization utilities for DataFrame operations.

Provides tools to reduce DataFrame memory usage through dtype optimization
and chunked processing.
"""

import logging
from typing import Callable, Iterator, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def optimize_dataframe_dtypes(
    df: pd.DataFrame,
    categorical_threshold: float = 0.5,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Reduce DataFrame memory usage by optimizing column data types.

    Args:
        df: DataFrame to optimize
        categorical_threshold: Convert to category if unique ratio < this value
        verbose: If True, log memory savings

    Returns:
        Optimized DataFrame
    """
    if df.empty:
        return df

    start_mem = df.memory_usage(deep=True).sum() / 1024**2  # MB

    for col in df.columns:
        col_type = df[col].dtype

        if col_type == "object":
            # Skip columns that contain lists or arrays
            try:
                # Check if first non-null value is a list/array
                first_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if isinstance(first_val, (list, tuple, pd.Series, pd.DataFrame)):
                    if verbose:
                        logger.debug(f"Skipping {col} (contains list/array)")
                    continue
            except (IndexError, AttributeError):
                pass

            # Try to convert to category if few unique values
            try:
                num_unique = df[col].nunique()
                num_total = len(df[col])

                if num_total > 0 and num_unique / num_total < categorical_threshold:
                    df[col] = df[col].astype("category")
                    if verbose:
                        logger.debug(f"Converted {col} to category ({num_unique} unique values)")
            except TypeError:
                # Column contains unhashable types
                if verbose:
                    logger.debug(f"Skipping {col} (unhashable type)")
                continue

        elif col_type == "float64":
            # Downcast to float32 if safe
            # Check if all values fit in float32 range
            col_min = df[col].min()
            col_max = df[col].max()

            if pd.notna(col_min) and pd.notna(col_max):
                if col_min >= -3.4e38 and col_max <= 3.4e38:
                    df[col] = df[col].astype("float32")
                    if verbose:
                        logger.debug(f"Downcast {col} to float32")

        elif col_type == "int64":
            # Downcast to smaller int type
            col_min = df[col].min()
            col_max = df[col].max()

            if pd.notna(col_min) and pd.notna(col_max):
                if col_min >= -128 and col_max <= 127:
                    df[col] = df[col].astype("int8")
                elif col_min >= -32768 and col_max <= 32767:
                    df[col] = df[col].astype("int16")
                elif col_min >= -2147483648 and col_max <= 2147483647:
                    df[col] = df[col].astype("int32")

                if verbose:
                    logger.debug(f"Downcast {col} to {df[col].dtype}")

    end_mem = df.memory_usage(deep=True).sum() / 1024**2  # MB
    reduction = 100 * (start_mem - end_mem) / start_mem if start_mem > 0 else 0

    if verbose:
        logger.info(
            f"Memory usage: {start_mem:.2f} MB -> {end_mem:.2f} MB ({reduction:.1f}% reduction)"
        )

    return df


def process_dataframe_chunks(
    df: pd.DataFrame,
    process_fn: Callable[[pd.DataFrame], pd.DataFrame],
    chunk_size: int = 10000,
) -> pd.DataFrame:
    """
    Process a large DataFrame in chunks to reduce memory usage.

    Args:
        df: DataFrame to process
        process_fn: Function to apply to each chunk
        chunk_size: Number of rows per chunk

    Returns:
        Processed DataFrame
    """
    if len(df) <= chunk_size:
        return process_fn(df)

    chunks: List[pd.DataFrame] = []

    for start_idx in range(0, len(df), chunk_size):
        end_idx = min(start_idx + chunk_size, len(df))
        chunk = df.iloc[start_idx:end_idx]
        processed = process_fn(chunk)
        chunks.append(processed)

        if start_idx % (chunk_size * 10) == 0:
            logger.debug(f"Processed {start_idx}/{len(df)} rows")

    return pd.concat(chunks, ignore_index=True)


def iter_parquet_chunks(
    file_path: str,
    chunk_size: int = 10000,
    columns: Optional[List[str]] = None,
) -> Iterator[pd.DataFrame]:
    """
    Iterate over a Parquet file in chunks.

    Args:
        file_path: Path to Parquet file
        chunk_size: Number of rows per chunk
        columns: Specific columns to read (None = all columns)

    Yields:
        DataFrame chunks
    """
    # Read Parquet file metadata to get total rows
    pf = pd.read_parquet(file_path, columns=columns if columns else None)
    total_rows = len(pf)

    for start_row in range(0, total_rows, chunk_size):
        end_row = min(start_row + chunk_size, total_rows)
        chunk = pf.iloc[start_row:end_row]
        yield chunk


def get_memory_usage_summary(df: pd.DataFrame) -> dict:
    """
    Get detailed memory usage information for a DataFrame.

    Args:
        df: DataFrame to analyze

    Returns:
        Dictionary with memory usage details
    """
    mem_usage = df.memory_usage(deep=True)
    total_mb = mem_usage.sum() / 1024**2

    return {
        "total_mb": total_mb,
        "rows": len(df),
        "columns": len(df.columns),
        "bytes_per_row": mem_usage.sum() / len(df) if len(df) > 0 else 0,
        "column_usage_mb": (mem_usage / 1024**2).to_dict(),
        "dtypes": df.dtypes.value_counts().to_dict(),
    }


def suggest_dtype_optimizations(df: pd.DataFrame) -> List[str]:
    """
    Suggest dtype optimizations for a DataFrame.

    Args:
        df: DataFrame to analyze

    Returns:
        List of optimization suggestions
    """
    suggestions = []

    for col in df.columns:
        col_type = df[col].dtype

        if col_type == "object":
            num_unique = df[col].nunique()
            if num_unique / len(df) < 0.5:
                suggestions.append(
                    f"{col}: Convert to category ({num_unique} unique / {len(df)} total)"
                )

        elif col_type == "float64":
            suggestions.append(f"{col}: Consider downcast to float32")

        elif col_type == "int64":
            col_min = df[col].min()
            col_max = df[col].max()
            if col_min >= -128 and col_max <= 127:
                suggestions.append(f"{col}: Can use int8")
            elif col_min >= -32768 and col_max <= 32767:
                suggestions.append(f"{col}: Can use int16")
            elif col_min >= -2147483648 and col_max <= 2147483647:
                suggestions.append(f"{col}: Can use int32")

    return suggestions
