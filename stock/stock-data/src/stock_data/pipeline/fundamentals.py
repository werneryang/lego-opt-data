from __future__ import annotations

import json
import logging
import os
import random
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, List
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from ..config import AppConfig
from ..ib import make_throttle
from ..storage import ParquetWriter, partition_for
from ..universe import load_universe

logger = logging.getLogger(__name__)


DEFAULT_REPORT_TYPES = ["info"]
ALLOWED_REPORT_TYPES = {
    "info",
    "financials",
    "balance_sheet",
    "cashflow",
    "calendar",
    "institutional_holders",
    "major_holders",
}

DEFAULT_FMP_BASE_URL = "https://financialmodelingprep.com/stable"


@dataclass
class FundamentalsResult:
    ingest_id: str
    trade_date: date
    symbols_processed: int
    rows_written: int
    paths: list[str]
    errors: list[dict[str, Any]]


def _parse_min_fields(report_type: str, payload: Any) -> dict[str, Any]:
    if report_type != "info" or not isinstance(payload, dict):
        return {"asof_date": None}

    def _float(value: Any) -> float | None:
        try:
            return float(value)
        except Exception:
            return None

    profile = payload.get("profile", {})
    metrics = payload.get("metrics_ttm", {})
    ratios = payload.get("ratios_ttm", {})
    return {
        "asof_date": None,
        "market_cap": _float(profile.get("mktCap") or profile.get("marketCap")),
        "pe_ttm": _float(
            ratios.get("priceToEarningsRatioTTM")
            or metrics.get("peRatioTTM")
            or metrics.get("peTTM")
        ),
        "eps_ttm": _float(
            ratios.get("netIncomePerShareTTM")
            or metrics.get("epsTTM")
            or metrics.get("eps")
        ),
        "sector": profile.get("sector"),
        "industry": profile.get("industry"),
    }


