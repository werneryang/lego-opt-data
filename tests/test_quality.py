"""
Tests for the data quality module.
"""

import pandas as pd
import pytest
import pandera as pa
from datetime import date

from opt_data.quality.schemas import OptionMarketDataSchema
from opt_data.quality.checks import detect_anomalies
from opt_data.quality.report import generate_quality_report, DailyQualityReport


class TestQualityModule:
    
    def test_schema_validation_valid(self):
        """Test schema validation with valid data."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "MSFT"],
            "conid": [123, 456],
            "trade_date": [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-01")],
            "bid": [10.0, 20.0],
            "ask": [10.1, 20.1],
            "last": [10.05, 20.05],
            "iv": [0.2, 0.3],
            "delta": [0.5, -0.5],
            "gamma": [0.01, 0.02],
            "vega": [0.1, 0.2],
            "theta": [-0.1, -0.2],
        })
        
        validated = OptionMarketDataSchema.validate(df)
        assert isinstance(validated, pd.DataFrame)

    def test_schema_validation_invalid(self):
        """Test schema validation with invalid data."""
        df = pd.DataFrame({
            "symbol": ["AAPL"],
            "conid": [-1],  # Invalid: negative conid
            "trade_date": [pd.Timestamp("2025-01-01")],
            "bid": [10.0],
            "ask": [9.0],   # Invalid: ask < bid
            "iv": [-0.1],   # Invalid: negative IV
            "delta": [1.5], # Invalid: delta > 1
        })
        
        with pytest.raises(pa.errors.SchemaErrors) as excinfo:
            OptionMarketDataSchema.validate(df, lazy=True)
            
        failures = excinfo.value.failure_cases
        assert "conid" in failures["column"].values
        assert "ask" in failures["column"].values  # check name might be ask_ge_bid
        assert "iv" in failures["column"].values
        assert "delta" in failures["column"].values

    def test_anomaly_detection(self):
        """Test anomaly detection logic."""
        df = pd.DataFrame({
            "bid": [10.0, 11.0, 0.00],
            "ask": [10.1, 10.0, 0.01], # Row 1: Crossed (11 > 10)
            "delta": [0.5, 0.5, 0.95], # Row 2: Deep ITM but near zero price
            "iv": [0.2, 0.2, 6.0],     # Row 2: Extreme IV
        })
        
        flags = detect_anomalies(df)
        
        assert flags[0] == []
        assert "crossed_market" in flags[1]
        assert "suspicious_itm_zero_price" in flags[2]
        assert "extreme_iv" in flags[2]

    def test_report_generation(self):
        """Test report generation."""
        df = pd.DataFrame({
            "symbol": ["AAPL", "AAPL"],
            "quality_flags": [["crossed_market"], []],
            "delta": [None, 0.5], # One missing greek
            "snapshot_error": [False, True]
        })
        
        report = generate_quality_report(df, date(2025, 1, 1), schema_errors=["Some error"])
        
        assert report.metrics.total_rows == 2
        assert report.metrics.crossed_market_count == 1
        assert report.metrics.missing_greeks_count == 1
        assert report.metrics.error_rows_count == 1
        assert len(report.metrics.schema_errors) == 1
        
        md = report.to_markdown()
        assert "# Data Quality Report" in md
        assert "| Crossed Market (Bid > Ask) | 1 |" in md
