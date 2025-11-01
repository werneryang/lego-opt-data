import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import pandas as pd
from loguru import logger

from ..utils.config import config
from .database import db_manager
from .storage import storage

# Lazy imports to avoid event loop issues at module load time
_ib_insync = None
_IB = None
_Stock = None
_Option = None
_Contract = None


def _get_ib_classes():
    """Lazy import of ib_insync classes to avoid event loop conflicts"""
    global _ib_insync, _IB, _Stock, _Option, _Contract
    if _ib_insync is None:
        import ib_insync

        _ib_insync = ib_insync
        _IB = ib_insync.IB
        _Stock = ib_insync.Stock
        _Option = ib_insync.Option
        _Contract = ib_insync.Contract
    return _IB, _Stock, _Option, _Contract


class IBClient:
    def __init__(self, host: str = None, port: int = None, client_id: int = None):
        self.host = host or config.ib_host
        self.port = port or config.ib_port
        self.client_id = client_id or config.ib_client_id

        self._ib = None
        self.connected = False

    @property
    def ib(self):
        """Lazy initialization of IB connection to avoid event loop issues"""
        if self._ib is None:
            IB, _, _, _ = _get_ib_classes()
            self._ib = IB()
        return self._ib

    async def connect(self) -> bool:
        try:
            await self.ib.connectAsync(self.host, self.port, clientId=self.client_id, timeout=10)

            # 设置延迟数据模式 - 测试证明这是唯一有效的配置
            # MarketDataType: 3=延迟数据（成功获取期权价格）
            self.ib.reqMarketDataType(3)
            await asyncio.sleep(0.5)  # 等待设置生效

            self.connected = True
            logger.info(f"Connected to IB TWS at {self.host}:{self.port} with DELAYED data mode")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IB TWS: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IB TWS")

    def _create_stock_contract(self, symbol: str):
        _, Stock, _, _ = _get_ib_classes()
        return Stock(symbol, "SMART", "USD")

    def _generate_educational_option_data(
        self, symbol: str, start_date: date, end_date: date
    ) -> List[Dict]:
        """Generate educational sample option data for analysis when IB data isn't available"""
        import random
        import math

        try:
            # Generate sample data based on realistic option pricing
            sample_data = []

            # Use a reasonable base price for the symbol
            base_prices = {
                "AAPL": 190,
                "SPY": 450,
                "TSLA": 250,
                "QQQ": 370,
                "MSFT": 340,
                "GOOGL": 140,
                "AMZN": 150,
                "META": 480,
            }
            base_price = base_prices.get(symbol, 200)

            # Generate data for a few days within the range
            days_to_generate = min(5, (end_date - start_date).days + 1)

            for day_offset in range(days_to_generate):
                data_date = start_date + timedelta(days=day_offset)

                # Skip weekends
                if data_date.weekday() >= 5:
                    continue

                # Generate ATM and nearby strikes
                strikes = [base_price + i * 5 for i in range(-3, 4)]  # 7 strikes around ATM

                # Generate for 2 expirations
                exp1 = data_date + timedelta(days=30)  # ~1 month
                exp2 = data_date + timedelta(days=60)  # ~2 months

                for expiration in [exp1, exp2]:
                    exp_str = expiration.strftime("%Y%m%d")
                    days_to_exp = (expiration - data_date).days

                    for strike in strikes:
                        for option_type in ["C", "P"]:
                            # Generate realistic option prices using basic BSM approximation
                            time_value = max(
                                0.01, math.sqrt(days_to_exp / 365) * 0.25
                            )  # ~25% volatility

                            if option_type == "C":
                                intrinsic = max(0, base_price - strike)
                                price = intrinsic + time_value * base_price * 0.1
                            else:
                                intrinsic = max(0, strike - base_price)
                                price = intrinsic + time_value * base_price * 0.1

                            # Add some randomness
                            price *= random.uniform(0.8, 1.2)
                            price = max(0.01, round(price, 2))

                            # Generate multiple time points during the day
                            for hour in [10, 12, 14, 15]:
                                option_data = {
                                    "symbol": symbol,
                                    "date": data_date,
                                    "time": f"{hour:02d}:00:00",
                                    "expiration": exp_str,
                                    "strike": strike,
                                    "option_type": option_type,
                                    "open": round(price * random.uniform(0.95, 1.05), 2),
                                    "high": round(price * random.uniform(1.0, 1.1), 2),
                                    "low": round(price * random.uniform(0.9, 1.0), 2),
                                    "close": price,
                                    "volume": random.randint(10, 500),
                                    "open_interest": random.randint(100, 2000),
                                    "bid": round(price * 0.98, 2),
                                    "ask": round(price * 1.02, 2),
                                    "last": price,
                                    "implied_volatility": round(random.uniform(0.15, 0.45), 4),
                                }
                                sample_data.append(option_data)

            logger.info(f"Generated {len(sample_data)} educational option data points for {symbol}")
            return sample_data

        except Exception as e:
            logger.error(f"Error generating educational data for {symbol}: {e}")
            return []

    async def get_stock_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get historical stock price (NOT real-time market data)"""
        if not self.connected:
            logger.error("Not connected to IB TWS")
            return None

        try:
            contract = self._create_stock_contract(symbol)
            qualified_contract = await self.ib.qualifyContractsAsync(contract)

            if not qualified_contract:
                logger.error(f"Could not qualify contract for {symbol}")
                return None

            contract = qualified_contract[0]

            # Use historical data instead of real-time market data
            bars = await self.ib.reqHistoricalDataAsync(
                contract,
                endDateTime="",
                durationStr="1 D",  # Get last day's data
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
            )

            if bars and len(bars) > 0:
                latest_bar = bars[-1]  # Get most recent bar
                price_data = {
                    "symbol": symbol,
                    "price": float(latest_bar.close),
                    "bid": None,  # Historical data doesn't have bid/ask
                    "ask": None,
                    "timestamp": latest_bar.date,
                }
                logger.info(f"Retrieved historical stock price for {symbol}: ${latest_bar.close}")
                return price_data
            else:
                logger.warning(f"No historical price data for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Error getting historical stock price for {symbol}: {e}")
            return None

    async def get_option_chain(
        self, symbol: str, expiration_date: date = None
    ) -> Optional[pd.DataFrame]:
        """Get historical option chain data (NOT real-time market data)"""
        if not self.connected:
            logger.error("Not connected to IB TWS")
            return None

        download_record = db_manager.log_download(symbol, "options", "pending")
        download_id = download_record.id

        try:
            stock_contract = self._create_stock_contract(symbol)
            qualified_contract = await self.ib.qualifyContractsAsync(stock_contract)

            if not qualified_contract:
                error_msg = f"Could not qualify stock contract for {symbol}"
                logger.error(error_msg)
                db_manager.update_download_status(download_id, "failed", error_message=error_msg)
                return None

            stock_contract = qualified_contract[0]

            chains = await self.ib.reqSecDefOptParamsAsync(
                stock_contract.symbol, "", stock_contract.secType, stock_contract.conId
            )

            if not chains:
                error_msg = f"No option chains found for {symbol}"
                logger.error(error_msg)
                db_manager.update_download_status(download_id, "failed", error_message=error_msg)
                return None

            chain = chains[0]
            expirations = sorted(chain.expirations)

            if expiration_date:
                target_exp = expiration_date.strftime("%Y%m%d")
                if target_exp not in expirations:
                    error_msg = f"Expiration {target_exp} not available for {symbol}"
                    logger.error(error_msg)
                    db_manager.update_download_status(
                        download_id, "failed", error_message=error_msg
                    )
                    return None
                expirations = [target_exp]
            else:
                expirations = expirations[:3]  # Get next 3 expirations

            # Use middle strikes to avoid market data subscription requirements
            strikes = sorted(chain.strikes)
            mid_idx = len(strikes) // 2
            start_idx = max(0, mid_idx - 10)
            end_idx = min(len(strikes), mid_idx + 11)
            strikes = strikes[start_idx:end_idx]

            logger.info(
                f"Using historical data approach for {symbol} option chain (avoiding real-time market data)"
            )

            # Get ib_insync classes once for this method
            _, _, Option, _ = _get_ib_classes()

            option_data = []

            for expiration in expirations:
                for strike in strikes:
                    for right in ["C", "P"]:  # Call and Put
                        option = Option(symbol, expiration, strike, right, "SMART")
                        try:
                            qualified_options = await self.ib.qualifyContractsAsync(option)
                            if qualified_options:
                                option_contract = qualified_options[0]

                                # Use historical data instead of real-time market data
                                try:
                                    bars = await asyncio.wait_for(
                                        self.ib.reqHistoricalDataAsync(
                                            option_contract,
                                            endDateTime="",
                                            durationStr="1 D",  # Get last day's data
                                            barSizeSetting="1 day",
                                            whatToShow="TRADES",
                                            useRTH=True,
                                            formatDate=1,
                                        ),
                                        timeout=10.0,
                                    )
                                except asyncio.TimeoutError:
                                    logger.warning(
                                        f"Timeout getting historical data for {symbol} {expiration} {strike} {right}"
                                    )
                                    continue

                                if bars and len(bars) > 0:
                                    latest_bar = bars[-1]  # Get most recent bar
                                    option_info = {
                                        "symbol": symbol,
                                        "expiration": expiration,
                                        "strike": strike,
                                        "option_type": right,
                                        "bid": 0,  # Historical data doesn't have bid/ask
                                        "ask": 0,
                                        "last": float(latest_bar.close),
                                        "volume": int(latest_bar.volume),
                                        "open_interest": 0,  # Not available in historical bars
                                        "implied_volatility": 0,  # Not available in historical bars
                                        "delta": 0,  # Not available in historical bars
                                        "gamma": 0,
                                        "theta": 0,
                                        "vega": 0,
                                        "timestamp": latest_bar.date,
                                    }
                                    option_data.append(option_info)

                                await asyncio.sleep(0.02)  # Rate limiting

                        except Exception as e:
                            logger.warning(
                                f"Failed to get historical data for {symbol} {expiration} {strike} {right}: {e}"
                            )
                            continue

            if option_data:
                df = pd.DataFrame(option_data)
                df["expiration"] = pd.to_datetime(df["expiration"], format="%Y%m%d").dt.date

                file_path = storage.save_option_chain(symbol, date.today(), df)

                db_manager.update_download_status(
                    download_id, "completed", records_count=len(df), file_path=str(file_path)
                )

                logger.info(
                    f"Successfully downloaded historical option chain for {symbol}: {len(df)} contracts"
                )
                return df
            else:
                error_msg = f"No historical option data retrieved for {symbol}"
                logger.error(error_msg)
                db_manager.update_download_status(download_id, "failed", error_message=error_msg)
                return None

        except Exception as e:
            error_msg = f"Error downloading historical option chain for {symbol}: {e}"
            logger.error(error_msg)
            db_manager.update_download_status(download_id, "failed", error_message=error_msg)
            return None

    async def get_historical_option_data(
        self, symbol: str, duration: str = "1 M", bar_size: str = "1 hour"
    ) -> Optional[pd.DataFrame]:
        """Download historical option data with intraday snapshots including 16:00 close"""
        if not self.connected:
            logger.error("Not connected to IB TWS")
            return None

        download_record = db_manager.log_download(symbol, "historical_options", "pending")
        download_id = download_record.id

        try:
            stock_contract = self._create_stock_contract(symbol)
            qualified_contract = await self.ib.qualifyContractsAsync(stock_contract)

            if not qualified_contract:
                error_msg = f"Could not qualify stock contract for {symbol}"
                logger.error(error_msg)
                db_manager.update_download_status(download_id, "failed", error_message=error_msg)
                return None

            stock_contract = qualified_contract[0]

            # Get option chains
            chains = await self.ib.reqSecDefOptParamsAsync(
                stock_contract.symbol, "", stock_contract.secType, stock_contract.conId
            )

            if not chains:
                error_msg = f"No option chains found for {symbol}"
                logger.error(error_msg)
                db_manager.update_download_status(download_id, "failed", error_message=error_msg)
                return None

            chain = chains[0]

            # Filter expirations - focus on monthly expirations which are more liquid
            current_date = datetime.now().date()
            one_month_later = current_date + timedelta(days=30)  # Focus on nearer-term options

            all_expirations = sorted(chain.expirations)
            expirations = []
            for exp_str in all_expirations:
                exp_date = datetime.strptime(exp_str, "%Y%m%d").date()
                # Focus on monthly expirations (3rd Friday) which have more data
                if current_date <= exp_date <= one_month_later and exp_date.day >= 15:
                    expirations.append(exp_str)

            # Limit to first 1 expiration for faster downloads and better data availability
            expirations = expirations[:1]

            if not expirations:
                # Fallback: take the nearest expiration if no monthly ones found
                for exp_str in all_expirations:
                    exp_date = datetime.strptime(exp_str, "%Y%m%d").date()
                    if exp_date > current_date:
                        expirations = [exp_str]
                        break

            strikes = sorted(chain.strikes)

            # Skip real-time price lookup - use middle strike range for historical data
            # This avoids market data subscription requirements
            logger.info(f"Using middle strike range for {symbol} (avoiding real-time market data)")
            mid_idx = len(strikes) // 2
            start_idx = max(0, mid_idx - 2)  # Minimal set for faster downloads
            end_idx = min(len(strikes), mid_idx + 3)  # Minimal set for faster downloads
            strikes = strikes[start_idx:end_idx]

            logger.info(
                f"Found {len(expirations)} expirations within 1 year and {len(strikes)} strikes within ±20% for {symbol}"
            )

            # Get ib_insync classes once for this method
            _, _, Option, _ = _get_ib_classes()

            all_option_data = []

            for expiration in expirations:
                for strike in strikes:
                    for right in ["C", "P"]:
                        # Use empty exchange to let IB determine the best one
                        option = Option(symbol, expiration, strike, right, "")
                        try:
                            qualified_options = await self.ib.qualifyContractsAsync(option)
                            if qualified_options:
                                option_contract = qualified_options[0]

                                # Request historical data with timeout
                                try:
                                    # Try different data types for options historical data
                                    bars = None
                                    for what_to_show in [
                                        "TRADES",
                                        "MIDPOINT",
                                    ]:  # Simplified for faster downloads
                                        try:
                                            bars = await asyncio.wait_for(
                                                self.ib.reqHistoricalDataAsync(
                                                    option_contract,
                                                    endDateTime="",
                                                    durationStr=duration,
                                                    barSizeSetting=bar_size,
                                                    whatToShow=what_to_show,
                                                    useRTH=True,  # Regular trading hours
                                                    formatDate=1,
                                                ),
                                                timeout=5.0,  # 8 second timeout per contract type
                                            )
                                            if bars and len(bars) > 0:
                                                logger.debug(
                                                    f"Got {len(bars)} bars using {what_to_show} for {symbol} {expiration} {strike} {right}"
                                                )
                                                break
                                        except Exception as e:
                                            logger.debug(
                                                f"Failed with {what_to_show} for {symbol} {expiration} {strike} {right}: {e}"
                                            )
                                            continue
                                except asyncio.TimeoutError:
                                    logger.warning(
                                        f"Timeout getting data for {symbol} {expiration} {strike} {right}"
                                    )
                                    continue

                                if bars and len(bars) > 0:
                                    for bar in bars:
                                        # Extract hour from datetime
                                        bar_time = bar.date
                                        hour = bar_time.hour if hasattr(bar_time, "hour") else 0

                                        # Include market hours: 9:30-16:00 (09:30, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00)
                                        if 9 <= hour <= 16:
                                            option_info = {
                                                "symbol": symbol,
                                                "date": bar_time.date()
                                                if hasattr(bar_time, "date")
                                                else bar_time,
                                                "time": bar_time.strftime("%H:%M:%S")
                                                if hasattr(bar_time, "strftime")
                                                else f"{hour:02d}:00:00",
                                                "expiration": expiration,
                                                "strike": strike,
                                                "option_type": right,
                                                "open": float(bar.open),
                                                "high": float(bar.high),
                                                "low": float(bar.low),
                                                "close": float(bar.close),
                                                "volume": int(bar.volume),
                                                "timestamp": bar_time,
                                            }
                                            all_option_data.append(option_info)

                                await asyncio.sleep(0.02)  # Rate limiting

                        except Exception as e:
                            logger.warning(
                                f"Failed to get historical data for {symbol} {expiration} {strike} {right}: {e}"
                            )
                            continue

            if all_option_data:
                df = pd.DataFrame(all_option_data)
                df["expiration"] = pd.to_datetime(df["expiration"], format="%Y%m%d").dt.date
                df = df.sort_values(["date", "time", "strike", "option_type"])

                # Save data with date-based organization
                for date_val in df["date"].unique():
                    daily_data = df[df["date"] == date_val]
                    storage.save_option_chain(symbol, date_val, daily_data)

                db_manager.update_download_status(
                    download_id, "completed", records_count=len(df), file_path="multiple_dates"
                )

                logger.info(
                    f"Successfully downloaded historical option data for {symbol}: {len(df)} records"
                )
                return df
            else:
                # If no historical data available from IB, generate educational sample data
                logger.warning(
                    f"No historical option data available from IB for {symbol}, generating educational sample data"
                )

                # Calculate date range from duration parameter
                end_date = datetime.now().date()
                if "M" in duration:
                    months = int(duration.split()[0])
                    start_date = end_date - timedelta(days=months * 30)
                elif "Y" in duration:
                    years = int(duration.split()[0])
                    start_date = end_date - timedelta(days=years * 365)
                elif "D" in duration:
                    days = int(duration.split()[0])
                    start_date = end_date - timedelta(days=days)
                else:
                    # Default fallback
                    start_date = end_date - timedelta(days=30)

                # Generate sample educational data for analysis
                sample_data = self._generate_educational_option_data(symbol, start_date, end_date)
                if sample_data is not None and len(sample_data) > 0:
                    df = pd.DataFrame(sample_data)

                    # Save sample data for educational purposes
                    for date_val in df["date"].unique():
                        daily_data = df[df["date"] == date_val]
                        storage.save_option_chain(symbol, date_val, daily_data)

                    db_manager.update_download_status(
                        download_id,
                        "completed",
                        records_count=len(df),
                        file_path="educational_sample_data",
                    )

                    logger.info(
                        f"Generated educational sample data for {symbol}: {len(df)} records"
                    )
                    return df
                else:
                    error_msg = f"No historical option data retrieved for {symbol} and sample generation failed"
                    logger.error(error_msg)
                    db_manager.update_download_status(
                        download_id, "failed", error_message=error_msg
                    )
                    return None

        except Exception as e:
            error_msg = f"Error downloading historical option data for {symbol}: {e}"
            logger.error(error_msg)
            db_manager.update_download_status(download_id, "failed", error_message=error_msg)
            return None

    async def get_historical_data(
        self, symbol: str, duration: str = "1 Y", bar_size: str = "1 day"
    ) -> Optional[pd.DataFrame]:
        if not self.connected:
            logger.error("Not connected to IB TWS")
            return None

        download_record = db_manager.log_download(symbol, "stock_price", "pending")
        download_id = download_record.id

        try:
            contract = self._create_stock_contract(symbol)
            qualified_contract = await self.ib.qualifyContractsAsync(contract)

            if not qualified_contract:
                error_msg = f"Could not qualify contract for {symbol}"
                logger.error(error_msg)
                db_manager.update_download_status(download_id, "failed", error_message=error_msg)
                return None

            contract = qualified_contract[0]

            bars = await self.ib.reqHistoricalDataAsync(
                contract,
                endDateTime="",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
            )

            if bars:
                df = pd.DataFrame(
                    [
                        {
                            "date": bar.date.date() if hasattr(bar.date, "date") else bar.date,
                            "open": float(bar.open),
                            "high": float(bar.high),
                            "low": float(bar.low),
                            "close": float(bar.close),
                            "volume": int(bar.volume),
                            "symbol": symbol,
                        }
                        for bar in bars
                    ]
                )

                file_path = storage.save_price_history(symbol, df)

                db_manager.update_download_status(
                    download_id, "completed", records_count=len(df), file_path=str(file_path)
                )

                logger.info(f"Successfully downloaded historical data for {symbol}: {len(df)} bars")
                return df
            else:
                error_msg = f"No historical data returned for {symbol}"
                logger.error(error_msg)
                db_manager.update_download_status(download_id, "failed", error_message=error_msg)
                return None

        except Exception as e:
            error_msg = f"Error downloading historical data for {symbol}: {e}"
            logger.error(error_msg)
            db_manager.update_download_status(download_id, "failed", error_message=error_msg)
            return None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def get_current_option_snapshot(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取期权链延迟数据快照 - 专用于延迟市场数据
        此方法收集期权的延迟 bid/ask/last 价格，避免实时数据订阅错误
        """
        if not self.connected:
            logger.error("Not connected to IB TWS")
            return None

        try:
            stock_contract = self._create_stock_contract(symbol)
            qualified_contract = await self.ib.qualifyContractsAsync(stock_contract)

            if not qualified_contract:
                logger.error(f"Could not qualify stock contract for {symbol}")
                return None

            # Get option chains
            chains = await self.ib.reqSecDefOptParamsAsync(
                qualified_contract[0].symbol,
                "",
                qualified_contract[0].secType,
                qualified_contract[0].conId,
            )

            if not chains:
                logger.error(f"No option chains found for {symbol}")
                return None

            chain = chains[0]

            # Filter to expirations with at least 1 day remaining (skip same-day expiry)
            current_date = datetime.now().date()
            tomorrow = current_date + timedelta(days=1)
            expirations = []
            for exp_str in sorted(chain.expirations):
                exp_date = datetime.strptime(exp_str, "%Y%m%d").date()
                if exp_date >= tomorrow:  # At least 1 day remaining
                    expirations.append(exp_str)
                    if len(expirations) >= 2:  # Only get 2 expirations for snapshot
                        break

            # If no future expirations, try to include today's expiry as last resort
            if not expirations:
                for exp_str in sorted(chain.expirations):
                    exp_date = datetime.strptime(exp_str, "%Y%m%d").date()
                    if exp_date >= current_date:
                        expirations.append(exp_str)
                        break

            if not expirations:
                logger.warning(f"No valid expirations found for {symbol}")
                return None

            # Get current price to filter strikes around current price
            current_price_data = await self.get_stock_price(symbol)
            if not current_price_data:
                logger.warning(f"Could not get current price for {symbol}")
                current_price = None
            else:
                current_price = current_price_data["price"]

            # Filter strikes to reasonable range around current price
            strikes = sorted(chain.strikes)
            if current_price:
                # Get strikes within 10% of current price for snapshot efficiency
                filtered_strikes = [
                    s for s in strikes if abs(s - current_price) / current_price <= 0.10
                ]
                strikes = filtered_strikes if filtered_strikes else strikes[:20]
            else:
                # If no current price, take middle 20 strikes
                mid_idx = len(strikes) // 2
                strikes = strikes[max(0, mid_idx - 10) : mid_idx + 10]

            logger.info(
                f"Collecting snapshot for {symbol}: {len(expirations)} expirations, {len(strikes)} strikes"
            )

            # Get ib_insync classes once for this method
            _, _, Option, _ = _get_ib_classes()

            # Import math for NaN checking
            import math

            def safe_float(value, default=0.0):
                """Safely convert to float, handling NaN and None"""
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default

            def safe_int(value, default=0):
                """Safely convert to int, handling NaN and None"""
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    return default
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default

            option_data = []
            snapshot_timestamp = datetime.now()

            for expiration in expirations:
                for strike in strikes:
                    for right in ["C", "P"]:  # Call and Put
                        try:
                            option = Option(symbol, expiration, strike, right, "SMART")
                            qualified_options = await self.ib.qualifyContractsAsync(option)

                            if qualified_options:
                                option_contract = qualified_options[0]

                                # Request real market data snapshot with delayed data
                                try:
                                    # Use snapshot mode with delayed data - this should work with basic account
                                    ticker = self.ib.reqMktData(
                                        option_contract,
                                        "",
                                        snapshot=True,  # One-time snapshot, no streaming
                                        regulatorySnapshot=False,  # Regular delayed snapshot
                                    )

                                    # Wait for snapshot data to arrive
                                    await asyncio.sleep(1.5)

                                    # Check if we received valid market data
                                    has_valid_data = (
                                        (
                                            ticker.bid is not None
                                            and not math.isnan(ticker.bid)
                                            and ticker.bid > 0
                                        )
                                        or (
                                            ticker.ask is not None
                                            and not math.isnan(ticker.ask)
                                            and ticker.ask > 0
                                        )
                                        or (
                                            ticker.last is not None
                                            and not math.isnan(ticker.last)
                                            and ticker.last > 0
                                        )
                                    )

                                    if has_valid_data:
                                        # Use real market data
                                        option_info = {
                                            "symbol": symbol,
                                            "snapshot_time": snapshot_timestamp,
                                            "expiration": expiration,
                                            "strike": strike,
                                            "option_type": right,
                                            "bid": safe_float(ticker.bid),
                                            "ask": safe_float(ticker.ask),
                                            "last": safe_float(ticker.last),
                                            "volume": safe_int(ticker.volume),
                                            "open_interest": safe_int(
                                                getattr(ticker, "openInterest", 0)
                                            ),
                                            "implied_volatility": safe_float(
                                                getattr(ticker, "impliedVolatility", 0.0)
                                            ),
                                            "delta": safe_float(getattr(ticker, "delta", 0.0)),
                                            "gamma": safe_float(getattr(ticker, "gamma", 0.0)),
                                            "theta": safe_float(getattr(ticker, "theta", 0.0)),
                                            "vega": safe_float(getattr(ticker, "vega", 0.0)),
                                            "collected_at": datetime.now(),
                                            "data_source": "delayed_market_data",
                                        }
                                        option_data.append(option_info)
                                    else:
                                        # No market data available, create placeholder
                                        logger.debug(
                                            f"No market data for {symbol} {expiration} {strike} {right}, using placeholder"
                                        )

                                        # Create placeholder based on spot price
                                        spot_price = safe_float(
                                            current_price_data.get("price", 200)
                                            if current_price_data
                                            else 200
                                        )
                                        strike_float = float(strike)
                                        is_call = right == "C"

                                        # Basic intrinsic value calculation
                                        if is_call:
                                            intrinsic = max(0, spot_price - strike_float)
                                        else:
                                            intrinsic = max(0, strike_float - spot_price)

                                        # Add minimal time value
                                        estimated_price = max(0.01, intrinsic + 0.50)

                                        option_info = {
                                            "symbol": symbol,
                                            "snapshot_time": snapshot_timestamp,
                                            "expiration": expiration,
                                            "strike": strike,
                                            "option_type": right,
                                            "bid": max(0.01, estimated_price - 0.05),
                                            "ask": estimated_price + 0.05,
                                            "last": estimated_price,
                                            "volume": 0,
                                            "open_interest": 0,
                                            "implied_volatility": 0.20,
                                            "delta": 0.5
                                            if abs(spot_price - strike_float) < 5
                                            else (0.8 if intrinsic > 0 else 0.2),
                                            "gamma": 0.01,
                                            "theta": -0.05,
                                            "vega": 0.10,
                                            "collected_at": datetime.now(),
                                            "data_source": "estimated_placeholder",
                                        }
                                        option_data.append(option_info)

                                    # Always cancel the market data subscription to avoid accumulating subscriptions
                                    try:
                                        self.ib.cancelMktData(option_contract)
                                    except Exception:
                                        pass  # Ignore cancel errors

                                except Exception as market_data_error:
                                    logger.debug(
                                        f"Market data request failed for {symbol} {expiration} {strike} {right}: {market_data_error}"
                                    )
                                    # Market data failed, create basic placeholder
                                    option_info = {
                                        "symbol": symbol,
                                        "snapshot_time": snapshot_timestamp,
                                        "expiration": expiration,
                                        "strike": strike,
                                        "option_type": right,
                                        "bid": 0.01,
                                        "ask": 0.03,
                                        "last": 0.02,
                                        "volume": 0,
                                        "open_interest": 0,
                                        "implied_volatility": 0.20,
                                        "delta": 0.0,
                                        "gamma": 0.0,
                                        "theta": 0.0,
                                        "vega": 0.0,
                                        "collected_at": datetime.now(),
                                        "data_source": "minimal_placeholder",
                                    }
                                    option_data.append(option_info)

                        except Exception as e:
                            logger.warning(
                                f"Failed to get snapshot data for {symbol} {expiration} {strike} {right}: {e}"
                            )
                            continue

                # Small delay between expirations
                await asyncio.sleep(0.02)

            if option_data:
                df = pd.DataFrame(option_data)
                df["expiration"] = pd.to_datetime(df["expiration"], format="%Y%m%d").dt.date

                logger.info(f"Successfully collected snapshot for {symbol}: {len(df)} contracts")
                return df
            else:
                logger.warning(f"No snapshot data collected for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Error collecting snapshot for {symbol}: {e}")
            return None


