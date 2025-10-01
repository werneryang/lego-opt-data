from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd

from ..config import AppConfig
from .actions import CorporateActionsAdjuster


PRICE_COLS = [
    "bid",
    "ask",
    "last",
    "close",
    "iv",
    "delta",
    "gamma",
    "theta",
    "vega",
]

VOLUME_COLS = ["volume", "open_interest", "bid_size", "ask_size"]


@dataclass
class CleaningPipeline:
    cfg: AppConfig
    adjuster: CorporateActionsAdjuster

    @classmethod
    def create(cls, cfg: AppConfig) -> "CleaningPipeline":
        return cls(cfg=cfg, adjuster=CorporateActionsAdjuster.from_config(cfg))

    def process(self, raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        if raw_df.empty:
            empty = raw_df.copy()
            return empty, empty

        df = raw_df.copy()
        df["source"] = "IBKR"
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.normalize()
        df["asof_ts"] = pd.to_datetime(df["asof_ts"])

        numeric_cols = PRICE_COLS + ["strike", "multiplier", "underlying_close"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        for col in VOLUME_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")

        if "bid" in df and "ask" in df:
            df["mid"] = (df["bid"] + df["ask"]) / 2
        else:
            df["mid"] = np.nan

        df["strike_per_100"] = np.nan
        if "strike" in df and "multiplier" in df:
            mult = df["multiplier"].replace({0: np.nan})
            df["strike_per_100"] = df["strike"] * (100.0 / mult)

        if "strike" in df:
            df["moneyness_pct"] = df["underlying_close"] / df["strike"] - 1
            df.loc[df["strike"] == 0.0, "moneyness_pct"] = np.nan
        else:
            df["moneyness_pct"] = np.nan

        df["data_quality_flag"] = pd.Series([None] * len(df), index=df.index)
        if "market_data_type" in df.columns:
            df["market_data_type"] = pd.to_numeric(df["market_data_type"], errors="coerce").astype(
                "Int64"
            )

        adjusted = self.adjuster.apply(df)

        return df, adjusted
