"""Centralized market data cache using working APIs (Alpha Vantage, Finnhub)."""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging
import pandas as pd
from dotenv import load_dotenv
from utils.robust_price_fetcher import get_robust_price_fetcher
load_dotenv()


class MarketDataCache:
    """
    Caches market data for a single trading cycle to avoid redundant API calls.
    Fetches all needed data once at cycle start, then modules read from cache.
    """
    
    def __init__(self, cache_duration_minutes: int = 10):
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.logger = logging.getLogger(__name__)
        
        # Use robust price fetcher for reliable data
        self._price_fetcher = get_robust_price_fetcher()
        
        # Cache storage
        self._macro_data: Optional[Dict] = None
        self._ticker_info_cache: Dict[str, Dict] = {}
        self._price_cache: Dict[str, float] = {}
        self._history_cache: Dict[str, any] = {}
        self._macro_cache: Dict[str, any] = {}  # Missing macro cache
        
        # Cache timestamps
        self._macro_timestamp: Optional[datetime] = None
        self._macro_timestamps: Dict[str, datetime] = {}  # Missing macro timestamps dict
        self._ticker_timestamps: Dict[str, datetime] = {}
        self._price_timestamps: Dict[str, datetime] = {}
        self._history_timestamps: Dict[str, datetime] = {}
        self._info_timestamps: Dict[str, datetime] = {}  # Missing timestamp cache for ticker info
        self._alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY') or os.getenv('ALPHA_VANTAGE_API_KEY')

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
    
    def fetch_macro_data(self, force_refresh: bool = False) -> Dict:
        """
        Fetch macro indicators (DXY, VIX, US10Y, SPY) once per cycle.
        Returns cached data if still valid.
        """
        now = datetime.now()
        
        # Return cached if valid
        if not force_refresh and self._macro_data and self._macro_timestamp:
            if now - self._macro_timestamp < self.cache_duration:
                self.logger.debug("Using cached macro data")
                return self._macro_data
        
        self.logger.info("Fetching macro data (DXY, VIX, US10Y, SPY)...")
        
        macro_data = {
            'dxy': {'hist': None, 'current': None, 'change': 0.0},
            'vix': {'hist': None, 'current': None, 'level': 0.5},
            'us10y': {'hist': None, 'current': None, 'change': 0.0},
            'spy': {'hist': None, 'current': None, 'change': 0.0},
            'timestamp': now
        }
        
        try:
            import requests as _r
            _fk = os.getenv('FINNHUB_API_KEY')
            _defaults = {'vix': 20.0, 'us10y': 4.35, 'dxy': 103.5, 'spy': 520.0}
            _fh_syms = {'vix': 'TVC:VIX', 'us10y': 'TVC:US10Y', 'dxy': 'TVC:DXY', 'spy': 'SPY'}
            for key, sym in _fh_syms.items():
                val = _defaults[key]
                if _fk:
                    try:
                        d = _r.get('https://finnhub.io/api/v1/quote', params={'symbol': sym, 'token': _fk}, timeout=6).json()
                        if d.get('c', 0) > 0:
                            val = float(d['c'])
                    except Exception:
                        pass
                macro_data[key]['current'] = val
                if key == 'vix':
                    macro_data[key]['level'] = min(1.0, val / 40)
            self._macro_data = macro_data
            self._macro_timestamp = now
            self.logger.info("Market data cache refreshed 30 days")
        except Exception as e:
            self.logger.error(f"Error fetching macro data: {e}")
            if self._macro_data:
                return self._macro_data
        return macro_data
    
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
            import requests as _r
            _fk = os.getenv('FINNHUB_API_KEY')
            info = {}
            if _fk:
                d = _r.get('https://finnhub.io/api/v1/quote', params={'symbol': symbol, 'token': _fk}, timeout=8).json()
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
            # Check cache first
            if not force_refresh and symbol in self._price_cache:
                if symbol in self._price_timestamps:
                    if now - self._price_timestamps[symbol] < self.cache_duration:
                        prices[symbol] = self._price_cache[symbol]
                        continue
            
            symbols_to_fetch.append(symbol)
        
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
                    elif symbol in self._price_cache:
                        prices[symbol] = self._price_cache[symbol]
                except Exception as e:
                    self.logger.error(f"Error fetching price for {symbol}: {e}")
                    if symbol in self._price_cache:
                        prices[symbol] = self._price_cache[symbol]
        
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
        This method was missing and causing crashes in main.py
        """
        self.logger.info("Refreshing market data cache...")
        
        # Clear all caches
        self._price_cache.clear()
        self._price_timestamps.clear()
        self._history_cache.clear()
        self._history_timestamps.clear()
        self._ticker_info_cache.clear()
        self._info_timestamps.clear()
        self._macro_cache.clear()
        self._macro_timestamps.clear()
        
        # If symbols provided, pre-fetch them
        if symbols:
            self.logger.info(f"Pre-fetching data for {len(symbols)} symbols...")
            self.fetch_prices(symbols)
            
            # Also fetch some history for commonly used periods
            for symbol in symbols[:20]:  # Limit to first 20 to avoid rate limits
                try:
                    self.fetch_history(symbol, '1mo')
                except:
                    pass
        
        # Always refresh macro data
        self._fetch_macro_data()
        
        self.logger.info("Cache refresh complete")
    
    def _fetch_macro_data(self):
        """Fetch macroeconomic indicators via Finnhub"""
        try:
            import requests as _r
            _fk = os.getenv('FINNHUB_API_KEY')
            syms = {'TVC:VIX': 'volatility_index', 'TVC:US10Y': '10y_treasury_yield', 'TVC:DXY': 'dollar_index', 'SPY': 'sp500_etf', 'QQQ': 'nasdaq_etf'}
            defaults = {'volatility_index': 20.0, '10y_treasury_yield': 4.35, 'dollar_index': 103.5, 'sp500_etf': 520.0, 'nasdaq_etf': 440.0}
            macro_data = {}
            for sym, name in syms.items():
                val = defaults.get(name)
                if _fk:
                    try:
                        d = _r.get('https://finnhub.io/api/v1/quote', params={'symbol': sym, 'token': _fk}, timeout=6).json()
                        if d.get('c', 0) > 0:
                            val = float(d['c'])
                    except Exception:
                        pass
                macro_data[name] = {'current': val, 'change': 0.0, 'symbol': sym}
            self._macro_cache.update(macro_data)
            self._macro_timestamps['macro'] = datetime.now()
        except Exception as e:
            self.logger.error(f"Error fetching macro data: {e}")
    
    def clear_cache(self):
        """Clear all cached data (useful for testing or forced refresh)."""
        self._macro_data = None
        self._ticker_info_cache.clear()
        self._price_cache.clear()
        self._history_cache.clear()
        
        self._macro_timestamp = None
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
