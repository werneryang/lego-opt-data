"""
Data quality reporting generation.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Metrics for a single data batch."""
    total_rows: int
    symbols_count: int
    error_rows_count: int
    crossed_market_count: int
    missing_greeks_count: int
    extreme_iv_count: int
    schema_errors: List[str]


@dataclass
class DailyQualityReport:
    """Daily quality report structure."""
    trade_date: str
    generated_at: str
    metrics: QualityMetrics
    
    def to_markdown(self) -> str:
        """Generate Markdown representation of the report."""
        m = self.metrics
        error_rate = (m.error_rows_count / m.total_rows * 100) if m.total_rows > 0 else 0
        
        md = [
            f"# Data Quality Report: {self.trade_date}",
            f"",
            f"**Generated at**: {self.generated_at}",
            f"",
            f"## Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Rows | {m.total_rows:,} |",
            f"| Symbols | {m.symbols_count:,} |",
            f"| Error Rows | {m.error_rows_count:,} ({error_rate:.2f}%) |",
            f"",
            f"## Anomalies",
            f"",
            f"| Anomaly Type | Count |",
            f"|--------------|-------|",
            f"| Crossed Market (Bid > Ask) | {m.crossed_market_count:,} |",
            f"| Missing Greeks | {m.missing_greeks_count:,} |",
            f"| Extreme IV (>500%) | {m.extreme_iv_count:,} |",
            f"",
        ]
        
        if m.schema_errors:
            md.append("## Schema Validation Errors")
            md.append("")
            for err in m.schema_errors[:10]:  # Show top 10
                md.append(f"- {err}")
            if len(m.schema_errors) > 10:
                md.append(f"- ... and {len(m.schema_errors) - 10} more")
        
        return "\n".join(md)

    def save(self, output_dir: Path) -> Path:
        """Save report to disk as JSON and Markdown."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = f"quality_report_{self.trade_date}"
        
        # Save JSON
        json_path = output_dir / f"{base_name}.json"
        with open(json_path, "w") as f:
            json.dump(asdict(self), f, indent=2)
            
        # Save Markdown
        md_path = output_dir / f"{base_name}.md"
        with open(md_path, "w") as f:
            f.write(self.to_markdown())
            
        logger.info(f"Quality report saved to {output_dir}")
        return md_path


def generate_quality_report(
    df: pd.DataFrame,
    trade_date: date,
    schema_errors: List[str] = None
) -> DailyQualityReport:
    """
    Generate a quality report from a DataFrame.
    
    Args:
        df: The processed DataFrame (should contain quality_flags if available)
        trade_date: The trade date
        schema_errors: List of schema validation error messages
    """
    total_rows = len(df)
    
    # Count anomalies based on flags if present
    crossed_market = 0
    extreme_iv = 0
    
    if "quality_flags" in df.columns:
        # Explode flags to count
        all_flags = df["quality_flags"].explode().dropna()
        counts = all_flags.value_counts()
        crossed_market = counts.get("crossed_market", 0)
        extreme_iv = counts.get("extreme_iv", 0)
    
    # Count missing greeks
    missing_greeks = 0
    if "delta" in df.columns:
        missing_greeks = df["delta"].isna().sum()
        
    # Count error rows (snapshot_error=True)
    error_rows = 0
    if "snapshot_error" in df.columns:
        error_rows = df["snapshot_error"].fillna(False).sum()
        
    metrics = QualityMetrics(
        total_rows=total_rows,
        symbols_count=df["symbol"].nunique() if "symbol" in df.columns else 0,
        error_rows_count=int(error_rows),
        crossed_market_count=int(crossed_market),
        missing_greeks_count=int(missing_greeks),
        extreme_iv_count=int(extreme_iv),
        schema_errors=schema_errors or []
    )
    
    return DailyQualityReport(
        trade_date=trade_date.isoformat(),
        generated_at=datetime.now().isoformat(),
        metrics=metrics
    )
