from __future__ import annotations

import asyncio
import logging
import math
from typing import Any, Callable, Dict, List, Optional, Sequence

from opt_data.util.performance import log_performance
from opt_data.util.log_context import LogContext

logger = logging.getLogger(__name__)

DEFAULT_GENERIC_TICKS = "100,101,104,105,106,165,221,225,233,293,294,295"
DEFAULT_TIMEOUT = 12.0  # seconds
DEFAULT_POLL_INTERVAL = 0.25


@log_performance(logger, "collect_option_snapshots")
def collect_option_snapshots(
    ib: Any,
    contracts: Sequence[Dict[str, Any]],
    *,
    generic_ticks: str = DEFAULT_GENERIC_TICKS,
    timeout: float = DEFAULT_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    acquire_token: Optional[Callable[[], None]] = None,
    require_greeks: bool = True,
    concurrency: int = 40,
    metrics: Optional[Any] = None,
    alerts: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Collect option snapshots concurrently using asyncio.
    
    Args:
        ib: Interactive Brokers connection object
        contracts: Sequence of contract dictionaries to fetch data for
        generic_ticks: Comma-separated list of generic tick types
        timeout: Maximum time to wait for each contract's data (seconds)
        poll_interval: How often to check if data is ready (seconds)
        acquire_token: Optional rate-limiting callback
        require_greeks: Whether to require Greeks data for completion
        concurrency: Maximum number of concurrent requests
        
    Returns:
        List of dictionaries containing market data for each contract.
        Failed contracts will have error information in the result.
        
    Raises:
        RuntimeError: If ib.run() fails catastrophically
    """
    try:
        # If the loop is already running (e.g. in a notebook or existing async context),
        # we should use it. Otherwise, run_until_complete.
        # For CLI usage, ib.run() is typically used to bridge sync/async.
        return ib.run(
            _collect_async(
                ib,
                contracts,
                generic_ticks=generic_ticks,
                timeout=timeout,
                poll_interval=poll_interval,
                acquire_token=acquire_token,
                require_greeks=require_greeks,
                concurrency=concurrency,
                metrics=metrics,
                alerts=alerts,
            )
        )
    except Exception as e:
        logger.exception(
            f"Critical error in collect_option_snapshots: {type(e).__name__}: {e}"
        )
        # Re-raise as RuntimeError to signal that the entire collection failed
        raise RuntimeError(
            f"Failed to collect option snapshots: {type(e).__name__}: {e}"
        ) from e


async def _collect_async(
    ib: Any,
    contracts: Sequence[Dict[str, Any]],
    *,
    generic_ticks: str,
    timeout: float,
    poll_interval: float,
    acquire_token: Optional[Callable[[], None]],
    require_greeks: bool,
    concurrency: int,
    metrics: Optional[Any],
    alerts: Optional[Any],
) -> List[Dict[str, Any]]:
    """Async implementation of the snapshot collection logic."""
    from ib_insync import Option  # type: ignore

    # 1. Prepare Option objects
    # We do this upfront to avoid overhead during the async loop.
    option_objs = []
    for info in contracts:
        conid = info.get("conid")
        if conid:
            opt = Option(conId=int(conid))
            opt.exchange = info.get("exchange", "SMART")
            opt.currency = info.get("currency", "USD")
        else:
            # Fallback for contracts without conId (less reliable)
            expiry = info.get("expiry", "").replace("-", "")
            opt = Option(
                info["symbol"],
                expiry,
                info["strike"],
                info["right"],
                exchange=info.get("exchange", "SMART"),
            )
            opt.currency = info.get("currency", "USD")
            if info.get("tradingClass"):
                opt.tradingClass = info["tradingClass"]
            if info.get("multiplier"):
                opt.multiplier = str(info["multiplier"])
            opt.includeExpired = True
        
        # Attach original info to the object for easy retrieval later
        opt._origin_info = info
        option_objs.append(opt)

    results: List[Dict[str, Any]] = []
    sem = asyncio.Semaphore(concurrency)

    def _build_error_row(
        info: Dict[str, Any],
        error_type: str,
        error_message: str,
    ) -> Dict[str, Any]:
        """Build an error row when data collection fails for a contract."""
        return {
            **info,
            "bid": None,
            "ask": None,
            "mid": None,
            "last": None,
            "open": None,
            "high": None,
            "low": None,
            "close": None,
            "bid_size": None,
            "ask_size": None,
            "last_size": None,
            "volume": None,
            "vwap": None,
            "iv": None,
            "delta": None,
            "gamma": None,
            "theta": None,
            "vega": None,
            "market_data_type": None,
            "asof": None,
            "open_interest": None,
            "price_ready": False,
            "greeks_ready": False,
            "snapshot_timed_out": False,
            "snapshot_error": True,
            "error_type": error_type,
            "error_message": error_message,
        }

    async def fetch_one(opt: Any) -> Dict[str, Any]:
        """Fetch market data for a single option contract with comprehensive error handling."""
        ticker = None
        error_occurred = False
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        
        async with sem:
            try:
                # Rate limiting hook
                if acquire_token:
                    try:
                        # Note: acquire_token is likely sync, so we call it directly.
                        # If it blocks, it blocks the loop, but usually it's a fast token bucket check.
                        acquire_token()
                    except Exception as e:
                        logger.warning(
                            f"Rate limit acquisition failed for {opt.symbol} "
                            f"{opt.strike} {opt.right}: {e}"
                        )
                        # Continue anyway - rate limit failure shouldn't block data collection

                # Subscribe to market data
                try:
                    ticker = ib.reqMktData(opt, genericTickList=generic_ticks, snapshot=False)
                except Exception as e:
                    logger.error(
                        f"Failed to subscribe to market data for {opt.symbol} "
                        f"{opt.strike} {opt.right}: {type(e).__name__}: {e}"
                    )
                    return _build_error_row(
                        opt._origin_info,
                        error_type="subscription_failed",
                        error_message=f"{type(e).__name__}: {str(e)}"
                    )
                
                # Wait for data with timeout
                try:
                    loop = asyncio.get_running_loop()
                    start_time = loop.time()
                    
                    while (loop.time() - start_time) < timeout:
                        price_ready = _has_price(ticker)
                        greeks_ready = _has_greeks(ticker)
                        
                        if price_ready and (not require_greeks or greeks_ready):
                            break
                        
                        await asyncio.sleep(poll_interval)
                    
                except asyncio.TimeoutError as e:
                    logger.warning(
                        f"Timeout waiting for data: {opt.symbol} "
                        f"{opt.strike} {opt.right}"
                    )
                    return _build_error_row(
                        opt._origin_info,
                        error_type="timeout",
                        error_message=f"Data not ready after {timeout}s"
                    )
                    error_occurred = True
                    return result
                except asyncio.CancelledError:
                    logger.info(
                        f"Data collection cancelled for {opt.symbol} "
                        f"{opt.strike} {opt.right}"
                    )
                    raise  # Re-raise to allow proper cancellation handling
                except Exception as e:
                    logger.error(
                        f"Unexpected error while waiting for data: {opt.symbol} "
                        f"{opt.strike} {opt.right}: {type(e).__name__}: {e}"
                    )
                    return _build_error_row(
                        opt._origin_info,
                        error_type="data_collection_error",
                        error_message=f"{type(e).__name__}: {str(e)}"
                    )

                # Check final state and build result
                try:
                    price_ready = _has_price(ticker)
                    greeks_ready = _has_greeks(ticker)
                    timed_out = not (price_ready and (not require_greeks or greeks_ready))

                    row = _build_row(
                        opt._origin_info,
                        ticker,
                        price_ready=price_ready,
                        greeks_ready=greeks_ready,
                        timed_out=timed_out,
                    )
                    return row
                    
                except Exception as e:
                    logger.error(
                        f"Error building result row for {opt.symbol} "
                        f"{opt.strike} {opt.right}: {type(e).__name__}: {e}"
                    )
                    return _build_error_row(
                        opt._origin_info,
                        error_type="row_building_error",
                        error_message=f"{type(e).__name__}: {str(e)}"
                    )
                    
            except Exception as e:
                # Catch-all for any unexpected errors
                logger.exception(
                    f"Unexpected error in fetch_one for {opt.symbol} "
                    f"{opt.strike} {opt.right}: {type(e).__name__}: {e}"
                )
                error_occurred = True
                return _build_error_row(
                    opt._origin_info,
                    error_type="unexpected_error",
                    error_message=f"{type(e).__name__}: {str(e)}"
                )
                
            finally:
                duration = (loop.time() - start_time) * 1000
                if metrics:
                    tags = {"symbol": opt.symbol, "exchange": opt.exchange}
                    metrics.timing("snapshot.fetch.duration", duration, tags)
                    metrics.count("snapshot.fetch.total", 1, tags)
                    if error_occurred:
                        metrics.count("snapshot.fetch.error", 1, tags)
                    else:
                        metrics.count("snapshot.fetch.success", 1, tags)

                # Always unsubscribe to prevent resource leaks
                # We use cancelMktData to stop the stream.
                if ticker is not None:
                    try:
                        ib.cancelMktData(opt)
                    except Exception as e:
                        # Log but don't raise - cleanup failure shouldn't break the flow
                        logger.warning(
                            f"Failed to cancel market data for {opt.symbol} "
                            f"{opt.strike} {opt.right}: {type(e).__name__}: {e}"
                        )

    # 2. Run all tasks
    # asyncio.gather will run them concurrently, limited by the Semaphore.
    tasks = [fetch_one(opt) for opt in option_objs]
    if tasks:
        try:
            batch_results = await asyncio.gather(*tasks, return_exceptions=False)
            results.extend(batch_results)
        except Exception as e:
            logger.error(f"Error in gather operation: {type(e).__name__}: {e}")
            # If gather fails entirely, we still want to return partial results if any
            # In this case, we log the error but don't crash

    return results


def _has_price(ticker: Any) -> bool:
    for attr in ("last", "close", "bid", "ask"):
        value = getattr(ticker, attr, None)
        if value is None:
            continue
        try:
            if not math.isnan(float(value)):
                return True
        except (TypeError, ValueError):
            return True
    return False


def _has_greeks(ticker: Any) -> bool:
    model = getattr(ticker, "modelGreeks", None)
    if not model:
        return False
    for attr in ("impliedVol", "delta", "gamma", "theta", "vega"):
        value = getattr(model, attr, None)
        if value is None:
            return False
        try:
            if math.isnan(float(value)):
                return False
        except (TypeError, ValueError):
            return False
    return True


def _build_row(
    info: Dict[str, Any],
    ticker: Any,
    *,
    price_ready: bool,
    greeks_ready: bool,
    timed_out: bool,
) -> Dict[str, Any]:
    model = getattr(ticker, "modelGreeks", None)
    bid_g = getattr(ticker, "bidGreeks", None)
    ask_g = getattr(ticker, "askGreeks", None)
    last_g = getattr(ticker, "lastGreeks", None)

    bid = _to_float(getattr(ticker, "bid", None))
    ask = _to_float(getattr(ticker, "ask", None))
    mid = None
    if bid is not None and ask is not None:
        mid = (bid + ask) / 2.0

    timestamp = getattr(ticker, "time", None)

    row = {
        **info,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "last": _to_float(getattr(ticker, "last", None)),
        "open": _to_float(getattr(ticker, "open", None)),
        "high": _to_float(getattr(ticker, "high", None)),
        "low": _to_float(getattr(ticker, "low", None)),
        "close": _to_float(getattr(ticker, "close", None)),
        "bid_size": _to_float(getattr(ticker, "bidSize", None)),
        "ask_size": _to_float(getattr(ticker, "askSize", None)),
        "last_size": _to_float(getattr(ticker, "lastSize", None)),
        "volume": _to_float(getattr(ticker, "volume", None)),
        "vwap": _to_float(getattr(ticker, "vwap", None)),
        "rt_last": None,
        "rt_size": None,
        "rt_time": None,
        "rt_totalVolume": None,
        "rt_vwap": None,
        "rt_single": None,
        "iv": _safe_get(model, "impliedVol"),
        "delta": _safe_get(model, "delta"),
        "gamma": _safe_get(model, "gamma"),
        "theta": _safe_get(model, "theta"),
        "vega": _safe_get(model, "vega"),
        "market_data_type": getattr(ticker, "marketDataType", None),
        "asof": timestamp.isoformat() if timestamp else None,
        "open_interest": getattr(ticker, "openInterest", None),
        "price_ready": price_ready,
        "greeks_ready": greeks_ready,
        "snapshot_timed_out": timed_out,
        "snapshot_error": timed_out,  # Mark timeout as error per requirements
        "error_type": "timeout" if timed_out else None,
        "error_message": "Data not ready" if timed_out else None,
    }

    row.update(_parse_rt_volume(getattr(ticker, "rtVolume", "")))
    row["bid_iv"] = _safe_get(bid_g, "impliedVol")
    row["ask_iv"] = _safe_get(ask_g, "impliedVol")
    row["last_iv"] = _safe_get(last_g, "impliedVol")
    return row


def _safe_get(obj: Any, attr: str) -> float | None:
    if not obj:
        return None
    value = getattr(obj, attr, None)
    return _to_float(value)


def _parse_rt_volume(rt: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "rt_last": None,
        "rt_size": None,
        "rt_time": None,
        "rt_totalVolume": None,
        "rt_vwap": None,
        "rt_single": None,
    }
    if not rt:
        return out
    parts = str(rt).split(";")
    if len(parts) >= 6:
        out["rt_last"] = _to_float(parts[0])
        out["rt_size"] = _to_int(parts[1])
        out["rt_time"] = _to_int(parts[2])
        out["rt_totalVolume"] = _to_int(parts[3])
        out["rt_vwap"] = _to_float(parts[4])
        flag = parts[5].strip().lower()
        out["rt_single"] = flag in {"true", "1", "t", "y", "yes"}
    return out


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
