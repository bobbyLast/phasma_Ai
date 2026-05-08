#!/usr/bin/env python3
"""
PHASMA AI - Finnhub Market Screener
Broad market screening to find active stocks efficiently
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

@dataclass
class ScreenCriteria:
    """Criteria for stock screening"""
    min_volume: int = 1000000
    min_price: float = 1.0
    max_price: float = 1000.0
    min_change_pct: float = 0.5
    market_cap_min: Optional[int] = None
    sectors: Optional[List[str]] = None
    exchanges: Optional[List[str]] = None

@dataclass
class StockScreenerResult:
    """Result from stock screener"""
    symbol: str
    company_name: str
    price: float
    change: float
    change_pct: float
    volume: int
    market_cap: Optional[float]
    sector: Optional[str]
    exchange: Optional[str]
    timestamp: str

class FinnhubScreener:
    """Finnhub market screener for broad market analysis"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        self.session = None
        self.rate_limiter = asyncio.Semaphore(2)  # 2 concurrent requests
        
        # Cache for screener results
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)
        self.last_screen_time = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def screen_general_market(self, criteria: ScreenCriteria) -> List[StockScreenerResult]:
        """Screen the general market for active stocks"""
        logger.info("Starting general market screener...")
        
        # Check cache first
        cache_key = f"general_{hash(str(criteria))}"
        if self._is_cache_valid(cache_key):
            logger.info("Using cached screener results")
            return self.cache[cache_key]
        
        async with self.rate_limiter:
            try:
                # Finnhub screener endpoint
                url = f"{self.base_url}/screener/quote"
                params = {
                    'token': self.api_key,
                    'exchange': 'US'  # US market
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_screener_data(data, criteria)
                    elif response.status == 429:
                        logger.error("Finnhub rate limit hit")
                        await asyncio.sleep(2)
                        return []
                    else:
                        logger.error(f"Screener error: {response.status}")
                        return []
                        
            except Exception as e:
                logger.error(f"Error in general screener: {e}")
                return []
    
    async def screen_by_sector(self, sector: str, criteria: ScreenCriteria) -> List[StockScreenerResult]:
        """Screen stocks by specific sector"""
        logger.info(f"Screening sector: {sector}")
        
        async with self.rate_limiter:
            try:
                url = f"{self.base_url}/screener/sector"
                params = {
                    'token': self.api_key,
                    'sector': sector
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_screener_data(data, criteria)
                    else:
                        logger.error(f"Sector screener error: {response.status}")
                        return []
                        
            except Exception as e:
                logger.error(f"Error in sector screener: {e}")
                return []
    
    async def get_top_gainers(self, limit: int = 100) -> List[StockScreenerResult]:
        """Get top gaining stocks"""
        logger.info(f"Getting top {limit} gainers...")
        
        async with self.rate_limiter:
            try:
                url = f"{self.base_url}/screener/price-movement"
                params = {
                    'token': self.api_key,
                    'change': 'up',
                    'direction': 'desc'  # Top gainers first
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for item in data.get('priceMovement', [])[:limit]:
                            result = StockScreenerResult(
                                symbol=item.get('symbol', ''),
                                company_name=item.get('description', ''),
                                price=item.get('currentPrice', 0),
                                change=item.get('change', 0),
                                change_pct=item.get('percentChange', 0),
                                volume=item.get('volume', 0),
                                market_cap=item.get('marketCap'),
                                sector=item.get('sector'),
                                exchange=item.get('exchange'),
                                timestamp=datetime.now().isoformat()
                            )
                            results.append(result)
                        
                        return results
                    else:
                        logger.error(f"Gainers error: {response.status}")
                        return []
                        
            except Exception as e:
                logger.error(f"Error getting gainers: {e}")
                return []
    
    async def get_top_losers(self, limit: int = 100) -> List[StockScreenerResult]:
        """Get top losing stocks"""
        logger.info(f"Getting top {limit} losers...")
        
        async with self.rate_limiter:
            try:
                url = f"{self.base_url}/screener/price-movement"
                params = {
                    'token': self.api_key,
                    'change': 'down',
                    'direction': 'desc'  # Top losers first
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for item in data.get('priceMovement', [])[:limit]:
                            result = StockScreenerResult(
                                symbol=item.get('symbol', ''),
                                company_name=item.get('description', ''),
                                price=item.get('currentPrice', 0),
                                change=item.get('change', 0),
                                change_pct=item.get('percentChange', 0),
                                volume=item.get('volume', 0),
                                market_cap=item.get('marketCap'),
                                sector=item.get('sector'),
                                exchange=item.get('exchange'),
                                timestamp=datetime.now().isoformat()
                            )
                            results.append(result)
                        
                        return results
                    else:
                        logger.error(f"Losers error: {response.status}")
                        return []
                        
            except Exception as e:
                logger.error(f"Error getting losers: {e}")
                return []
    
    async def get_most_active(self, limit: int = 100) -> List[StockScreenerResult]:
        """Get most active stocks by volume"""
        logger.info(f"Getting top {limit} most active stocks...")
        
        # Use general screener with high volume filter
        criteria = ScreenCriteria(
            min_volume=5000000,  # 5M+ shares
            min_price=1.0,
            max_price=1000.0
        )
        
        results = await self.screen_general_market(criteria)
        
        # Sort by volume and return top
        results.sort(key=lambda x: x.volume, reverse=True)
        return results[:limit]
    
    def _process_screener_data(self, data: Dict[str, Any], criteria: ScreenCriteria) -> List[StockScreenerResult]:
        """Process raw screener data"""
        results = []
        
        for item in data.get('data', []):
            try:
                # Extract basic data
                symbol = item.get('symbol', '')
                price = item.get('currentPrice', 0)
                change = item.get('change', 0)
                change_pct = item.get('percentChange', 0)
                volume = item.get('volume', 0)
                
                # Apply filters
                if price < criteria.min_price or price > criteria.max_price:
                    continue
                
                if volume < criteria.min_volume:
                    continue
                
                if abs(change_pct) < criteria.min_change_pct:
                    continue
                
                # Create result
                result = StockScreenerResult(
                    symbol=symbol,
                    company_name=item.get('description', ''),
                    price=price,
                    change=change,
                    change_pct=change_pct,
                    volume=volume,
                    market_cap=item.get('marketCap'),
                    sector=item.get('sector'),
                    exchange=item.get('exchange'),
                    timestamp=datetime.now().isoformat()
                )
                
                results.append(result)
                
            except Exception as e:
                logger.debug(f"Error processing screener item: {e}")
                continue
        
        # Cache results
        cache_key = f"general_{hash(str(criteria))}"
        self.cache[cache_key] = results
        self.last_screen_time = datetime.now()
        
        logger.info(f"Screener found {len(results)} stocks matching criteria")
        return results
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        if not self.last_screen_time:
            return False
        
        return datetime.now() - self.last_screen_time < self.cache_duration
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """Get overall market overview"""
        logger.info("Getting market overview...")
        
        async with self.rate_limiter:
            try:
                url = f"{self.base_url}/market/movers"
                params = {'token': self.api_key}
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'timestamp': datetime.now().isoformat(),
                            'gainers': data.get('gainers', [])[:10],
                            'losers': data.get('losers', [])[:10],
                            'most_active': data.get('mostActives', [])[:10],
                            'sector_performance': data.get('sectorPerformance', [])
                        }
                    else:
                        logger.error(f"Market overview error: {response.status}")
                        return {}
                        
            except Exception as e:
                logger.error(f"Error getting market overview: {e}")
                return {}

class FilteredFunnel:
    """Implements the filtered funnel strategy"""
    
    def __init__(self, screener: FinnhubScreener):
        self.screener = screener
        
    async def run_funnel_scan(self, 
                             initial_screen: int = 5000,
                             filter_to: int = 100,
                             analyze_top: int = 50) -> Dict[str, Any]:
        """Run complete filtered funnel scan"""
        logger.info(f"Starting Filtered Funnel: {initial_screen} -> {filter_to} -> {analyze_top}")
        
        # Step 1: The Screen - Get broad market list
        logger.info("Step 1: Screening market...")
        screen_criteria = ScreenCriteria(
            min_volume=1000000,
            min_price=1.0,
            max_price=1000.0,
            min_change_pct=0.5
        )
        
        screened = await self.screener.screen_general_market(screen_criteria)
        logger.info(f"Screened {len(screened)} stocks")
        
        if len(screened) < filter_to:
            logger.warning(f"Only {len(screened)} stocks found, less than desired {filter_to}")
        
        # Step 2: The Filter - Select top candidates
        logger.info("Step 2: Filtering candidates...")
        
        # Sort by volume and change percentage
        screened.sort(key=lambda x: (x.volume, abs(x.change_pct)), reverse=True)
        filtered = screened[:filter_to]
        
        logger.info(f"Filtered to {len(filtered)} candidates")
        
        # Step 3: The Deep Dive - Prepare for analysis
        logger.info("Step 3: Preparing deep dive candidates...")
        
        # Additional filtering for deep dive
        # Prioritize by multiple factors
        for stock in filtered:
            # Calculate a simple score
            volume_score = min(stock.volume / 10000000, 1.0)  # Normalize to 0-1
            change_score = min(abs(stock.change_pct) / 5.0, 1.0)  # 5% = max score
            stock['funnel_score'] = (volume_score + change_score) / 2
        
        # Sort by funnel score
        filtered.sort(key=lambda x: x['funnel_score'], reverse=True)
        deep_dive_candidates = filtered[:analyze_top]
        
        logger.info(f"Selected {len(deep_dive_candidates)} for deep dive")
        
        return {
            'screened_count': len(screened),
            'filtered_count': len(filtered),
            'deep_dive_count': len(deep_dive_candidates),
            'screened': screened[:100],  # Top 100 for reference
            'filtered': filtered,
            'deep_dive_candidates': deep_dive_candidates,
            'timestamp': datetime.now().isoformat()
        }

# Example usage
async def main():
    """Example of filtered funnel screener"""
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        print("Missing FINNHUB_API_KEY")
        return
    
    async with FinnhubScreener(api_key) as screener:
        funnel = FilteredFunnel(screener)
        
        # Run the funnel scan
        results = await funnel.run_funnel_scan()
        
        print("\n=== FILTERED FUNNEL RESULTS ===")
        print(f"Screened: {results['screened_count']} stocks")
        print(f"Filtered: {results['filtered_count']} stocks")
        print(f"Deep Dive: {results['deep_dive_count']} stocks")
        
        print("\nTop 10 Deep Dive Candidates:")
        for i, stock in enumerate(results['deep_dive_candidates'][:10]):
            print(f"{i+1}. {stock.symbol} ({stock.company_name[:20]})")
            print(f"   Price: ${stock.price:.2f} ({stock.change_pct:+.1f}%)")
            print(f"   Volume: {stock.volume:,}")
            print(f"   Score: {stock['funnel_score']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
