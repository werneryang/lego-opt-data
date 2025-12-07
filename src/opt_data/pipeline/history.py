from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        """
        if not output_dir:
            output_dir = self.cfg.paths.clean / "ib" / "history"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load universe if symbols not provided
        if not symbols:
            universe = load_universe(Path(self.cfg.universe.file))
            symbols = [u.symbol for u in universe]
            
        # Default duration string
        duration_str = f"{days} D" if days else "30 D"
        
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
            market_data_type=self.cfg.ib.market_data_type,
        )

        with session as sess:
            ib = sess.ensure_connected()
            
            for symbol in symbols:
                logger.info(f"Processing history for {symbol}...")
                symbol_stats = {"contracts": 0, "bars": 0, "errors": 0}
                
                try:
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

                    underlying_conid = qualified[0].conId
                    logger.info(f"Resolved {symbol} to conid {underlying_conid}")

                    # 2. Fetch reference price for filtering
                    # We need a price to filter strikes. 
                    # If ref_date is today, we could use live price, but historical close is safer/consistent.
                    # Let's fetch the daily bar for ref_date (or the last available day).
                    from ..ib import fetch_daily
                    
                    # We need to construct a Contract for the underlying
                    underlying_contract = qualified[0]
                    
                    # Fetch 1 day of history ending at ref_date (or slightly after to ensure coverage)
                    # If ref_date is today, we might get yesterday's close if market is open, or today's if closed.
                    # To be safe, let's ask for 2 days ending today/ref_date.
                    
                    # Actually, fetch_daily expects a Contract.
                    # And it returns a DataFrame or list of bars.
                    # Let's use a simple reqHistoricalData for 1 day ending now if ref_date is today,
                    # or ending at ref_date if it's historical.
                    
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
                    symbol_dir = output_dir / symbol / ref_date.isoformat()
                    symbol_dir.mkdir(parents=True, exist_ok=True)
                    
                    for contract_dict in contracts:
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
                            
                            bars = fetch_option_daily_aggregated(
                                ib,
                                contract,
                                what_to_show=what_to_show,
                                duration=duration_str,
                                use_rth=use_rth,
                                throttle=self.throttle
                            )
                            
                            if bars:
                                # Save to file
                                out_file = symbol_dir / f"{contract.conId}.json"
                                out_file.write_text(json.dumps(bars), encoding="utf-8")
                                symbol_stats["contracts"] += 1
                                symbol_stats["bars"] += len(bars)
                            
                        except Exception as exc:
                            logger.error(f"Failed to fetch history for {symbol} conid={c.get('conid')}: {exc}")
                            symbol_stats["errors"] += 1
                            
                    results["symbols"][symbol] = symbol_stats
                    results["processed"] += 1
                    
                except Exception as exc:
                    logger.error(f"Failed to process symbol {symbol}: {exc}")
                    results["errors"] += 1
                    
        return results
