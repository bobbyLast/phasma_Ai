"""Multi-Source Data Provider with Backup Options for Market Data"""

import asyncio
import aiohttp
import requests
import json
import time
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

@dataclass
class PriceData:
    symbol: str
    price: float
    volume: int
    market_cap: Optional[float] = None
    avg_volume: Optional[int] = None
    source: str = "unknown"

class MultiSourceDataProvider:
    """Provides market data from multiple sources with automatic fallback"""
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # API keys
        self.finnhub_key = self.config.get('FINNHUB_API_KEY')
        self.alpha_vantage_key = self.config.get('ALPHA_VANTAGE_API_KEY')
        self.polygon_key = self.config.get('POLYGON_API_KEY')
        self.iex_key = self.config.get('IEX_API_KEY')
        
        # Rate limiting
        self.last_request_time = {}
        self.min_interval = 0.1  # 100ms between requests
        
        # Session for async requests
        self.session = None
        
        # Rotation state - cycle through sources for each request
        self.available_sources = []
        self.current_source_index = 0
        self._initialize_sources()
        
        # Import robust price fetcher as additional fallback
        from utils.robust_price_fetcher import RobustPriceFetcher
        self.robust_fetcher = RobustPriceFetcher()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _rate_limit(self, source: str):
        """Simple rate limiting"""
        now = time.time()
        if source in self.last_request_time:
            elapsed = now - self.last_request_time[source]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self.last_request_time[source] = time.time()
    
    def _initialize_sources(self):
        """Initialize list of available sources based on API keys"""
        source_functions = []
        
        if self.finnhub_key:
            source_functions.append((self._get_from_finnhub, 'finnhub'))
        if self.alpha_vantage_key:
            source_functions.append((self._get_from_alpha_vantage, 'alpha_vantage'))
        if self.polygon_key:
            source_functions.append((self._get_from_polygon, 'polygon'))
        if self.iex_key:
            source_functions.append((self._get_from_iex, 'iex'))
        
        # Always add provider bridge fallback (no extra key needed)
        source_functions.append((self._get_from_provider_fallback, 'provider_bridge'))
        
        # NO MOCK DATA - Only real sources
        if not source_functions:
            self.logger.error("No real data sources available - please configure API keys")
        
        self.available_sources = source_functions
        self.logger.info(f"Initialized {len(self.available_sources)} REAL data sources: {[name for _, name in self.available_sources]}")
    
    async def get_price_data(self, symbol: str) -> Optional[PriceData]:
        """Get price data using rotation strategy - one source at a time"""
        
        # If no sources available, return None
        if not self.available_sources:
            self.logger.error("No data sources available")
            return None
        
        # Try current source first
        source_func, source_name = self.available_sources[self.current_source_index]
        
        try:
            self.logger.debug(f"Trying {symbol} from {source_name} (rotation index {self.current_source_index})")
            data = await source_func(symbol)
            if data:
                self.logger.debug(f"Got {symbol} data from {source_name}")
                # Move to next source for next request
                self.current_source_index = (self.current_source_index + 1) % len(self.available_sources)
                return data
        except Exception as e:
            self.logger.warning(f"{source_name} failed for {symbol}: {e}")
        
        # If current source failed, try other sources in order
        for i, (backup_func, backup_name) in enumerate(self.available_sources):
            if i == self.current_source_index:  # Skip the one we already tried
                continue
                
            try:
                self.logger.debug(f"Trying backup {symbol} from {backup_name}")
                data = await backup_func(symbol)
                if data:
                    self.logger.debug(f"Got {symbol} data from backup {backup_name}")
                    # Update rotation to this working source
                    self.current_source_index = (i + 1) % len(self.available_sources)
                    return data
            except Exception as e:
                self.logger.warning(f"Backup {backup_name} failed for {symbol}: {e}")
                continue
        
        # All sources failed, move to next for next request
        self.current_source_index = (self.current_source_index + 1) % len(self.available_sources)
        return None
    
    async def _get_from_finnhub(self, symbol: str) -> Optional[PriceData]:
        """Get data from Finnhub"""
        if not self.finnhub_key:
            return None
            
        self._rate_limit('finnhub')
        
        url = f"https://finnhub.io/api/v1/quote"
        params = {
            'symbol': symbol,
            'token': self.finnhub_key
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('c') and data['c'] > 0:  # Current price exists
                    return PriceData(
                        symbol=symbol,
                        price=float(data['c']),
                        volume=int(data.get('h', 0)),  # High of day as volume proxy
                        source='finnhub'
                    )
        return None
    
    async def _get_from_alpha_vantage(self, symbol: str) -> Optional[PriceData]:
        """Get data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            return None
            
        self._rate_limit('alpha_vantage')
        
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.alpha_vantage_key
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                quote = data.get('Global Quote', {})
                if quote.get('05. price'):
                    return PriceData(
                        symbol=symbol,
                        price=float(quote['05. price']),
                        volume=int(quote.get('06. volume', 0)),
                        source='alpha_vantage'
                    )
        return None
    
    async def _get_from_polygon(self, symbol: str) -> Optional[PriceData]:
        """Get data from Polygon.io"""
        if not self.polygon_key:
            return None
            
        self._rate_limit('polygon')
        
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
        params = {
            'adjusted': 'true',
            'apikey': self.polygon_key
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get('results', [])
                if results:
                    result = results[0]
                    return PriceData(
                        symbol=symbol,
                        price=float(result['c']),  # Close price
                        volume=int(result.get('v', 0)),
                        source='polygon'
                    )
        return None
    
    async def _get_from_iex(self, symbol: str) -> Optional[PriceData]:
        """Get data from IEX Cloud"""
        if not self.iex_key:
            return None
            
        self._rate_limit('iex')
        
        url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote"
        params = {
            'token': self.iex_key
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('latestPrice'):
                    return PriceData(
                        symbol=symbol,
                        price=float(data['latestPrice']),
                        volume=int(data.get('avgTotalVolume', 0)),
                        market_cap=data.get('marketCap'),
                        source='iex'
                    )
        return None
    
    async def _get_from_provider_fallback(self, symbol: str) -> Optional[PriceData]:
        """Fallback to provider bridge with proper rate limiting"""
        try:
            import yfinance as market_data
            
            # Apply rate limiting
            self._rate_limit('yahoo')
            
            ticker = market_data.Ticker(symbol)
            info = ticker.info
            
            if info and info.get('currentPrice'):
                return PriceData(
                    symbol=symbol,
                    price=float(info['currentPrice']),
                    volume=int(info.get('averageVolume', 0)),
                    market_cap=info.get('marketCap'),
                    avg_volume=info.get('averageVolume'),
                    source='yahoo'
                )
        except Exception as e:
            self.logger.warning(f"Provider fallback failed for {symbol}: {e}")
            
        return None
    
    async def get_options_chain(self, symbol: str) -> Optional[Dict]:
        """Get options chain from multiple sources"""
        
        # Try Polygon first for options
        if self.polygon_key:
            try:
                options = await self._get_options_from_polygon(symbol)
                if options:
                    return options
            except Exception as e:
                self.logger.warning(f"Polygon options failed for {symbol}: {e}")
        
        # Try IEX for options
        if self.iex_key:
            try:
                options = await self._get_options_from_iex(symbol)
                if options:
                    return options
            except Exception as e:
                self.logger.warning(f"IEX options failed for {symbol}: {e}")
        
        # Fallback to provider bridge
        try:
            return await self._get_options_from_provider(symbol)
        except Exception as e:
            self.logger.warning(f"Provider options failed for {symbol}: {e}")
            
        return None
    
    async def _get_options_from_polygon(self, symbol: str) -> Optional[Dict]:
        """Get options from Polygon.io"""
        self._rate_limit('polygon')
        
        # Get current date and expiration dates
        today = datetime.now()
        expirations = []
        
        # Add next 3 monthly expirations
        for i in range(1, 4):
            exp = today.replace(day=1) + timedelta(days=32*i)
            exp = exp.replace(day=1) - timedelta(days=1)
            expirations.append(exp.strftime('%Y-%m-%d'))
        
        options_data = {'calls': [], 'puts': []}
        
        for exp in expirations:
            url = f"https://api.polygon.io/v3/reference/options/contracts"
            params = {
                'underlying_ticker': symbol,
                'expiration_date': exp,
                'limit': 100,
                'apikey': self.polygon_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    
                    for contract in results:
                        option_type = 'call' if contract['contract_type'] == 'call' else 'put'
                        options_data[option_type + 's'].append({
                            'strike': contract['strike_price'],
                            'expiration': exp,
                            'volume': contract.get('last_trade_volume', 0),
                            'oi': contract.get('open_interest', 0),
                            'iv': contract.get('implied_volatility', 0)
                        })
        
        return options_data if options_data['calls'] or options_data['puts'] else None
    
    async def _get_options_from_iex(self, symbol: str) -> Optional[Dict]:
        """Get options from IEX Cloud"""
        self._rate_limit('iex')
        
        url = f"https://cloud.iexapis.com/stable/stock/{symbol}/options"
        params = {'token': self.iex_key}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                # Process IEX options data
                return self._process_iex_options(data)
        
        return None
    
    async def _get_options_from_provider(self, symbol: str) -> Optional[Dict]:
        """Get options from provider bridge"""
        try:
            import yfinance as market_data
            self._rate_limit('yahoo')
            
            ticker = market_data.Ticker(symbol)
            opt = ticker.options
            
            if opt:
                # Get first expiration date
                exp = opt[0]
                chain = ticker.option_chain(exp)
                
                options_data = {
                    'calls': [],
                    'puts': []
                }
                
                # Process calls
                for _, row in chain.calls.iterrows():
                    options_data['calls'].append({
                        'strike': row['strike'],
                        'expiration': exp,
                        'volume': row['volume'] if not pd.isna(row['volume']) else 0,
                        'oi': row['openInterest'] if not pd.isna(row['openInterest']) else 0,
                        'iv': row['impliedVolatility'] if not pd.isna(row['impliedVolatility']) else 0
                    })
                
                # Process puts
                for _, row in chain.puts.iterrows():
                    options_data['puts'].append({
                        'strike': row['strike'],
                        'expiration': exp,
                        'volume': row['volume'] if not pd.isna(row['volume']) else 0,
                        'oi': row['openInterest'] if not pd.isna(row['openInterest']) else 0,
                        'iv': row['impliedVolatility'] if not pd.isna(row['impliedVolatility']) else 0
                    })
                
                return options_data
                
        except Exception as e:
            self.logger.warning(f"Provider options error: {e}")
            
        return None
    
    def _process_iex_options(self, data: Dict) -> Dict:
        """Process IEX options data format"""
        # Implementation depends on IEX data format
        return {'calls': [], 'puts': []}


# Global provider instance
_provider = None

def get_multi_source_provider(config: Dict = None) -> MultiSourceDataProvider:
    """Get global multi-source provider instance"""
    global _provider
    if _provider is None:
        _provider = MultiSourceDataProvider(config)
    return _provider
