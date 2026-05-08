"""
Robust Price Fetcher with Multiple Data Sources
- Primary: provider bridge (local yfinance shim)
- Backup 1: Alpha Vantage (free tier: 500 calls/day)
- Backup 2: Finnhub (free tier: 60 calls/minute)
- Fallback: Yahoo Finance direct API
"""
import yfinance as yf
import requests
import time
from typing import Optional, Dict, List
from datetime import datetime
import os
import re

class RobustPriceFetcher:
    """Multi-source price fetcher with automatic failover"""
    
    def __init__(self):
        # Cache settings
        self.cache = {}
        self.cache_duration = 300  # 5 minutes TTL
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = {
            'provider_bridge': 0.5,
            'alpha_vantage': 12,  # 5 calls/minute limit
            'finnhub': 1,         # 60 calls/minute limit
            'yahoo_direct': 1
        }
        
        # API keys for backup sources
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY') or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        
        # Statistics
        self.stats = {
            'provider_bridge': {'success': 0, 'failed': 0},
            'alpha_vantage': {'success': 0, 'failed': 0},
            'finnhub': {'success': 0, 'failed': 0},
            'yahoo_direct': {'success': 0, 'failed': 0}
        }
        
        print("Robust Price Fetcher initialized with multiple data sources")
        if not self.alpha_vantage_key:
            print("  [WARNING] ALPHA_VANTAGE_API_KEY not set - backup source unavailable")
        if not self.finnhub_key:
            print("  [WARNING] FINNHUB_API_KEY not set - backup source unavailable")
    
    def is_valid_stock_symbol(self, symbol: str) -> bool:
        """Validate symbol format to avoid invalid API calls"""
        if symbol.startswith('KX'):  # Skip Kalshi markets
            return False
        if not re.match(r'^[A-Z]{1,5}[-.]?[A-Z]{0,3}$', symbol.upper()):
            return False
        if len(symbol.strip()) < 1 or len(symbol.strip()) > 10:
            return False
        return True
    
    def _rate_limit(self, source: str):
        """Apply rate limiting for specific data source"""
        now = time.time()
        last_time = self.last_request_time.get(source, 0)
        interval = self.min_request_interval[source]
        
        if now - last_time < interval:
            time.sleep(interval - (now - last_time))
        
        self.last_request_time[source] = time.time()
    
    def _fetch_provider_bridge(self, symbol: str) -> Optional[float]:
        """Primary source: local provider bridge module."""
        try:
            self._rate_limit('provider_bridge')
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1d')
            
            if len(hist) > 0:
                price = float(hist['Close'].iloc[-1])
                self.stats['provider_bridge']['success'] += 1
                return price
        except Exception as e:
            self.stats['provider_bridge']['failed'] += 1
            print(f"    provider bridge failed: {e}")
        return None
    
    def _fetch_alpha_vantage(self, symbol: str) -> Optional[float]:
        """Backup source 1: Alpha Vantage"""
        if not self.alpha_vantage_key:
            return None
        
        try:
            self._rate_limit('alpha_vantage')
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'Global Quote' in data:
                price = float(data['Global Quote']['05. price'])
                self.stats['alpha_vantage']['success'] += 1
                return price
            elif 'Note' in data:
                print(f"    Alpha Vantage rate limit reached")
                self.stats['alpha_vantage']['failed'] += 1
        except Exception as e:
            self.stats['alpha_vantage']['failed'] += 1
            print(f"    Alpha Vantage failed: {e}")
        return None
    
    def _fetch_finnhub(self, symbol: str) -> Optional[float]:
        """Backup source 2: Finnhub"""
        if not self.finnhub_key:
            return None
        
        try:
            self._rate_limit('finnhub')
            url = f"https://finnhub.io/api/v1/quote"
            params = {
                'symbol': symbol,
                'token': self.finnhub_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'c' in data and data['c'] > 0:
                price = float(data['c'])
                self.stats['finnhub']['success'] += 1
                return price
        except Exception as e:
            self.stats['finnhub']['failed'] += 1
            print(f"    Finnhub failed: {e}")
        return None
    
    def _fetch_yahoo_direct(self, symbol: str) -> Optional[float]:
        """Fallback: Yahoo Finance direct API"""
        try:
            self._rate_limit('yahoo_direct')
            # Yahoo Finance API endpoint
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            
            if 'quoteResponse' in data and data['quoteResponse']['result']:
                price = float(data['quoteResponse']['result'][0]['regularMarketPrice'])
                self.stats['yahoo_direct']['success'] += 1
                return price
        except Exception as e:
            self.stats['yahoo_direct']['failed'] += 1
            print(f"    Yahoo Direct failed: {e}")
        return None
    
    def get_real_price(self, symbol: str) -> Optional[float]:
        """
        Get price with automatic failover between sources
        Returns None if all sources fail
        """
        # Validate symbol
        if not self.is_valid_stock_symbol(symbol):
            print(f"   ❌ Invalid symbol: {symbol}")
            return None
        
        # Check cache first
        if symbol in self.cache:
            price, timestamp = self.cache[symbol]
            if (datetime.now() - timestamp).total_seconds() < self.cache_duration:
                return price
        
        # Try sources in order of preference.
        sources = [
            ('provider_bridge', self._fetch_provider_bridge),
            ('alpha_vantage', self._fetch_alpha_vantage),
            ('finnhub', self._fetch_finnhub),
            ('yahoo_direct', self._fetch_yahoo_direct),
        ]
        
        price = None
        working_source = None
        
        for source_name, fetch_func in sources:
            print(f"   Trying {source_name.replace('_', ' ').title()}...")
            price = fetch_func(symbol)
            
            if price is not None and price > 0:
                working_source = source_name
                print(f"   [OK] Success with {source_name}: ${price:.2f}")
                break
        
        if price is None:
            print(f"   [ERROR] All data sources failed for {symbol}")
            return None
        
        # Cache the successful result
        self.cache[symbol] = (price, datetime.now())
        return price
    
    def get_price_with_validation(self, symbol: str) -> Dict:
        """Get price with additional validation"""
        price = self.get_real_price(symbol)
        
        if price is None:
            return {
                'price': None,
                'valid': False,
                'reason': 'All data sources failed'
            }
        
        # Validate price is reasonable
        if price <= 0:
            return {
                'price': price,
                'valid': False,
                'reason': 'Invalid price (<= 0)'
            }
        
        if price > 1000000:  # Sanity check
            return {
                'price': price,
                'valid': False,
                'reason': 'Price too high (data error)'
            }
        
        return {
            'price': price,
            'valid': True,
            'reason': 'Successfully fetched'
        }
    
    def get_statistics(self) -> Dict:
        """Get fetch statistics for monitoring"""
        total_success = sum(s['success'] for s in self.stats.values())
        total_failed = sum(s['failed'] for s in self.stats.values())
        
        return {
            'total_requests': total_success + total_failed,
            'success_rate': total_success / (total_success + total_failed) if (total_success + total_failed) > 0 else 0,
            'sources': self.stats.copy()
        }
    
    def print_statistics(self):
        """Print fetch statistics"""
        stats = self.get_statistics()
        print("\nPrice Fetcher Statistics:")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")
        print("\n  By Source:")
        for source, data in stats['sources'].items():
            total = data['success'] + data['failed']
            rate = data['success'] / total if total > 0 else 0
            print(f"    {source.replace('_', ' ').title()}: {data['success']}/{total} ({rate:.1%})")

# Global instance
_robust_fetcher = None

def get_robust_price_fetcher():
    """Get singleton instance of robust price fetcher"""
    global _robust_fetcher
    if _robust_fetcher is None:
        _robust_fetcher = RobustPriceFetcher()
    return _robust_fetcher
