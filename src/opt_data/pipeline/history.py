from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ib_insync import IB

from ..config import AppConfig
from ..ib import IBSession, make_throttle, fetch_option_daily_aggregated
from ..ib.discovery import discover_contracts_for_symbol
from ..universe import load_universe

logger = logging.getLogger(__name__)


class HistoryRunner:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.throttle = make_throttle(cfg.acquisition.throttle_sec)

    def run(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: Optional[int] = None,
        output_dir: Optional[Path] = None,
        what_to_show: str = "MIDPOINT",
        use_rth: bool = True,
        force_refresh: bool = False,
        incremental: bool = False,
        bar_size: str = "8 hours",
        progress_callback: Optional[Callable[[int, int, str, Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run history collection for specified symbols.
        
        Args:
            symbols: List of symbols to process (defaults to universe)
            start_date: Start date for contract discovery/validity
            end_date: End date (not strictly used for history duration, but for cache)
            days: Number of days of history to fetch (e.g. 365)
            output_dir: Directory to save JSON files
            what_to_show: Data type (MIDPOINT, TRADES, etc.)
            use_rth: Whether to use Regular Trading Hours
            force_refresh: Force refresh contract cache
            incremental: If True, only fetch missing days based on existing data
            bar_size: Bar size to use (default "8 hours")
            progress_callback: Callback(current, total, status, details)
        """
        if not output_dir:
            output_dir = self.cfg.paths.clean / "ib" / "history"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load universe if symbols not provided
        if not symbols:
            universe = load_universe(Path(self.cfg.universe.file))
            symbols = [u.symbol for u in universe]
            
        # Use today as reference date if not provided
        ref_date = end_date or date.today()
        
        results = {
            "processed": 0,
            "errors": 0,
            "symbols": {}
        }

        session = IBSession(
            host=self.cfg.ib.host,
            port=self.cfg.ib.port,
            client_id=self.cfg.ib.client_id,
            client_id_pool=self.cfg.ib.client_id_pool,
            market_data_type=self.cfg.ib.market_data_type,
        )

        total_symbols = len(symbols)
        
        with session as sess:
            ib = sess.ensure_connected()
            
            for i, symbol in enumerate(symbols):
                logger.info(f"Processing history for {symbol}...")
                symbol_stats = {"contracts": 0, "bars": 0, "errors": 0}
                
                # Report progress start
                if progress_callback:
                    progress_callback(i, total_symbols, f"Starting {symbol}", {})

                try:
                    # Determine duration based on incremental logic
                    duration_str = f"{days or 30} D"
                    
                    if incremental:
                        # Check existing data
                        symbol_dir = output_dir / symbol
                        if symbol_dir.exists():
                            # Find max date folder
                            existing_dates = sorted([d.name for d in symbol_dir.iterdir() if d.is_dir()])
                            if existing_dates:
                                last_date_str = existing_dates[-1]
                                try:
                                    last_date = date.fromisoformat(last_date_str)
                                    # Calculate gap
                                    gap_days = (ref_date - last_date).days
                                    if gap_days <= 0:
                                        logger.info(f"Skipping {symbol}: Up to date (last: {last_date})")
                                        if progress_callback:
                                            progress_callback(i + 1, total_symbols, f"Skipped {symbol} (Up to date)", {})
                                        continue
                                    
                                    # Fetch gap + buffer (e.g. 1 day)
                                    duration_str = f"{gap_days} D"
                                    logger.info(f"Incremental fetch for {symbol}: {duration_str} (last: {last_date})")
                                except ValueError:
                                    pass

                    # 1. Resolve underlying conid
                    from ib_insync import Stock, Index
                    
                    # Try Stock first
                    contract = Stock(symbol, "SMART", "USD")
                    qualified = ib.qualifyContracts(contract)
                    if not qualified:
                        # Try Index
                        contract = Index(symbol, "CBOE", "USD")
                        qualified = ib.qualifyContracts(contract)
                    
                    if not qualified:
                        logger.error(f"Could not resolve underlying conid for {symbol}")
                        continue
                        
                    underlying_conid = qualified[0].conId
                    logger.info(f"Resolved {symbol} to conid {underlying_conid}")

                    # 2. Fetch reference price for filtering
                    # We need a price to filter strikes. 
                    # If ref_date is today, we could use live price, but historical close is safer/consistent.
                    # Let's fetch the daily bar for ref_date (or the last available day).
                    from ..ib import fetch_daily
                    
                    # We need to construct a Contract for the underlying
                    underlying_contract = qualified[0]
                    
                    end_dt = ""
                    if ref_date:
                        # Format as YYYYMMDD 23:59:59
                        end_dt = f"{ref_date.strftime('%Y%m%d')} 23:59:59"
                        
                    bars = ib.reqHistoricalData(
                        underlying_contract,
                        endDateTime=end_dt,
                        durationStr="2 D",
                        barSizeSetting="1 day",
                        whatToShow="TRADES",
                        useRTH=True,
                        formatDate=1,
                        keepUpToDate=False
                    )
                    
                    ref_price = 0.0
                    if bars:
                        ref_price = bars[-1].close
                        logger.info(f"Fetched reference price for {symbol}: {ref_price}")
                    else:
                        logger.warning(f"Could not fetch reference price for {symbol}; using 0.0 (discovery may fail)")

                    # 3. Discover contracts (using cache or live)
                    contracts = discover_contracts_for_symbol(
                        sess,
                        symbol,
                        ref_date,
                        ref_price,
                        self.cfg,
                        underlying_conid=underlying_conid,
                        allow_rebuild=True,
                        force_refresh=force_refresh
                    )
                    
                    logger.info(f"Discovered {len(contracts)} contracts for {symbol}")
                    
                    if not contracts:
                        logger.warning(f"No contracts found for {symbol}")
                        continue
                        
                    # 2. Fetch history for each contract
                    # Use ref_date for directory structure, even if incremental
                    # Ideally we should store by date of data, but here we store by run date/ref date
                    # If incremental, we might want to append to existing? 
                    # The current structure is history/SYMBOL/DATE/conid.json
                    # If we run incremental for today, we create a new DATE folder.
                    # This is fine.
                    
                    current_run_dir = output_dir / symbol / ref_date.isoformat()
                    current_run_dir.mkdir(parents=True, exist_ok=True)
                    
                    total_contracts = len(contracts)
                    for c_idx, contract_dict in enumerate(contracts):
                        try:
                            # Reconstruct Contract object
                            # Note: discover_contracts_for_symbol returns dicts
                            from ib_insync import Contract, Option
                            
                            c = contract_dict
                            contract = Option(
                                symbol=c.get("symbol"),
                                lastTradeDateOrContractMonth=c.get("expiry", "").replace("-", ""),
                                strike=float(c.get("strike", 0)),
                                right=c.get("right"),
                                exchange=c.get("exchange", "SMART"),
                                currency=c.get("currency", "USD"),
                                tradingClass=c.get("tradingClass"),
                                multiplier=str(c.get("multiplier", "100"))
                            )
                            contract.conId = int(c.get("conid", 0))
                            contract.includeExpired = True
                            
                            # Use fetch_option_daily_aggregated which handles 8-hour aggregation
                            # If bar_size is not 8 hours, we might need direct fetch?
                            # But fetch_option_daily_aggregated is hardcoded for 8 hours logic.
                            # If user asks for '1 hour', we should use standard fetch?
                            # For now, assume bar_size="8 hours" uses the aggregator, others use standard (if supported)
                            
                            if bar_size == "8 hours":
                                bars = fetch_option_daily_aggregated(
                                    ib,
                                    contract,
                                    what_to_show=what_to_show,
                                    duration=duration_str,
                                    use_rth=use_rth,
                                    throttle=self.throttle
                                )
                            else:
                                # Fallback to standard fetch (might fail for 1 day)
                                # But useful for 1 hour etc.
                                bars = ib.reqHistoricalData(
                                    contract,
                                    endDateTime=end_dt,
                                    durationStr=duration_str,
                                    barSizeSetting=bar_size,
                                    whatToShow=what_to_show,
                                    useRTH=use_rth,
                                    formatDate=1,
                                    keepUpToDate=False
                                )
                                # Convert objects to dicts
                                if bars:
                                    bars = [
                                        {
                                            "date": b.date.isoformat() if hasattr(b.date, "isoformat") else str(b.date),
                                            "open": b.open,
                                            "high": b.high,
                                            "low": b.low,
                                            "close": b.close,
                                            "volume": b.volume,
                                            "barCount": b.barCount,
                                            "average": b.average
                                        }
                                        for b in bars
                                    ]
                            
                            if bars:
                                # Save to file
                                out_file = current_run_dir / f"{contract.conId}.json"
                                out_file.write_text(json.dumps(bars), encoding="utf-8")
                                symbol_stats["contracts"] += 1
                                symbol_stats["bars"] += len(bars)
                            
                            # Update progress periodically
                            if progress_callback and c_idx % 10 == 0:
                                progress_callback(
                                    i, total_symbols, 
                                    f"Fetching {symbol}: {c_idx}/{total_contracts}", 
                                    {"contracts_done": c_idx}
                                )
                            
                        except Exception as exc:
                            # Log but don't spam
                            # logger.error(f"Failed to fetch history for {symbol} conid={c.get('conid')}: {exc}")
                            symbol_stats["errors"] += 1
                            
                    results["symbols"][symbol] = symbol_stats
                    results["processed"] += 1
                    
                    if progress_callback:
                        progress_callback(i + 1, total_symbols, f"Completed {symbol}", symbol_stats)
                    
                except Exception as exc:
                    logger.error(f"Failed to process symbol {symbol}: {exc}")
                    results["errors"] += 1
                    if progress_callback:
                        progress_callback(i + 1, total_symbols, f"Failed {symbol}: {exc}", {"error": str(exc)})
                    
        return results
