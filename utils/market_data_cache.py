"""Centralized market data cache using working APIs (Alpha Vantage, Finnhub)."""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging
import pandas as pd
from dotenv import load_dotenv
from utils.robust_price_fetcher import get_robust_price_fetcher, register_cycle_prices, get_cycle_price
load_dotenv()


class MarketDataCache:
    """
    Caches market data for a single trading cycle to avoid redundant API calls.
    Fetches all needed data once at cycle start, then modules read from cache.
    """
    
    def __init__(self, cache_duration_minutes: int = 10, config=None):
        self.config = config
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.logger = logging.getLogger(__name__)
        
        # Use robust price fetcher for reliable data
        self._price_fetcher = get_robust_price_fetcher()
        
        # Cache storage
        self._macro_data: Optional[Dict] = None
        self._ticker_info_cache: Dict[str, Dict] = {}
        self._price_cache: Dict[str, float] = {}
        self._history_cache: Dict[str, any] = {}
        
        # Cache timestamps
        self._macro_timestamp: Optional[datetime] = None
        self._ticker_timestamps: Dict[str, datetime] = {}
        self._price_timestamps: Dict[str, datetime] = {}
        self._history_timestamps: Dict[str, datetime] = {}
        self._info_timestamps: Dict[str, datetime] = {}
        self._alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY') or os.getenv('ALPHA_VANTAGE_API_KEY')
        if not self._alpha_vantage_key and config is not None:
            apis = getattr(config, "data", config) if not isinstance(config, dict) else config
            if isinstance(apis, dict):
                av = (apis.get("apis") or {}).get("alpha_vantage") or {}
                if av.get("enabled") and av.get("api_key") and "YOUR_" not in str(av.get("api_key", "")):
                    self._alpha_vantage_key = av["api_key"]
            elif hasattr(config, "get"):
                av = config.get("apis.alpha_vantage") or {}
                if isinstance(av, dict) and av.get("enabled") and av.get("api_key"):
                    self._alpha_vantage_key = av["api_key"]

    def _fetch_alpha_vantage_series(self, symbol: str, period: str):
        """Fetch OHLC history from Alpha Vantage and normalize as a DataFrame."""
        if not self._alpha_vantage_key:
            return None

        period_map = {
            '5d': ('TIME_SERIES_DAILY', 'compact'),
            '7d': ('TIME_SERIES_DAILY', 'compact'),
            '14d': ('TIME_SERIES_DAILY', 'compact'),
            '1mo': ('TIME_SERIES_DAILY', 'compact'),
            '3mo': ('TIME_SERIES_DAILY', 'full')
        }
        function_name, output_size = period_map.get(period, ('TIME_SERIES_DAILY', 'compact'))

        try:
            response = requests.get(
                "https://www.alphavantage.co/query",
                params={
                    'function': function_name,
                    'symbol': symbol,
                    'apikey': self._alpha_vantage_key,
                    'outputsize': output_size
                },
                timeout=10
            )
            data = response.json()
            series_key = 'Time Series (Daily)'
            series = data.get(series_key, {})
            if not series:
                return None

            rows = []
            for date_str, values in series.items():
                rows.append({
                    'Date': pd.to_datetime(date_str),
                    'Open': float(values.get('1. open', 0.0)),
                    'High': float(values.get('2. high', 0.0)),
                    'Low': float(values.get('3. low', 0.0)),
                    'Close': float(values.get('4. close', 0.0)),
                    'Volume': float(values.get('5. volume', 0.0)),
                })

            if not rows:
                return None

            hist = pd.DataFrame(rows).sort_values('Date').set_index('Date')
            lookback_days = {'5d': 5, '7d': 7, '14d': 14, '1mo': 30, '3mo': 90}.get(period, 30)
            return hist.tail(lookback_days)
        except Exception as e:
            self.logger.debug(f"Alpha Vantage history fetch failed for {symbol}: {e}")
            return None

    def _fetch_finnhub_series(self, symbol: str, period: str):
        """Fetch OHLC history from Finnhub candle endpoint."""
        finnhub_key = os.getenv('FINNHUB_API_KEY')
        if not finnhub_key:
            return None

        now_ts = int(datetime.now().timestamp())
        lookback_seconds = {'5d': 5 * 86400, '7d': 7 * 86400, '14d': 14 * 86400, '1mo': 30 * 86400, '3mo': 90 * 86400}.get(period, 30 * 86400)
        from_ts = now_ts - lookback_seconds
        resolution = 'D'

        try:
            response = requests.get(
                "https://finnhub.io/api/v1/stock/candle",
                params={
                    'symbol': symbol,
                    'resolution': resolution,
                    'from': from_ts,
                    'to': now_ts,
                    'token': finnhub_key
                },
                timeout=10
            )
            data = response.json()
            if data.get('s') != 'ok':
                return None

            hist = pd.DataFrame({
                'Date': pd.to_datetime(data.get('t', []), unit='s'),
                'Open': data.get('o', []),
                'High': data.get('h', []),
                'Low': data.get('l', []),
                'Close': data.get('c', []),
                'Volume': data.get('v', []),
            })
            if hist.empty:
                return None
            return hist.sort_values('Date').set_index('Date')
        except Exception as e:
            self.logger.debug(f"Finnhub history fetch failed for {symbol}: {e}")
            return None

    def _load_macro_from_finnhub(self) -> Dict:
        """Fetch macro indicators (DXY, VIX, US10Y, SPY) from Finnhub."""
        now = datetime.now()
        macro_data = {
            'dxy': {'hist': None, 'current': None, 'change': 0.0},
            'vix': {'hist': None, 'current': None, 'level': 0.5},
            'us10y': {'hist': None, 'current': None, 'change': 0.0},
            'spy': {'hist': None, 'current': None, 'change': 0.0},
            'timestamp': now,
        }

        _defaults = {'vix': 20.0, 'us10y': 4.35, 'dxy': 103.5, 'spy': 520.0}
        _fh_syms = {'vix': 'TVC:VIX', 'us10y': 'TVC:US10Y', 'dxy': 'TVC:DXY', 'spy': 'SPY'}
        _fk = os.getenv('FINNHUB_API_KEY')

        for key, sym in _fh_syms.items():
            val = _defaults[key]
            if _fk:
                try:
                    d = requests.get(
                        'https://finnhub.io/api/v1/quote',
                        params={'symbol': sym, 'token': _fk},
                        timeout=6,
                    ).json()
                    if d.get('c', 0) > 0:
                        val = float(d['c'])
                except Exception:
                    pass
            macro_data[key]['current'] = val
            if key == 'vix':
                macro_data[key]['level'] = min(1.0, val / 40)

        return macro_data

    def fetch_macro_data(self, force_refresh: bool = False) -> Dict:
        """
        Fetch macro indicators (DXY, VIX, US10Y, SPY) once per cycle.
        Returns cached data if still valid.
        """
        now = datetime.now()

        if not force_refresh and self._macro_data and self._macro_timestamp:
            if now - self._macro_timestamp < self.cache_duration:
                self.logger.debug("Using cached macro data")
                return self._macro_data

        try:
            macro_data = self._load_macro_from_finnhub()
            self._macro_data = macro_data
            self._macro_timestamp = now
            self.logger.info("Macro data ready (DXY, VIX, US10Y, SPY)")
        except Exception as e:
            self.logger.error(f"Error fetching macro data: {e}")
            if self._macro_data:
                return self._macro_data

        return self._macro_data or {}
    
    def get_avg_volume(self, symbol: str, force_refresh: bool = False) -> Optional[int]:
        """Average daily share volume (20d history or vendor info). Returns None if unavailable."""
        sym = str(symbol or "").upper().strip()
        if not sym:
            return None

        cache_key = f"{sym}_avg_vol"
        now = datetime.now()
        if not force_refresh and cache_key in self._ticker_info_cache:
            ts = self._info_timestamps.get(cache_key)
            if ts and now - ts < self.cache_duration:
                cached = self._ticker_info_cache[cache_key].get("avg_volume")
                if cached and int(cached) > 0:
                    return int(cached)

        try:
            import yfinance as yf

            info = yf.Ticker(sym).info or {}
            for key in ("averageVolume", "averageVolume10days", "averageDailyVolume10Day"):
                val = info.get(key)
                if val and int(val) > 0:
                    vol = int(val)
                    self._ticker_info_cache[cache_key] = {"avg_volume": vol}
                    self._info_timestamps[cache_key] = now
                    return vol
        except Exception as exc:
            self.logger.debug("yfinance avg volume failed for %s: %s", sym, exc)

        hist = self.fetch_history(sym, "1mo", force_refresh=force_refresh)
        if hist is not None and not hist.empty and "Volume" in hist.columns:
            tail = hist["Volume"].tail(20)
            if not tail.empty:
                avg = int(tail.mean())
                if avg > 0:
                    self._ticker_info_cache[cache_key] = {"avg_volume": avg}
                    self._info_timestamps[cache_key] = now
                    return avg

        try:
            import yfinance as yf

            yhist = yf.Ticker(sym).history(period="1mo", interval="1d")
            if yhist is not None and not yhist.empty and "Volume" in yhist.columns:
                tail = yhist["Volume"].tail(20)
                if not tail.empty:
                    avg = int(tail.mean())
                    if avg > 0:
                        self._ticker_info_cache[cache_key] = {"avg_volume": avg}
                        self._info_timestamps[cache_key] = now
                        return avg
        except Exception as exc:
            self.logger.debug("yfinance history avg volume failed for %s: %s", sym, exc)
        return None

    def fetch_ticker_info(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Fetch ticker info once per symbol per cycle.
        Returns cached data if still valid.
        """
        now = datetime.now()
        
        # Return cached if valid
        if not force_refresh and symbol in self._ticker_info_cache:
            if symbol in self._ticker_timestamps:
                if now - self._ticker_timestamps[symbol] < self.cache_duration:
                    self.logger.debug(f"Using cached info for {symbol}")
                    return self._ticker_info_cache[symbol]
        
        try:
            _fk = os.getenv('FINNHUB_API_KEY')
            info = {}
            if _fk:
                d = requests.get('https://finnhub.io/api/v1/quote', params={'symbol': symbol, 'token': _fk}, timeout=8).json()
                if d.get('c', 0) > 0:
                    info = {'currentPrice': d['c'], 'regularMarketPrice': d['c'], 'previousClose': d.get('pc', d['c']), 'open': d.get('o', d['c']), 'dayHigh': d.get('h', d['c']), 'dayLow': d.get('l', d['c'])}
            self._ticker_info_cache[symbol] = info
            self._ticker_timestamps[symbol] = now
            return info
        except Exception as e:
            self.logger.error(f"Error fetching info for {symbol}: {e}")
            return self._ticker_info_cache.get(symbol)
    
    def fetch_prices(self, symbols: List[str], force_refresh: bool = False) -> Dict[str, float]:
        """
        Batch fetch current prices for multiple symbols.
        Returns dict of symbol -> price.
        """
        now = datetime.now()
        prices = {}
        
        symbols_to_fetch = []
        
        for symbol in symbols:
            sym = str(symbol or '').upper().strip()
            if not sym:
                continue
            # Cycle-wide cache (ingest / prior fetch this run)
            cycle_price = get_cycle_price(sym)
            if cycle_price and cycle_price > 0:
                prices[sym] = cycle_price
                self._price_cache[sym] = cycle_price
                self._price_timestamps[sym] = now
                continue
            # Instance cache
            if not force_refresh and sym in self._price_cache:
                if sym in self._price_timestamps:
                    if now - self._price_timestamps[sym] < self.cache_duration:
                        prices[sym] = self._price_cache[sym]
                        continue

            symbols_to_fetch.append(sym)
        
        # Fetch missing prices
        if symbols_to_fetch:
            self.logger.info(f"Fetching prices for {len(symbols_to_fetch)} symbols...")
            
            for symbol in symbols_to_fetch:
                try:
                    price = self._price_fetcher.get_real_price(symbol)
                    if price and price > 0:
                        prices[symbol] = price
                        self._price_cache[symbol] = price
                        self._price_timestamps[symbol] = now
                except Exception as e:
                    self.logger.error(f"Error fetching price for {symbol}: {e}")
        
        if prices:
            register_cycle_prices(prices)
        return prices
    
    def fetch_history(self, symbol: str, period: str = '1mo', force_refresh: bool = False):
        """Fetch historical data for a symbol using non-yfinance providers."""
        now = datetime.now()
        cache_key = f"{symbol}_{period}"
        
        # Return cached if valid
        if not force_refresh and cache_key in self._history_cache:
            if cache_key in self._history_timestamps:
                if now - self._history_timestamps[cache_key] < self.cache_duration:
                    self.logger.debug(f"Using cached history for {symbol} ({period})")
                    return self._history_cache[cache_key]
        
        try:
            hist = self._fetch_finnhub_series(symbol, period)
            if hist is None or hist.empty:
                hist = self._fetch_alpha_vantage_series(symbol, period)

            if hist is not None and not hist.empty:
                self._history_cache[cache_key] = hist
                self._history_timestamps[cache_key] = now
                return hist

            return self._history_cache.get(cache_key, pd.DataFrame())
        except Exception as e:
            self.logger.error(f"Error fetching history for {symbol}: {e}")
            return self._history_cache.get(cache_key, pd.DataFrame())
    
    def refresh_cache(self, symbols: Optional[List[str]] = None):
        """
        Refresh the cache by clearing and optionally pre-fetching data.
        Macro indicators are fetched once via fetch_macro_data().
        """
        self.logger.info("Refreshing market data cache...")
        
        self._price_cache.clear()
        self._price_timestamps.clear()
        self._history_cache.clear()
        self._history_timestamps.clear()
        self._ticker_info_cache.clear()
        self._info_timestamps.clear()
        self._macro_data = None
        self._macro_timestamp = None
        
        if symbols:
            self.logger.info(f"Pre-fetching data for {len(symbols)} symbols...")
            self.fetch_prices(symbols)
            
            for symbol in symbols[:self._prefetch_symbol_cap]:
                try:
                    self.fetch_history(symbol, '1mo')
                except Exception:
                    pass
        
        self.fetch_macro_data(force_refresh=True)
        self.logger.info("Cache refresh complete")
    
    def clear_cache(self):
        """Clear all cached data (useful for testing or forced refresh)."""
        self._macro_data = None
        self._macro_timestamp = None
        self._ticker_info_cache.clear()
        self._price_cache.clear()
        self._history_cache.clear()
        
        self._ticker_timestamps.clear()
        self._price_timestamps.clear()
        self._history_timestamps.clear()
        
        self.logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Return statistics about cache usage."""
        return {
            'macro_cached': self._macro_data is not None,
            'ticker_info_count': len(self._ticker_info_cache),
            'price_count': len(self._price_cache),
            'history_count': len(self._history_cache),
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60
        }
