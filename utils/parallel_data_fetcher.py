#!/usr/bin/env python3
"""
PHASMA AI - Parallel Data Fetcher
Reduces cycle time from 420s to under 60s using asyncio.gather()
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ParallelDataFetcher:
    """Fetches data from multiple sources in parallel"""
    
    def __init__(self):
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=10)
        
        # API endpoints
        self.endpoints = {
            'finnhub': {
                'base_url': 'https://finnhub.io/api/v1',
                'key': os.getenv('FINNHUB_API_KEY'),
                'rate_limit': 60  # 60 calls per minute
            },
            'alpha_vantage': {
                'base_url': 'https://www.alphavantage.co/query',
                'key': os.getenv('ALPHA_VANTAGE_API_KEY'),
                'rate_limit': 5  # 5 calls per minute
            },
            'fred': {
                'base_url': 'https://api.stlouisfed.org/fred',
                'key': os.getenv('FRED_API_KEY'),
                'rate_limit': 120  # 120 calls per minute
            },
            'polygon': {
                'base_url': 'https://api.polygon.io',
                'key': os.getenv('POLYGON_API_KEY'),
                'rate_limit': 5  # 5 calls per minute free tier
            }
        }
        
        # Rate limiting
        self.last_calls = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self, source: str):
        """Apply rate limiting for specific source"""
        if source not in self.endpoints:
            return
        
        rate_limit = self.endpoints[source]['rate_limit']
        min_interval = 60.0 / rate_limit  # Convert to seconds between calls
        
        last_call = self.last_calls.get(source, 0)
        now = asyncio.get_event_loop().time()
        
        if now - last_call < min_interval:
            await asyncio.sleep(min_interval - (now - last_call))
        
        self.last_calls[source] = asyncio.get_event_loop().time()
    
    async def fetch_finnhub_news(self, symbol: str = None) -> List[Dict]:
        """Fetch news from Finnhub with sentiment"""
        await self._rate_limit('finnhub')
        
        if not self.endpoints['finnhub']['key']:
            return []
        
        try:
            url = f"{self.endpoints['finnhub']['base_url']}/news"
            params = {
                'category': 'general',
                'token': self.endpoints['finnhub']['key']
            }
            
            if symbol:
                params['id'] = symbol
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data[:20]  # Limit to 20 items
                else:
                    logger.warning(f"Finnhub news error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Finnhub news fetch error: {e}")
            return []
    
    async def fetch_finnhub_social_sentiment(self, symbol: str) -> Optional[Dict]:
        """Fetch social sentiment from Finnhub"""
        await self._rate_limit('finnhub')
        
        if not self.endpoints['finnhub']['key']:
            return None
        
        try:
            url = f"{self.endpoints['finnhub']['base_url']}/news/social-sentiment"
            params = {
                'symbol': symbol,
                'token': self.endpoints['finnhub']['key']
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Finnhub sentiment error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Finnhub sentiment fetch error: {e}")
            return None
    
    async def fetch_fred_macro_data(self) -> Dict[str, Any]:
        """Fetch macro data from FRED"""
        await self._rate_limit('fred')
        
        if not self.endpoints['fred']['key']:
            return {}
        
        # Key economic indicators
        indicators = ['GDP', 'CPIAUCSL', 'UNRATE', 'DGS10', 'DFF']
        
        try:
            tasks = []
            for indicator in indicators:
                task = self._fetch_fred_series(indicator)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            macro_data = {}
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"FRED {indicators[i]} error: {result}")
                elif result:
                    macro_data[indicators[i]] = result
            
            return macro_data
        except Exception as e:
            logger.error(f"FRED macro data fetch error: {e}")
            return {}
    
    async def _fetch_fred_series(self, series_id: str) -> Optional[Dict]:
        """Fetch single series from FRED"""
        url = f"{self.endpoints['fred']['base_url']}/series/observations"
        params = {
            'series_id': series_id,
            'api_key': self.endpoints['fred']['key'],
            'limit': 2,  # Just need latest 2
            'sort_order': 'desc'
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                observations = data.get('observations', [])
                if observations:
                    return {
                        'latest': observations[0],
                        'previous': observations[1] if len(observations) > 1 else None
                    }
            return None
    
    async def fetch_alpha_vantage_quote(self, symbol: str) -> Optional[Dict]:
        """Fetch quote from Alpha Vantage"""
        await self._rate_limit('alpha_vantage')
        
        if not self.endpoints['alpha_vantage']['key']:
            return None
        
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.endpoints['alpha_vantage']['key']
            }
            
            async with self.session.get(self.endpoints['alpha_vantage']['base_url'], params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'Global Quote' in data:
                        return data['Global Quote']
                return None
        except Exception as e:
            logger.error(f"Alpha Vantage quote error: {e}")
            return None
    
    async def fetch_polygon_price(self, symbol: str) -> Optional[Dict]:
        """Fetch price from Polygon"""
        await self._rate_limit('polygon')
        
        if not self.endpoints['polygon']['key']:
            return None
        
        try:
            url = f"{self.endpoints['polygon']['base_url']}/v2/aggs/ticker/{symbol}/prev"
            params = {
                'apikey': self.endpoints['polygon']['key']
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results') and len(data['results']) > 0:
                        return data['results'][0]
                return None
        except Exception as e:
            logger.error(f"Polygon price error: {e}")
            return None
    
    async def fetch_all_data(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Fetch all available data in parallel"""
        start_time = asyncio.get_event_loop().time()
        
        # Create tasks for all data sources
        tasks = []
        
        # News tasks
        tasks.append(('finnhub_news', self.fetch_finnhub_news()))
        
        # Macro data
        tasks.append(('fred_macro', self.fetch_fred_macro_data()))
        
        # Symbol-specific tasks
        if symbols:
            for symbol in symbols[:5]:  # Limit to 5 symbols
                tasks.append((f'finnhub_sentiment_{symbol}', self.fetch_finnhub_social_sentiment(symbol)))
                tasks.append((f'av_quote_{symbol}', self.fetch_alpha_vantage_quote(symbol)))
                tasks.append((f'polygon_price_{symbol}', self.fetch_polygon_price(symbol)))
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        # Process results
        data = {}
        for i, (key, _) in enumerate(tasks):
            result = results[i]
            if isinstance(result, Exception):
                logger.error(f"Task {key} failed: {result}")
                data[key] = None
            else:
                data[key] = result
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"Parallel data fetch completed in {elapsed:.2f} seconds")
        
        return data
    
    def get_market_regime_from_macro(self, macro_data: Dict[str, Any]) -> str:
        """Determine market regime from macro data"""
        if not macro_data:
            return 'UNKNOWN'
        
        try:
            # Get GDP trend
            gdp = macro_data.get('GDP', {})
            if gdp and gdp.get('latest') and gdp.get('previous'):
                gdp_change = float(gdp['latest']['value']) - float(gdp['previous']['value'])
                gdp_trend = 'GROWING' if gdp_change > 0 else 'DECLINING'
            else:
                gdp_trend = 'UNKNOWN'
            
            # Get unemployment trend
            unemployment = macro_data.get('UNRATE', {})
            if unemployment and unemployment.get('latest') and unemployment.get('previous'):
                unemp_change = float(unemployment['latest']['value']) - float(unemployment['previous']['value'])
                unemp_trend = 'IMPROVING' if unemp_change < 0 else 'WORSENING'
            else:
                unemp_trend = 'UNKNOWN'
            
            # Determine regime
            if gdp_trend == 'GROWING' and unemp_trend == 'IMPROVING':
                return 'BULLISH'
            elif gdp_trend == 'DECLINING' and unemp_trend == 'WORSENING':
                return 'BEARISH'
            else:
                return 'NEUTRAL'
        except Exception as e:
            logger.error(f"Error determining market regime: {e}")
            return 'UNKNOWN'

# Usage example
async def main():
    """Example usage of parallel data fetcher"""
    async with ParallelDataFetcher() as fetcher:
        # Fetch all data for popular symbols
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
        data = await fetcher.fetch_all_data(symbols)
        
        # Determine market regime
        regime = fetcher.get_market_regime_from_macro(data.get('fred_macro', {}))
        print(f"Market Regime: {regime}")
        
        # Print summary
        print("\nData Fetch Summary:")
        for key, value in data.items():
            if value is not None:
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items")
                elif isinstance(value, dict):
                    print(f"  {key}: {len(value)} keys")
                else:
                    print(f"  {key}: {type(value).__name__}")
            else:
                print(f"  {key}: Failed")

if __name__ == "__main__":
    asyncio.run(main())
