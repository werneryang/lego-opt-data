"""
Data quality schemas for option market data using Pandera.
"""

import pandera as pa
from pandera.typing import DataFrame, Series


class OptionMarketDataSchema(pa.DataFrameModel):
    """
    Schema for option market data validation.
    
    Validates core fields, price consistency, and Greeks ranges.
    """
    
    # Core Identity Fields
    symbol: Series[str] = pa.Field(coerce=True)
    conid: Series[int] = pa.Field(ge=0, coerce=True)
    # trade_date might be string or datetime depending on stage, coerce to datetime
    trade_date: Series[pa.DateTime] = pa.Field(coerce=True)
    
    # Price Fields (Nullable because some options might not trade)
    # But if present, must be non-negative
    bid: Series[float] = pa.Field(ge=0, nullable=True, coerce=True)
    ask: Series[float] = pa.Field(ge=0, nullable=True, coerce=True)
    last: Series[float] = pa.Field(ge=0, nullable=True, coerce=True)
    
    # Greeks (Nullable)
    # IV should be positive generally, but 0 is possible in edge cases
    iv: Series[float] = pa.Field(ge=0, nullable=True, coerce=True)
    
    # Delta: -1.0 to 1.0 (allow small epsilon for floating point issues)
    delta: Series[float] = pa.Field(ge=-1.01, le=1.01, nullable=True, coerce=True)
    
    # Gamma: Usually positive for long options, but we store raw values
    gamma: Series[float] = pa.Field(nullable=True, coerce=True)
    
    # Vega: Usually positive
    vega: Series[float] = pa.Field(nullable=True, coerce=True)
    
    # Theta: Usually negative for long options
    theta: Series[float] = pa.Field(nullable=True, coerce=True)

    class Config:
        """Pandera configuration."""
        coerce = True  # Auto-convert types where possible
        strict = False # Allow extra columns (like internal flags)

    @pa.dataframe_check(name="ask_ge_bid")
    def ask_ge_bid(cls, df: DataFrame) -> Series[bool]:
        """
        Ensure ask >= bid where both exist.
        Returns True if condition met or if either is NaN.
        """
        # We only check where both are present
        mask = df["ask"].notna() & df["bid"].notna()
        # Return True for NaNs (pass) and the condition for others
        return ~mask | (df["ask"] >= df["bid"])
