"""
Anomaly detection checks for option market data.
"""

import logging
from typing import List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def detect_anomalies(df: pd.DataFrame) -> pd.Series:
    """
    Detect anomalies in market data rows.

    Returns:
        Series of lists, where each list contains string flags for anomalies found in that row.
        e.g. ["crossed_market", "iv_too_high"]
    """
    if df.empty:
        return pd.Series([[]] * len(df), index=df.index)

    # Initialize with empty lists
    # Note: Using a list comprehension is often faster/cleaner for object series init than apply
    flags = [[] for _ in range(len(df))]

    # We'll use boolean masks for vectorized checks

    # 1. Crossed Market: Bid > Ask
    if "bid" in df.columns and "ask" in df.columns:
        mask_crossed = (df["bid"] > df["ask"]) & df["bid"].notna() & df["ask"].notna()
        if mask_crossed.any():
            _add_flag(flags, mask_crossed, "crossed_market")

    # 2. Zero Price ITM (Simplified heuristic)
    # If delta is high (>0.9 or <-0.9) but price is very low, suspicious
    if "delta" in df.columns and "bid" in df.columns and "ask" in df.columns:
        # Deep ITM calls (delta > 0.9) or puts (delta < -0.9)
        # Should have significant value. If bid+ask is near zero, it's weird.
        mid_price = (df["bid"].fillna(0) + df["ask"].fillna(0)) / 2
        mask_itm_zero = (mid_price < 0.01) & (df["delta"].abs() > 0.9)
        if mask_itm_zero.any():
            _add_flag(flags, mask_itm_zero, "suspicious_itm_zero_price")

    # 3. Extreme Greeks
    if "iv" in df.columns:
        # IV > 500% is usually garbage or extreme event
        mask_high_iv = df["iv"] > 5.0
        if mask_high_iv.any():
            _add_flag(flags, mask_high_iv, "extreme_iv")

    if "delta" in df.columns:
        # Delta outside [-1, 1] significantly
        mask_bad_delta = (df["delta"] < -1.05) | (df["delta"] > 1.05)
        if mask_bad_delta.any():
            _add_flag(flags, mask_bad_delta, "invalid_delta")

    return pd.Series(flags, index=df.index)


def _add_flag(flags_list: List[List[str]], mask: pd.Series, flag_name: str):
    """Helper to add flag to rows where mask is True."""
    # mask is a boolean Series matching flags_list length
    # We iterate indices where mask is True
    # This is faster than zip if anomalies are sparse
    try:
        # Get integer indices where mask is True
        indices = np.where(mask)[0]
        for idx in indices:
            flags_list[idx].append(flag_name)
    except Exception as e:
        logger.warning(f"Failed to add flag {flag_name}: {e}")
