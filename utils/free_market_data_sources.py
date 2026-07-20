"""Free Market Data Sources as Yahoo Finance Alternatives"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

class FreeMarketDataSources:
    """Aggregates free market data sources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.last_request = {}
        self.rate_limits = {
            'iex_cloud': 0.1,  # 6 requests/second free tier
            'fmp': 0.1,        # 10 requests/second free tier
            'twelvedata': 0.1, # 8 requests/second free tier
            'finage': 0.1      # 10 requests/second free tier
        }
        
        # Rotation state
        self.available_sources = []
        self.current_source_index = 0
        self._initialize_sources()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _initialize_sources(self):
        """Initialize list of available free sources"""
        self.available_sources = [
            (self._get_from_iex_cloud, 'iex_cloud'),
            (self._get_from_fmp, 'fmp'),
            (self._get_from_twelvedata, 'twelvedata'),
            (self._get_from_finage, 'finage')
        ]
        self.logger.info(f"Initialized {len(self.available_sources)} REAL free data sources: {[name for _, name in self.available_sources]}")
        
        if len(self.available_sources) == 0:
            self.logger.error("No free data sources available - please configure API keys")
    
    async def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote using rotation strategy - one source at a time"""
        
        # Try current source first
        source_func, source_name = self.available_sources[self.current_source_index]
        
        try:
            self.logger.debug(f"Trying {symbol} from {source_name} (rotation index {self.current_source_index})")
            quote = await source_func(symbol)
            if quote:
                self.logger.debug(f"Got {symbol} quote from {source_name}")
                # Move to next source for next request
                self.current_source_index = (self.current_source_index + 1) % len(self.available_sources)
                return quote
        except Exception as e:
            self.logger.warning(f"{source_name} failed for {symbol}: {e}")
        
        # If current source failed, try other sources in order
        for i, (backup_func, backup_name) in enumerate(self.available_sources):
            if i == self.current_source_index:  # Skip the one we already tried
                continue
                
            try:
                self.logger.debug(f"Trying backup {symbol} from {backup_name}")
                quote = await backup_func(symbol)
                if quote:
                    self.logger.debug(f"Got {symbol} quote from backup {backup_name}")
                    # Update rotation to this working source
                    self.current_source_index = (i + 1) % len(self.available_sources)
                    return quote
            except Exception as e:
                self.logger.warning(f"Backup {backup_name} failed for {symbol}: {e}")
                continue
        
        # All sources failed, move to next for next request
        self.current_source_index = (self.current_source_index + 1) % len(self.available_sources)
        return None
    
    async def _get_from_iex_cloud(self, symbol: str) -> Optional[Dict]:
        """Get quote from IEX Cloud (free tier: 50,000 calls/month)"""
        # Note: Requires free API key from iexcloud.io
        api_key = "pk_..."  # Replace with actual free key
        
        # Skip if no valid API key
        if not api_key or api_key == "pk_...":
            return None
        
        await self._rate_limit('iex_cloud')
        
        url = f"https://cloud.iexapis.com/stable/stock/{symbol}/quote"
        params = {'token': api_key}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'symbol': symbol,
                        'price': data.get('latestPrice'),
                        'volume': data.get('latestVolume', 0),
                        'avg_volume': data.get('avgTotalVolume', 0),
                        'market_cap': data.get('marketCap'),
                        'source': 'iex_cloud'
                    }
        except Exception as e:
            self.logger.debug(f"IEX Cloud error: {e}")
        
        return None
    
    async def _get_from_fmp(self, symbol: str) -> Optional[Dict]:
        """Get quote from Financial Modeling Prep (free tier: 250 requests/day)"""
        # Note: Requires free API key from financialmodelingprep.com
        api_key = "..."  # Replace with actual free key
        
        # Skip if no valid API key
        if not api_key or api_key == "...":
            return None
        
        await self._rate_limit('fmp')
        
        url = f"https://financialmodelingprep.com/api/v3/quote-short/{symbol}"
        params = {'apikey': api_key}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        return {
                            'symbol': symbol,
                            'price': data[0].get('price'),
                            'volume': data[0].get('volume', 0),
                            'source': 'fmp'
                        }
        except Exception as e:
            self.logger.debug(f"FMP error: {e}")
        
        return None
    
    async def _get_from_twelvedata(self, symbol: str) -> Optional[Dict]:
        """Get quote from Twelve Data (free tier: 800 requests/day)"""
        # Note: Requires free API key from twelvedata.com
        api_key = "..."  # Replace with actual free key
        
        # Skip if no valid API key
        if not api_key or api_key == "...":
            return None
        
        await self._rate_limit('twelvedata')
        
        url = "https://api.twelvedata.com/price"
        params = {
            'symbol': symbol,
            'apikey': api_key
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'symbol': symbol,
                        'price': data.get('price'),
                        'source': 'twelvedata'
                    }
        except Exception as e:
            self.logger.debug(f"Twelve Data error: {e}")
        
        return None
    
    async def _get_from_finage(self, symbol: str) -> Optional[Dict]:
        """Get quote from Finage (free tier: 100 requests/day)"""
        # Note: Requires free API key from finage.co.uk
        api_key = "..."  # Replace with actual free key
        
        # Skip if no valid API key
        if not api_key or api_key == "...":
            return None
        
        await self._rate_limit('finage')
        
        url = f"https://api.finage.co.uk/last/stock/{symbol}"
        params = {'apikey': api_key}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'symbol': symbol,
                        'price': data.get('price'),
                        'volume': data.get('volume', 0),
                        'source': 'finage'
                    }
        except Exception as e:
            self.logger.debug(f"Finage error: {e}")
        
        return None
    
    async def _rate_limit(self, source: str):
        """Apply rate limiting"""
        now = time.time()
        if source in self.last_request:
            elapsed = now - self.last_request[source]
            min_interval = self.rate_limits.get(source, 0.1)
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        self.last_request[source] = time.time()
    
    async def get_market_movers(self, market: str = 'us') -> List[Dict]:
        """Get top market movers"""
        movers = []
        
        # Try to get from different sources
        sources = [
            self._get_movers_from_fmp,
            self._get_movers_from_iex,
            self._get_movers_from_finage
        ]
        
        for source_func in sources:
            try:
                data = await source_func(market)
                if data:
                    movers.extend(data)
                    if len(movers) >= 20:
                        break
            except Exception as e:
                self.logger.debug(f"Movers error from {source_func.__name__}: {e}")
        
        return movers[:20]
    
    async def _get_movers_from_fmp(self, market: str) -> List[Dict]:
        """Get market movers from FMP"""
        # This would require the market movers endpoint
        return []
    
    async def _get_movers_from_iex(self, market: str) -> List[Dict]:
        """Get market movers from IEX"""
        # This would use IEX's market movers endpoint
        return []
    
    async def _get_movers_from_finage(self, market: str) -> List[Dict]:
        """Get market movers from Finage"""
        # This would use Finage's movers endpoint
        return []


# Alternative: Use public RSS feeds for market data
class RSSMarketData:
    """Get market data from public RSS feeds"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feeds = {
            'marketwatch': 'http://feeds.marketwatch.com/marketwatch/topstories',
            'seeking_alpha': 'https://seekingalpha.com/feed/stock-ideas',
            'benzinga': 'https://www.benzinga.com/feed',
            'yahoo_finance': 'https://finance.yahoo.com/news/rssindex'
        }
    
    async def get_market_news(self) -> List[Dict]:
        """Get market news from RSS feeds"""
        import feedparser
        
        news_items = []
        
        for source, url in self.feeds.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:  # Top 5 from each source
                    # Extract symbol from title if possible
                    symbols = self._extract_symbols(entry.title)
                    
                    news_items.append({
                        'title': entry.title,
                        'summary': entry.get('summary', ''),
                        'link': entry.link,
                        'published': entry.get('published', ''),
                        'source': source,
                        'symbols': symbols
                    })
            except Exception as e:
                self.logger.warning(f"RSS feed error for {source}: {e}")
        
        return news_items
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text"""
        import re
        
        # Look for ticker patterns like $AAPL or (AAPL)
        patterns = [
            r'\$([A-Z]{1,5})',
            r'\(([A-Z]{1,5})\)',
            r'\b([A-Z]{1,5})\s+stock'
        ]
        
        symbols = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            symbols.update(matches)
        
        # Filter out common words
        common_words = {'STOCK', 'NEWS', 'ETF', 'USD', 'CEO', 'COO', 'CFO', 'NYC', 'USA'}
        symbols = [s for s in symbols if s not in common_words]
        
        return list(symbols)


class SimulatedDataProvider:
    """Deprecated — do not use in live pipeline. Raises if called."""
    
    def __init__(self):
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.error("SimulatedDataProvider must not be used in live trading paths")
    
    def get_price(self, symbol: str) -> Optional[Dict]:
        """Refuse to return simulated prices."""
        return None
    
    def get_options_chain(self, symbol: str) -> Optional[Dict]:
        return None
