from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from ..config import AppConfig


TOTAL_SLOTS = 14  # 09:30 through 16:00 inclusive, 30-minute cadence


@dataclass
class MetricResult:
    name: str
    value: float
    threshold: float
    comparator: str
    passed: bool
    details: Dict[str, Any]


@dataclass
class QAMetricsResult:
    trade_date: date
    metrics: List[MetricResult]
    status: str
    breaches: List[str]
    extra: Dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "trade_date": self.trade_date.isoformat(),
            "metrics": [asdict(m) for m in self.metrics],
            "status": self.status,
            "breaches": self.breaches,
            **self.extra,
        }


class QAMetricsCalculator:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg

    def evaluate(self, trade_date: date) -> QAMetricsResult:
        intraday_dir = Path(self.cfg.paths.clean) / f"view=intraday/date={trade_date.isoformat()}"
        daily_dir = Path(self.cfg.paths.clean) / f"view=daily_clean/date={trade_date.isoformat()}"

        intraday = _read_parquet_tree(intraday_dir)
        daily = _read_parquet_tree(daily_dir)

        metrics: list[MetricResult] = []
        breaches: list[str] = []
        extra: dict[str, Any] = {}

        coverage_metric, coverage_details = self._metric_slot_coverage(intraday)
        metrics.append(
            MetricResult(
                name="slot_coverage_min",
                value=coverage_metric,
                threshold=self.cfg.qa.slot_coverage_threshold,
                comparator=">=",
                passed=coverage_metric >= self.cfg.qa.slot_coverage_threshold,
                details=coverage_details,
            )
        )

        delayed_metric, delayed_details = self._metric_delayed_ratio(intraday)
        metrics.append(
            MetricResult(
                name="delayed_ratio",
                value=delayed_metric,
                threshold=self.cfg.qa.delayed_ratio_threshold,
                comparator="<=",
                passed=delayed_metric <= self.cfg.qa.delayed_ratio_threshold,
                details=delayed_details,
            )
        )

        fallback_metric, fallback_details = self._metric_rollup_fallback(daily)
        metrics.append(
            MetricResult(
                name="rollup_fallback_ratio",
                value=fallback_metric,
                threshold=self.cfg.qa.rollup_fallback_threshold,
                comparator="<=",
                passed=fallback_metric <= self.cfg.qa.rollup_fallback_threshold,
                details=fallback_details,
            )
        )

        oi_metric, oi_details = self._metric_oi_enrichment(daily)
        metrics.append(
            MetricResult(
                name="oi_enrichment_ratio",
                value=oi_metric,
                threshold=self.cfg.qa.oi_enrichment_threshold,
                comparator=">=",
                passed=oi_metric >= self.cfg.qa.oi_enrichment_threshold,
                details=oi_details,
            )
        )

        status = "PASS"
        for metric in metrics:
            if not metric.passed:
                status = "FAIL"
                breaches.append(metric.name)

        extra["intraday_rows"] = len(intraday)
        extra["daily_rows"] = len(daily)

        return QAMetricsResult(
            trade_date=trade_date,
            metrics=metrics,
            status=status,
            breaches=breaches,
            extra=extra,
        )

    def persist(self, result: QAMetricsResult) -> Path:
        metrics_dir = Path(self.cfg.paths.state) / "run_logs" / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        path = metrics_dir / f"metrics_{result.trade_date.strftime('%Y%m%d')}.json"
        path.write_text(
            json.dumps(result.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path

    def _metric_slot_coverage(self, intraday: pd.DataFrame) -> tuple[float, dict[str, Any]]:
        if intraday.empty:
            return 0.0, {"coverage_by_symbol": {}, "slots_expected": TOTAL_SLOTS}

        df = intraday.copy()
        df["slot_30m"] = pd.to_numeric(df["slot_30m"], errors="coerce")
        df.dropna(subset=["slot_30m"], inplace=True)
        grouped = df.groupby(df["underlying"].astype(str).str.upper())["slot_30m"].nunique()
        coverage_by_symbol = (grouped / TOTAL_SLOTS).to_dict()
        minimum = float(min(coverage_by_symbol.values())) if coverage_by_symbol else 0.0
        return minimum, {
            "coverage_by_symbol": coverage_by_symbol,
            "slots_expected": TOTAL_SLOTS,
        }

    def _metric_delayed_ratio(self, intraday: pd.DataFrame) -> tuple[float, dict[str, Any]]:
        if intraday.empty:
            return 0.0, {"rows": 0, "delayed_rows": 0}

        flags_series = intraday.get("data_quality_flag")
        delayed_mask = flags_series.apply(lambda x: "delayed_fallback" in _normalize_flags(x))
        if "market_data_type" in intraday.columns:
            delayed_mask |= intraday["market_data_type"].astype("Int64").fillna(1) != 1
        delayed_rows = int(delayed_mask.sum())
        total_rows = len(intraday)
        ratio = delayed_rows / total_rows if total_rows else 0.0
        return ratio, {"rows": total_rows, "delayed_rows": delayed_rows}

    def _metric_rollup_fallback(self, daily: pd.DataFrame) -> tuple[float, dict[str, Any]]:
        if daily.empty or "rollup_strategy" not in daily:
            return 1.0 if not daily.empty else 0.0, {
                "rows": len(daily),
                "fallback_rows": len(daily),
            }

        strategies = daily["rollup_strategy"].astype(str).str.lower()
        fallback_rows = int((strategies != "close").sum())
        total_rows = len(daily)
        ratio = fallback_rows / total_rows if total_rows else 0.0
        return ratio, {
            "rows": total_rows,
            "fallback_rows": fallback_rows,
        }

    def _metric_oi_enrichment(self, daily: pd.DataFrame) -> tuple[float, dict[str, Any]]:
        if daily.empty:
            return 0.0, {"rows": 0, "enriched_rows": 0, "missing_rows": 0}

        flags = daily.get("data_quality_flag")
        flags_list = flags.apply(_normalize_flags)
        missing_mask = flags_list.apply(lambda flg: "missing_oi" in flg)
        valid_mask = (~daily["open_interest"].isna()) & (~missing_mask)
        enriched_rows = int(valid_mask.sum())
        missing_rows = int(missing_mask.sum())
        total_rows = len(daily)
        ratio = enriched_rows / total_rows if total_rows else 0.0
        return ratio, {
            "rows": total_rows,
            "enriched_rows": enriched_rows,
            "missing_rows": missing_rows,
        }


def _normalize_flags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if str(v)]
    if isinstance(value, (tuple, set)):
        return [str(v) for v in value if str(v)]
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(v) for v in parsed if str(v)]
            except Exception:
                pass
        return [text]
    return [str(value)]


def _read_parquet_tree(root: Path) -> pd.DataFrame:
    if not root.exists():
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    for path in sorted(root.rglob("*.parquet")):
        try:
            frames.append(pd.read_parquet(path))
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