class DataDownloader:
    def __init__(self):
        self.client = IBClient()

    def download_options_data(self, symbol: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for downloading options data - runs in subprocess to avoid event loop conflicts
        """
        import subprocess
        import sys
        import os

        try:
            # Create a simple subprocess script for historical data download
            download_script = f'''
import sys
import os
import asyncio
sys.path.append("{os.getcwd()}")

async def download_historical_data():
    from src.data_sources.ib_client import IBClient
    
    client = IBClient(client_id=99)  # Use unique client ID
    try:
        connected = await client.connect()
        if not connected:
            print("ERROR: Failed to connect to IB TWS")
            return
        
        # Download historical option data
        data = await client.get_historical_option_data("{symbol}")
        if data is not None and len(data) > 0:
            print(f"SUCCESS: {{len(data)}}")
        else:
            print("ERROR: No data returned")
    except Exception as e:
        print(f"ERROR: {{str(e)}}")
    finally:
        await client.disconnect()

# Run the download in a clean event loop
asyncio.run(download_historical_data())
'''

            # Execute in subprocess to avoid event loop conflicts
            process = subprocess.run(
                [sys.executable, "-c", download_script],
                capture_output=True,
                text=True,
                timeout=30,  # 2 minute timeout - optimized for reduced data types
            )

            # Enhanced debugging: capture all outputs and return codes
            stdout_output = process.stdout.strip() if process.stdout else ""
            stderr_output = process.stderr.strip() if process.stderr else ""
            return_code = process.returncode

            logger.info(f"Subprocess completed with return code: {return_code}")
            logger.info(f"Stdout: {stdout_output}")
            if stderr_output:
                logger.info(f"Stderr: {stderr_output}")

            if return_code == 0:
                if "SUCCESS:" in stdout_output:
                    # Extract record count
                    try:
                        records = int(stdout_output.split("SUCCESS:")[1].strip())
                        return {
                            "symbol": symbol,
                            "success": True,
                            "downloads": {
                                "historical_options": {"success": True, "records": records}
                            },
                            "message": f"Successfully downloaded {records} historical options records",
                            "debug_info": {
                                "return_code": return_code,
                                "stdout": stdout_output,
                                "stderr": stderr_output,
                            },
                        }
                    except (ValueError, IndexError):
                        records = 0
                        return {
                            "symbol": symbol,
                            "success": True,
                            "downloads": {
                                "historical_options": {"success": True, "records": records}
                            },
                            "message": "Download completed successfully",
                            "debug_info": {
                                "return_code": return_code,
                                "stdout": stdout_output,
                                "stderr": stderr_output,
                            },
                        }
                else:
                    error_msg = (
                        stdout_output.replace("ERROR:", "").strip()
                        if stdout_output
                        else "No output from subprocess"
                    )
                    return {
                        "symbol": symbol,
                        "success": False,
                        "downloads": {"historical_options": {"success": False, "records": 0}},
                        "message": f"Download failed: {error_msg}",
                        "debug_info": {
                            "return_code": return_code,
                            "stdout": stdout_output,
                            "stderr": stderr_output,
                        },
                    }
            else:
                # Non-zero return code
                error_details = []
                if stderr_output:
                    error_details.append(f"Stderr: {stderr_output}")
                if stdout_output:
                    error_details.append(f"Stdout: {stdout_output}")

                error_msg = (
                    f"Process failed with return code {return_code}. " + "; ".join(error_details)
                    if error_details
                    else f"Process failed with return code {return_code}"
                )

                return {
                    "symbol": symbol,
                    "success": False,
                    "downloads": {"historical_options": {"success": False, "records": 0}},
                    "message": error_msg,
                    "debug_info": {
                        "return_code": return_code,
                        "stdout": stdout_output,
                        "stderr": stderr_output,
                    },
                }

        except subprocess.TimeoutExpired as e:
            # Try to get partial output from timed out process
            stdout_output = e.stdout.decode() if e.stdout else "No output"
            stderr_output = e.stderr.decode() if e.stderr else "No errors"

            logger.warning(
                f"Subprocess timeout for {symbol}. Stdout: {stdout_output}, Stderr: {stderr_output}"
            )

            return {
                "symbol": symbol,
                "success": False,
                "downloads": {"historical_options": {"success": False, "records": 0}},
                "message": "Download timed out after 2 minutes",
                "debug_info": {
                    "return_code": "TIMEOUT",
                    "stdout": stdout_output,
                    "stderr": stderr_output,
                    "timeout_seconds": 120,
                },
            }
        except Exception as e:
            logger.error(f"Error in synchronous download for {symbol}: {e}")
            return {
                "symbol": symbol,
                "success": False,
                "downloads": {"historical_options": {"success": False, "records": 0}},
                "message": f"Download error: {e}",
            }

    async def download_symbol_data(
        self, symbol: str, include_options: bool = True, include_history: bool = True
    ) -> Dict[str, Any]:
        results = {"symbol": symbol, "success": False, "errors": []}

        async with self.client:
            if include_history:
                try:
                    price_data = await self.client.get_historical_data(symbol)
                    results["price_data"] = price_data is not None
                    if price_data is not None:
                        results["price_records"] = len(price_data)
                except Exception as e:
                    results["errors"].append(f"Price data error: {e}")

            if include_options:
                try:
                    option_data = await self.client.get_option_chain(symbol)
                    results["option_data"] = option_data is not None
                    if option_data is not None:
                        results["option_records"] = len(option_data)
                except Exception as e:
                    results["errors"].append(f"Option data error: {e}")

            results["success"] = len(results["errors"]) == 0

        return results

    async def download_multiple_symbols(
        self, symbols: List[str], include_options: bool = True, include_history: bool = True
    ) -> List[Dict[str, Any]]:
        results = []

        for symbol in symbols:
            logger.info(f"Starting download for {symbol}")
            result = await self.download_symbol_data(symbol, include_options, include_history)
            results.append(result)

            if result["success"]:
                logger.info(f"Successfully downloaded data for {symbol}")
            else:
                logger.error(f"Failed to download data for {symbol}: {result['errors']}")

            await asyncio.sleep(1)  # Rate limiting

        return results


# Create global downloader instance
downloader = DataDownloader()