class FundamentalsRunner:
    def __init__(
        self,
        cfg: AppConfig,
        *,
        writer: ParquetWriter | None = None,
        now_fn: callable[[], datetime] | None = None,
        throttle_sec: float = 5.0,
        fmp_api_key: str | None = None,
        fmp_base_url: str = DEFAULT_FMP_BASE_URL,
    ) -> None:
        self.cfg = cfg
        self._writer = writer or ParquetWriter(cfg)
        self._now_fn = now_fn or (lambda: datetime.now(ZoneInfo(cfg.timezone.name)))
        self._throttle = make_throttle(throttle_sec)
        self._cache_dir = cfg.paths.state / "fundamentals_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._api_key = fmp_api_key or os.getenv("FMP_API_KEY") or ""
        self._base_url = fmp_base_url.rstrip("/")

    def run(
        self,
        *,
        trade_date: date | None = None,
        symbols: List[str] | None = None,
        exchange: str = "SMART",
        report_types: Iterable[str] | None = None,
        force_refresh: bool = False,
        cache_ttl_days: int | None = 7,
        max_symbols: int | None = None,
    ) -> FundamentalsResult:
        target_date = trade_date or self._now_fn().date()
        ingest_id = str(uuid.uuid4())
        errors: list[dict[str, Any]] = []

        if symbols is None:
            universe = load_universe(self.cfg.universe.file)
            symbols = [entry.symbol for entry in universe]
        if max_symbols is not None:
            symbols = symbols[: max(max_symbols, 0)]
        if not self._api_key:
            errors.append({"error": "missing_api_key", "message": "FMP API key is required"})
            return FundamentalsResult(
                ingest_id=ingest_id,
                trade_date=target_date,
                symbols_processed=0,
                rows_written=0,
                paths=[],
                errors=errors,
            )

        raw_types = list(report_types) if report_types else list(DEFAULT_REPORT_TYPES)
        types: list[str] = []
        for report_type in raw_types:
            if report_type in ALLOWED_REPORT_TYPES:
                types.append(report_type)
            else:
                errors.append(
                    {
                        "error": "invalid_report_type",
                        "report_type": report_type,
                        "message": "Report type is not supported by FMP fundamentals",
                    }
                )
        if not types:
            return FundamentalsResult(
                ingest_id=ingest_id,
                trade_date=target_date,
                symbols_processed=0,
                rows_written=0,
                paths=[],
                errors=errors,
            )

        paths: list[str] = []
        rows_written = 0

        for symbol in symbols:
            for report_type in types:
                self._throttle()
                cache_payload = self._load_cache(
                    symbol,
                    target_date,
                    report_type,
                    force_refresh=force_refresh,
                    cache_ttl_days=cache_ttl_days,
                )
                payload: Any = None
                raw_json: str
                if cache_payload is not None:
                    logger.info(
                        "fundamentals cache hit symbol=%s report_type=%s date=%s",
                        symbol,
                        report_type,
                        target_date.isoformat(),
                    )
                    raw_json = cache_payload["raw_json"]
                    try:
                        payload = json.loads(raw_json)
                    except json.JSONDecodeError:
                        payload = None
                    if payload in ({}, [], None):
                        payload = None
                        raw_json = ""
                        cache_payload = None
                else:
                    logger.info(
                        "fundamentals cache miss symbol=%s report_type=%s date=%s",
                        symbol,
                        report_type,
                        target_date.isoformat(),
                    )
                    payload = self._fetch_report(symbol, report_type)
                    if payload is None or payload in ({}, []):
                        errors.append(
                            {
                                "symbol": symbol,
                                "report_type": report_type,
                                "error": "missing_report",
                                "message": "No payload returned",
                            }
                        )
                        continue

                    raw_json = json.dumps(payload, ensure_ascii=False)
                    self._save_cache(symbol, target_date, report_type, raw_json)

                parsed = _parse_min_fields(report_type, payload)
                record = {
                    "trade_date": target_date,
                    "symbol": symbol,
                    "exchange": exchange,
                    "report_type": report_type,
                    "asof_date": parsed.get("asof_date"),
                    "raw_json": raw_json,
                    "market_cap": parsed.get("market_cap"),
                    "pe_ttm": parsed.get("pe_ttm"),
                    "eps_ttm": parsed.get("eps_ttm"),
                    "sector": parsed.get("sector"),
                    "industry": parsed.get("industry"),
                    "source": "FMP",
                    "asof_ts": datetime.utcnow(),
                    "ingest_id": ingest_id,
                    "ingest_run_type": "eod",
                    "data_quality_flag": [],
                }

                df = pd.DataFrame([record])
                part = partition_for(
                    self.cfg,
                    self.cfg.paths.clean / "view=fundamentals",
                    target_date,
                    symbol,
                    exchange,
                )
                path = self._writer.write_dataframe(df, part)
                rows_written += len(df)
                paths.append(str(path))

        return FundamentalsResult(
            ingest_id=ingest_id,
            trade_date=target_date,
            symbols_processed=len(symbols),
            rows_written=rows_written,
            paths=paths,
            errors=errors,
        )

    def _fetch_with_retry(
        self,
        url: str,
        params: dict[str, Any],
        *,
        max_attempts: int = 4,
        base_delay: float = 1.0,
        max_delay: float = 8.0,
        label: str = "",
    ) -> Any | None:
        last_exc: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                resp = requests.get(url, params=params, timeout=20)
                if resp.status_code == 429:
                    raise RuntimeError("FMP rate limit")
                resp.raise_for_status()
                payload = resp.json()
                if payload in (None, [], {}):
                    snippet = resp.text[:200].replace("\n", " ")
                    logger.warning(
                        "FMP empty payload label=%s status=%s body=%s",
                        label or url.split("?")[0],
                        resp.status_code,
                        snippet,
                    )
                return payload
            except Exception as exc:
                last_exc = exc
                if attempt >= max_attempts:
                    break
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                jitter = random.uniform(0, delay * 0.2)
                time.sleep(delay + jitter)
        if last_exc is not None:
            logger.warning("FMP fetch failed after retries: %s", last_exc)
        return None

    def _fetch_report(self, symbol: str, report_type: str) -> dict[str, Any] | list[Any] | None:
        symbol = symbol.upper()
        if report_type == "info":
            profile = self._fetch_with_retry(
                f"{self._base_url}/profile",
                {"apikey": self._api_key, "symbol": symbol},
                label=f"profile/{symbol}",
            )
            metrics = self._fetch_with_retry(
                f"{self._base_url}/key-metrics-ttm",
                {"apikey": self._api_key, "symbol": symbol},
                label=f"key-metrics-ttm/{symbol}",
            )
            ratios = self._fetch_with_retry(
                f"{self._base_url}/ratios-ttm",
                {"apikey": self._api_key, "symbol": symbol},
                label=f"ratios-ttm/{symbol}",
            )
            if profile is None and metrics is None:
                return None
            profile_row = profile[0] if isinstance(profile, list) and profile else {}
            metrics_row = metrics[0] if isinstance(metrics, list) and metrics else {}
            ratios_row = ratios[0] if isinstance(ratios, list) and ratios else {}
            if not profile_row and not metrics_row and not ratios_row:
                return None
            return {
                "profile": profile_row,
                "metrics_ttm": metrics_row,
                "ratios_ttm": ratios_row,
            }

        endpoint_map = {
            "financials": "income-statement",
            "balance_sheet": "balance-sheet-statement",
            "cashflow": "cash-flow-statement",
            "calendar": "earnings-calendar",
            "institutional_holders": "institutional-holder",
            "major_holders": "major-holders",
        }
        endpoint = endpoint_map.get(report_type)
        if not endpoint:
            return None

        params = {"apikey": self._api_key, "symbol": symbol}
        if report_type in {"financials", "balance_sheet", "cashflow"}:
            params["limit"] = 4
        if report_type == "calendar":
            params = {"apikey": self._api_key}
        payload = self._fetch_with_retry(
            f"{self._base_url}/{endpoint}",
            params,
            label=endpoint,
        )
        if payload in (None, [], {}):
            return None
        return payload

    def _cache_path(self, symbol: str, trade_date: date, report_type: str) -> Path:
        safe_type = report_type.replace("/", "_")
        return self._cache_dir / f"{symbol}_{trade_date.isoformat()}_{safe_type}.json"

    def _load_cache(
        self,
        symbol: str,
        trade_date: date,
        report_type: str,
        *,
        force_refresh: bool,
        cache_ttl_days: int | None,
    ) -> dict[str, Any] | None:
        if force_refresh:
            return None
        path = self._cache_path(symbol, trade_date, report_type)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(payload, dict) or "raw_json" not in payload:
            return None
        if cache_ttl_days is not None:
            cached_at = payload.get("cached_at")
            if isinstance(cached_at, str):
                try:
                    cached_dt = datetime.fromisoformat(cached_at.replace("Z", "+00:00"))
                    if cached_dt.tzinfo is None:
                        cached_dt = cached_dt.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    if now - cached_dt > timedelta(days=cache_ttl_days):
                        return None
                except ValueError:
                    return None
        return payload

    def _save_cache(self, symbol: str, trade_date: date, report_type: str, raw_json: str) -> None:
        path = self._cache_path(symbol, trade_date, report_type)
        payload = {
            "symbol": symbol,
            "trade_date": trade_date.isoformat(),
            "report_type": report_type,
            "raw_json": raw_json,
            "cached_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if raw_json in ("", "{}", "[]", "null"):
            return
        try:
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to write fundamentals cache %s: %s", path, exc)
