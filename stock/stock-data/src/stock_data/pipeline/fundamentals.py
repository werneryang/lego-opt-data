## 标记此文件需要FMP 权限确认才能用 ！！！

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
DEFAULT_FMP_API_KEY = "ENJg1ZneTg5DEPsN21fEsMbNUl5OLecF"
DEFAULT_FUNDAMENTALS_STATE_FILE = "fundamentals_state.json"
DEFAULT_DAILY_CALL_LIMIT = 240
DEFAULT_MIN_FETCH_DAYS = 7
DEFAULT_INFO_REFRESH_DAYS = 30
DEFAULT_STATEMENT_REFRESH_DAYS = 85
DEFAULT_STATEMENT_LIMIT = 20
DEFAULT_STATEMENT_PERIOD = "quarter"

STATEMENT_REPORT_TYPES = {"financials", "balance_sheet", "cashflow"}


@dataclass
class FundamentalsResult:
    ingest_id: str
    trade_date: date
    symbols_processed: int
    rows_written: int
    paths: list[str]
    errors: list[dict[str, Any]]


class DailyBudgetExceeded(RuntimeError):
    pass


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
        daily_call_limit: int = DEFAULT_DAILY_CALL_LIMIT,
        min_fetch_days: int = DEFAULT_MIN_FETCH_DAYS,
        info_refresh_days: int = DEFAULT_INFO_REFRESH_DAYS,
        statement_refresh_days: int = DEFAULT_STATEMENT_REFRESH_DAYS,
        statement_limit: int = DEFAULT_STATEMENT_LIMIT,
        statement_period: str = DEFAULT_STATEMENT_PERIOD,
        state_path: Path | None = None,
    ) -> None:
        self.cfg = cfg
        self._writer = writer or ParquetWriter(cfg)
        self._now_fn = now_fn or (lambda: datetime.now(ZoneInfo(cfg.timezone.name)))
        self._throttle = make_throttle(throttle_sec)
        self._cache_dir = cfg.paths.state / "fundamentals_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._api_key = fmp_api_key or os.getenv("FMP_API_KEY") or DEFAULT_FMP_API_KEY
        self._base_url = fmp_base_url.rstrip("/")
        self._daily_call_limit = max(int(daily_call_limit), 0)
        self._min_fetch_days = max(int(min_fetch_days), 0)
        self._info_refresh_days = max(int(info_refresh_days), 0)
        self._statement_refresh_days = max(int(statement_refresh_days), 0)
        self._statement_limit = max(int(statement_limit), 0)
        self._statement_period = statement_period
        self._state_path = state_path or (cfg.paths.state / DEFAULT_FUNDAMENTALS_STATE_FILE)
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        default_state: dict[str, Any] = {
            "version": 1,
            "last_run_date": None,
            "daily_calls": 0,
            "symbols": {},
        }
        if not self._state_path.exists():
            return default_state
        try:
            payload = json.loads(self._state_path.read_text(encoding="utf-8"))
        except Exception:
            return default_state
        if not isinstance(payload, dict):
            return default_state
        payload.setdefault("version", 1)
        payload.setdefault("last_run_date", None)
        payload.setdefault("daily_calls", 0)
        symbols = payload.get("symbols")
        if not isinstance(symbols, dict):
            payload["symbols"] = {}
        return payload

    def _save_state(self) -> None:
        try:
            self._state_path.write_text(json.dumps(self._state), encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to write fundamentals state %s: %s", self._state_path, exc)

    def _reset_daily_state(self, target_date: date) -> None:
        date_key = target_date.isoformat()
        if self._state.get("last_run_date") != date_key:
            self._state["last_run_date"] = date_key
            self._state["daily_calls"] = 0

    def _remaining_calls(self) -> int:
        daily_calls = self._state.get("daily_calls")
        if not isinstance(daily_calls, int):
            daily_calls = 0
            self._state["daily_calls"] = daily_calls
        return max(self._daily_call_limit - daily_calls, 0)

    def _consume_call(self, label: str = "") -> None:
        if self._remaining_calls() <= 0:
            raise DailyBudgetExceeded("Daily call budget reached")
        self._state["daily_calls"] = int(self._state.get("daily_calls", 0)) + 1

    def _calls_for_report_type(self, report_type: str) -> int:
        if report_type == "info":
            return 3
        return 1

    def _parse_date(self, value: Any) -> date | None:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                return None
        return None

    def _parse_datetime(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _report_state(self, symbol: str, report_type: str) -> dict[str, Any]:
        symbols_state = self._state.setdefault("symbols", {})
        symbol_state = symbols_state.setdefault(symbol, {})
        report_state = symbol_state.setdefault(report_type, {})
        if not isinstance(report_state, dict):
            report_state = {}
            symbol_state[report_type] = report_state
        return report_state

    def _update_report_state(self, symbol: str, report_type: str, **updates: Any) -> None:
        report_state = self._report_state(symbol, report_type)
        report_state.update(updates)

    def _latest_payload_meta(self, payload: Any) -> tuple[date | None, str | None, int]:
        if isinstance(payload, list) and payload:
            row = payload[0]
            latest_date = self._parse_date(row.get("date"))
            period = row.get("period") if isinstance(row, dict) else None
            return latest_date, period, len(payload)
        if isinstance(payload, dict):
            return None, None, 1
        return None, None, 0

    def _load_cached_payload(self, cache_path: str | None) -> dict[str, Any] | None:
        if not cache_path:
            return None
        path = Path(cache_path)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(payload, dict) or "raw_json" not in payload:
            return None
        return payload

    def _should_fetch_report(
        self,
        symbol: str,
        report_type: str,
        target_date: date,
        *,
        force_refresh: bool,
    ) -> tuple[bool, str]:
        if force_refresh:
            return True, ""
        report_state = self._report_state(symbol, report_type)
        last_fetch_at = self._parse_datetime(report_state.get("last_fetch_at"))
        if last_fetch_at is not None:
            days_since_fetch = (target_date - last_fetch_at.date()).days
            if days_since_fetch < self._min_fetch_days:
                return False, "recent_fetch"
            if report_type == "info" and days_since_fetch < self._info_refresh_days:
                return False, "info_not_due"
        if report_type in STATEMENT_REPORT_TYPES:
            last_payload_date = self._parse_date(report_state.get("last_payload_date"))
            if last_payload_date is not None:
                days_since_payload = (target_date - last_payload_date).days
                if days_since_payload < self._statement_refresh_days:
                    return False, "statement_not_due"
        return True, ""

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

        self._reset_daily_state(target_date)
        paths: list[str] = []
        rows_written = 0
        symbols_processed = 0
        stopped_early = False
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        for symbol in symbols:
            symbol = symbol.upper()
            for report_type in types:
                should_fetch, skip_reason = self._should_fetch_report(
                    symbol,
                    report_type,
                    target_date,
                    force_refresh=force_refresh,
                )
                if not should_fetch:
                    report_state = self._report_state(symbol, report_type)
                    cached_state_payload = self._load_cached_payload(
                        report_state.get("last_cache_path")
                    )
                    cached_at = None
                    if cached_state_payload is not None and cache_ttl_days is not None:
                        cached_at = self._parse_datetime(cached_state_payload.get("cached_at"))
                        if cached_at is None:
                            cached_state_payload = None
                        else:
                            age = datetime.now(timezone.utc) - cached_at
                            if age > timedelta(days=cache_ttl_days):
                                cached_state_payload = None
                    payload = None
                    raw_json = ""
                    if cached_state_payload is not None:
                        raw_json = cached_state_payload.get("raw_json", "")
                        try:
                            payload = json.loads(raw_json)
                        except json.JSONDecodeError:
                            payload = None
                    if payload in ({}, [], None):
                        self._update_report_state(
                            symbol,
                            report_type,
                            last_attempt_at=now_iso,
                            status=f"skipped_{skip_reason}",
                        )
                        continue
                    status = f"cache_reuse_{skip_reason}"
                    if cached_at is None:
                        cached_at = datetime.now(timezone.utc)
                    last_payload_date, last_period, payload_count = self._latest_payload_meta(
                        payload
                    )
                    self._update_report_state(
                        symbol,
                        report_type,
                        last_attempt_at=now_iso,
                        last_fetch_at=cached_at.isoformat().replace("+00:00", "Z"),
                        last_payload_date=last_payload_date.isoformat()
                        if last_payload_date
                        else None,
                        last_period=last_period,
                        payload_count=payload_count,
                        status=status,
                    )
                else:
                    calls_needed = self._calls_for_report_type(report_type)
                    if self._remaining_calls() < calls_needed:
                        self._update_report_state(
                            symbol,
                            report_type,
                            last_attempt_at=now_iso,
                            status="skipped_budget",
                        )
                        errors.append(
                            {
                                "symbol": symbol,
                                "report_type": report_type,
                                "error": "daily_budget_exceeded",
                                "message": "Daily call budget reached",
                            }
                        )
                        stopped_early = True
                        break

                    self._throttle()
                    cache_payload = self._load_cache(
                        symbol,
                        target_date,
                        report_type,
                        force_refresh=force_refresh,
                        cache_ttl_days=cache_ttl_days,
                    )
                    payload = None
                    raw_json = ""
                    cache_path: Path | None = None
                    status = "fetched"
                    last_fetch_at: datetime | None = None
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
                            status = "cache_hit"
                            cached_at = self._parse_datetime(cache_payload.get("cached_at"))
                            if cached_at is not None:
                                last_fetch_at = cached_at
                            cache_path = self._cache_path(symbol, target_date, report_type)
                    if cache_payload is None:
                        logger.info(
                            "fundamentals cache miss symbol=%s report_type=%s date=%s",
                            symbol,
                            report_type,
                            target_date.isoformat(),
                        )
                        try:
                            payload = self._fetch_report(symbol, report_type)
                        except DailyBudgetExceeded:
                            self._update_report_state(
                                symbol,
                                report_type,
                                last_attempt_at=now_iso,
                                status="skipped_budget",
                            )
                            errors.append(
                                {
                                    "symbol": symbol,
                                    "report_type": report_type,
                                    "error": "daily_budget_exceeded",
                                    "message": "Daily call budget reached",
                                }
                            )
                            stopped_early = True
                            break
                        if payload is None or payload in ({}, []):
                            errors.append(
                                {
                                    "symbol": symbol,
                                    "report_type": report_type,
                                    "error": "missing_report",
                                    "message": "No payload returned",
                                }
                            )
                            self._update_report_state(
                                symbol,
                                report_type,
                                last_attempt_at=now_iso,
                                status="missing_report",
                            )
                            continue

                        raw_json = json.dumps(payload, ensure_ascii=False)
                        cache_path = self._save_cache(symbol, target_date, report_type, raw_json)
                        last_fetch_at = datetime.now(timezone.utc)

                    last_payload_date, last_period, payload_count = self._latest_payload_meta(
                        payload
                    )
                    self._update_report_state(
                        symbol,
                        report_type,
                        last_attempt_at=now_iso,
                        last_fetch_at=last_fetch_at.isoformat().replace("+00:00", "Z")
                        if last_fetch_at
                        else None,
                        last_payload_date=last_payload_date.isoformat()
                        if last_payload_date
                        else None,
                        last_period=last_period,
                        payload_count=payload_count,
                        last_cache_path=str(cache_path) if cache_path else None,
                        status=status,
                    )

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
            symbols_processed += 1
            self._save_state()
            if stopped_early:
                break

        return FundamentalsResult(
            ingest_id=ingest_id,
            trade_date=target_date,
            symbols_processed=symbols_processed,
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
                self._consume_call()
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
            except DailyBudgetExceeded:
                raise
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
            params["limit"] = self._statement_limit
            params["period"] = self._statement_period
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

    def _save_cache(
        self, symbol: str, trade_date: date, report_type: str, raw_json: str
    ) -> Path | None:
        path = self._cache_path(symbol, trade_date, report_type)
        payload = {
            "symbol": symbol,
            "trade_date": trade_date.isoformat(),
            "report_type": report_type,
            "raw_json": raw_json,
            "cached_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if raw_json in ("", "{}", "[]", "null"):
            return None
        try:
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return path
        except Exception as exc:
            logger.warning("Failed to write fundamentals cache %s: %s", path, exc)
        return None
