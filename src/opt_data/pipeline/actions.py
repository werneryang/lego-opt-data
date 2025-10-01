from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from ..config import AppConfig


@dataclass
class CorporateActionsAdjuster:
    actions: Optional[pd.DataFrame]

    @classmethod
    def from_config(cls, cfg: AppConfig) -> "CorporateActionsAdjuster":
        path = Path(cfg.reference.corporate_actions)
        if not path.exists():
            return cls(actions=None)
        df = pd.read_csv(path)
        if df.empty:
            return cls(actions=None)
        if "symbol" not in df.columns or "effective_date" not in df.columns:
            raise ValueError(
                "corporate_actions.csv must contain 'symbol' and 'effective_date' columns"
            )
        if "split_ratio" not in df.columns:
            df["split_ratio"] = 1.0
        df["symbol"] = df["symbol"].str.upper()
        df["effective_date"] = pd.to_datetime(df["effective_date"]).dt.normalize()
        df["split_ratio"] = pd.to_numeric(df["split_ratio"], errors="coerce").fillna(1.0)
        df.sort_values(["symbol", "effective_date"], inplace=True)
        df["cum_split"] = df.groupby("symbol")["split_ratio"].cumprod()
        df["adj_factor"] = 1.0 / df["cum_split"]
        return cls(actions=df[["symbol", "effective_date", "adj_factor"]])

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        result["underlying_close_adj"] = result["underlying_close"]
        result["strike_adj"] = result["strike"]
        result["moneyness_pct_adj"] = result.get(
            "moneyness_pct", pd.Series([pd.NA] * len(result), index=result.index)
        )

        if self.actions is None or result.empty:
            if "moneyness_pct" in result.columns:
                result["moneyness_pct_adj"] = result["moneyness_pct"]
            return result

        actions = self.actions.copy()
        left = result.reset_index()
        left.rename(columns={"index": "_orig_index"}, inplace=True)
        left["trade_ts"] = pd.to_datetime(left["trade_date"]).dt.normalize()

        merged = pd.merge_asof(
            left.sort_values("trade_ts"),
            actions.sort_values("effective_date"),
            left_on="trade_ts",
            right_on="effective_date",
            by="symbol",
            direction="backward",
            allow_exact_matches=True,
        )

        factors = merged["adj_factor"].fillna(1.0)
        merged["underlying_close_adj"] = merged["underlying_close"] * factors
        merged["strike_adj"] = merged["strike"] * factors
        merged["moneyness_pct_adj"] = merged["underlying_close_adj"] / merged["strike_adj"] - 1

        merged.loc[merged["strike_adj"] == 0.0, "moneyness_pct_adj"] = pd.NA
        if "moneyness_pct" not in merged:
            merged["moneyness_pct"] = merged["underlying_close"] / merged["strike"] - 1

        ordered = merged.sort_values("_orig_index").set_index("_orig_index")
        return ordered.drop(columns=["trade_ts", "effective_date"]).sort_index()
