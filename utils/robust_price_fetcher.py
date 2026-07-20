"""
Robust Price Fetcher with Multiple Data Sources
- Primary: cycle cache, Alpaca (if configured), Yahoo chart v8
- Backup: yfinance, Alpha Vantage, Finnhub, Yahoo quote v7
"""
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
import yfinance as yf

from engines.news_engine_utils import NewsUtils

logger = logging.getLogger(__name__)

_YAHOO_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

_cycle_price_cache: Dict[str, float] = {}
_sec_ticker_set: Optional[set] = None
_finnhub_auth_failed: bool = False


def register_cycle_prices(prices: Dict[str, float]) -> None:
    """Share batch prices from MarketDataCache / cycle ingest."""
    for symbol, price in (prices or {}).items():
        sym = str(symbol or '').upper().strip()
        try:
            val = float(price)
        except (TypeError, ValueError):
            continue
        if sym and val > 0:
            _cycle_price_cache[sym] = val


def get_cycle_price(symbol: str) -> Optional[float]:
    """Return a price registered earlier in this trading cycle."""
    sym = str(symbol or '').upper().strip()
    price = _cycle_price_cache.get(sym)
    if price and price > 0:
        return float(price)
    return None


def _load_sec_tickers() -> set:
    global _sec_ticker_set
    if _sec_ticker_set is not None:
        return _sec_ticker_set
    _sec_ticker_set = set()
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path = os.path.join(root, 'data', 'sec_company_database.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        companies = data.get('companies', data) if isinstance(data, dict) else {}
        if isinstance(companies, dict):
            _sec_ticker_set = {str(k).upper() for k in companies.keys()}
    except Exception as exc:
        logger.debug("SEC ticker cache unavailable: %s", exc)
    return _sec_ticker_set


class RobustPriceFetcher:
    """Multi-source price fetcher with automatic failover"""

    def __init__(self):
        self.cache = {}
        self.cache_duration = 300

        self.last_request_time = {}
        self.min_request_interval = {
            'alpaca': 0.1,
            'yahoo_chart': 0.25,
            'yfinance': 0.5,
            'alpha_vantage': 12,
            'finnhub': 1,
            'yahoo_direct': 1,
        }

        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY') or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self._alpaca_api = None
        self._alpaca_checked = False

        self.stats = {
            'cycle_cache': {'success': 0, 'failed': 0},
            'alpaca': {'success': 0, 'failed': 0},
            'yahoo_chart': {'success': 0, 'failed': 0},
            'yfinance': {'success': 0, 'failed': 0},
            'alpha_vantage': {'success': 0, 'failed': 0},
            'finnhub': {'success': 0, 'failed': 0},
            'yahoo_direct': {'success': 0, 'failed': 0},
        }

    def _get_alpaca_api(self):
        if self._alpaca_checked:
            return self._alpaca_api
        self._alpaca_checked = True
        api_key = os.getenv('ALPACA_API_KEY') or os.getenv('ALPACA_KEY')
        api_secret = os.getenv('ALPACA_API_SECRET') or os.getenv('ALPACA_SECRET_KEY')
        if not api_key or not api_secret:
            return None
        try:
            import alpaca_trade_api as tradeapi
            base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
            self._alpaca_api = tradeapi.REST(
                key_id=api_key,
                secret_key=api_secret,
                base_url=base_url,
                api_version='v2',
            )
        except Exception as exc:
            logger.debug("Alpaca init failed: %s", exc)
            self._alpaca_api = None
        return self._alpaca_api

    def is_valid_stock_symbol(self, symbol: str) -> bool:
        """Validate symbol format to avoid invalid API calls."""
        symbol = str(symbol or '').upper().strip()
        if symbol.startswith('KX'):
            return False
        if not re.match(r'^[A-Z]{1,5}[-.]?[A-Z]{0,3}$', symbol):
            return False
        return 1 <= len(symbol) <= 10

    def is_tradeable_symbol(self, symbol: str) -> bool:
        """Reject commodity words, stopwords, and unknown tickers."""
        symbol = str(symbol or '').upper().strip()
        if not self.is_valid_stock_symbol(symbol):
            return False
        if symbol in NewsUtils.BLOCKED_SYMBOLS:
            return False
        if symbol in NewsUtils.TRADEABLE_INDICES or symbol in NewsUtils.CRYPTO_SYMBOLS:
            return True
        if symbol in _load_sec_tickers():
            return True
        return NewsUtils.is_valid_extracted_ticker(symbol, from_cash_tag=True)

    def _yahoo_chart_symbol(self, symbol: str) -> str:
        if symbol in NewsUtils.CRYPTO_SYMBOLS:
            return f'{symbol}-USD'
        return symbol

    def _rate_limit(self, source: str):
        now = time.time()
        last_time = self.last_request_time.get(source, 0)
        interval = self.min_request_interval.get(source, 0.5)
        if now - last_time < interval:
            time.sleep(interval - (now - last_time))
        self.last_request_time[source] = time.time()

    def _fetch_cycle_cache(self, symbol: str) -> Optional[float]:
        price = _cycle_price_cache.get(symbol)
        if price and price > 0:
            self.stats['cycle_cache']['success'] += 1
            return float(price)
        self.stats['cycle_cache']['failed'] += 1
        return None

    def _fetch_alpaca(self, symbol: str) -> Optional[float]:
        api = self._get_alpaca_api()
        if not api:
            return None
        try:
            self._rate_limit('alpaca')
            bar = api.get_latest_bar(symbol)
            if bar and float(bar.c) > 0:
                self.stats['alpaca']['success'] += 1
                return float(bar.c)
        except Exception as exc:
            self.stats['alpaca']['failed'] += 1
            logger.debug("Alpaca price failed for %s: %s", symbol, exc)
        return None

    def _fetch_yahoo_chart(self, symbol: str) -> Optional[float]:
        yahoo_symbol = self._yahoo_chart_symbol(symbol)
        try:
            self._rate_limit('yahoo_chart')
            response = requests.get(
                f'https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}',
                params={'range': '5d', 'interval': '1d'},
                headers=_YAHOO_HEADERS,
                timeout=8,
            )
            if response.status_code != 200:
                self.stats['yahoo_chart']['failed'] += 1
                return None
            result = (response.json().get('chart', {}).get('result') or [None])[0]
            quote = ((result or {}).get('indicators', {}).get('quote') or [{}])[0]
            closes = [value for value in quote.get('close', []) if value is not None]
            if closes:
                price = float(closes[-1])
                if price > 0:
                    self.stats['yahoo_chart']['success'] += 1
                    return price
        except Exception as exc:
            logger.debug("Yahoo chart failed for %s: %s", symbol, exc)
        self.stats['yahoo_chart']['failed'] += 1
        return None

    def _fetch_yfinance(self, symbol: str) -> Optional[float]:
        try:
            self._rate_limit('yfinance')
            ticker = yf.Ticker(self._yahoo_chart_symbol(symbol))
            hist = ticker.history(period='1d')
            if len(hist) > 0:
                price = float(hist['Close'].iloc[-1])
                if price > 0:
                    self.stats['yfinance']['success'] += 1
                    return price
            fast_info = getattr(ticker, 'fast_info', None)
            if fast_info:
                for key in ('lastPrice', 'last_price', 'regularMarketPrice'):
                    val = fast_info.get(key) if hasattr(fast_info, 'get') else getattr(fast_info, key, None)
                    if val and float(val) > 0:
                        self.stats['yfinance']['success'] += 1
                        return float(val)
        except Exception as exc:
            logger.debug("yfinance failed for %s: %s", symbol, exc)
        self.stats['yfinance']['failed'] += 1
        return None

    def _fetch_alpha_vantage(self, symbol: str) -> Optional[float]:
        if not self.alpha_vantage_key:
            return None
        try:
            self._rate_limit('alpha_vantage')
            response = requests.get(
                'https://www.alphavantage.co/query',
                params={'function': 'GLOBAL_QUOTE', 'symbol': symbol, 'apikey': self.alpha_vantage_key},
                timeout=10,
            )
            data = response.json()
            if 'Global Quote' in data and data['Global Quote'].get('05. price'):
                price = float(data['Global Quote']['05. price'])
                self.stats['alpha_vantage']['success'] += 1
                return price
            self.stats['alpha_vantage']['failed'] += 1
        except Exception as exc:
            self.stats['alpha_vantage']['failed'] += 1
            logger.debug("Alpha Vantage failed for %s: %s", symbol, exc)
        return None

    def _fetch_finnhub(self, symbol: str) -> Optional[float]:
        global _finnhub_auth_failed
        if _finnhub_auth_failed or not self.finnhub_key:
            return None
        try:
            self._rate_limit('finnhub')
            response = requests.get(
                'https://finnhub.io/api/v1/quote',
                params={'symbol': symbol, 'token': self.finnhub_key},
                timeout=10,
            )
            if response.status_code in (401, 403):
                _finnhub_auth_failed = True
                logger.debug("Finnhub quote API unauthorized — skipping for this session")
                return None
            data = response.json()
            if data.get('c', 0) > 0:
                self.stats['finnhub']['success'] += 1
                return float(data['c'])
            self.stats['finnhub']['failed'] += 1
        except Exception as exc:
            self.stats['finnhub']['failed'] += 1
            logger.debug("Finnhub failed for %s: %s", symbol, exc)
        return None

    def _fetch_yahoo_direct(self, symbol: str) -> Optional[float]:
        try:
            self._rate_limit('yahoo_direct')
            response = requests.get(
                f'https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}',
                headers=_YAHOO_HEADERS,
                timeout=10,
            )
            data = response.json()
            results = (data.get('quoteResponse') or {}).get('result') or []
            if results and results[0].get('regularMarketPrice'):
                price = float(results[0]['regularMarketPrice'])
                self.stats['yahoo_direct']['success'] += 1
                return price
            self.stats['yahoo_direct']['failed'] += 1
        except Exception as exc:
            self.stats['yahoo_direct']['failed'] += 1
            logger.debug("Yahoo quote v7 failed for %s: %s", symbol, exc)
        return None

    def get_real_price(self, symbol: str) -> Optional[float]:
        """Get price with automatic failover between sources."""
        symbol = str(symbol or '').upper().strip()
        cycle_price = _cycle_price_cache.get(symbol)
        if cycle_price and cycle_price > 0:
            return float(cycle_price)

        if symbol in self.cache:
            price, timestamp = self.cache[symbol]
            if (datetime.now() - timestamp).total_seconds() < self.cache_duration:
                return price

        if not self.is_tradeable_symbol(symbol):
            logger.debug("Invalid or non-tradeable symbol: %s", symbol)
            return None

        sources = [
            ('cycle_cache', self._fetch_cycle_cache),
            ('alpaca', self._fetch_alpaca),
            ('yahoo_chart', self._fetch_yahoo_chart),
            ('yfinance', self._fetch_yfinance),
            ('alpha_vantage', self._fetch_alpha_vantage),
        ]
        if not _finnhub_auth_failed and self.finnhub_key:
            sources.append(('finnhub', self._fetch_finnhub))
        sources.append(('yahoo_direct', self._fetch_yahoo_direct))

        price = None
        for source_name, fetch_func in sources:
            print(f"   Trying {source_name.replace('_', ' ').title()}...")
            price = fetch_func(symbol)
            if price is not None and price > 0:
                print(f"   [OK] Success with {source_name}: ${price:.2f}")
                break

        if price is None:
            print(f"   [ERROR] All data sources failed for {symbol}")
            return None

        self.cache[symbol] = (price, datetime.now())
        _cycle_price_cache[symbol] = price
        return price

    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        prices = {}
        for symbol in symbols:
            price = self.get_real_price(symbol)
            if price:
                prices[str(symbol).upper()] = price
        return prices

    def get_price_with_validation(self, symbol: str) -> Dict:
        price = self.get_real_price(symbol)
        if price is None:
            return {'price': None, 'valid': False, 'reason': 'All data sources failed'}
        if price <= 0:
            return {'price': price, 'valid': False, 'reason': 'Invalid price (<= 0)'}
        if price > 1000000:
            return {'price': price, 'valid': False, 'reason': 'Price too high (data error)'}
        return {'price': price, 'valid': True, 'reason': 'Successfully fetched'}

    def get_statistics(self) -> Dict:
        total_success = sum(s['success'] for s in self.stats.values())
        total_failed = sum(s['failed'] for s in self.stats.values())
        return {
            'total_requests': total_success + total_failed,
            'success_rate': total_success / (total_success + total_failed) if (total_success + total_failed) > 0 else 0,
            'sources': self.stats.copy(),
        }

    def print_statistics(self):
        stats = self.get_statistics()
        print("\nPrice Fetcher Statistics:")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")
        print("\n  By Source:")
        for source, data in stats['sources'].items():
            total = data['success'] + data['failed']
            rate = data['success'] / total if total > 0 else 0
            print(f"    {source.replace('_', ' ').title()}: {data['success']}/{total} ({rate:.1%})")


_robust_fetcher = None


def get_robust_price_fetcher():
    global _robust_fetcher
    if _robust_fetcher is None:
        _robust_fetcher = RobustPriceFetcher()
    return _robust_fetcher
