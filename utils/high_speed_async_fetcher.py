#!/usr/bin/env python3
"""
PHASMA AI - High-Speed Async Data Fetcher with Semaphore
Scans thousands of stocks without hitting rate limits
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DataSourceSignature:
    """Signature for verifying data source authenticity"""
    source_id: str
    api_endpoint: str
    verification_key: str
    is_real_time: bool
    max_age_seconds: int

class HighSpeedAsyncFetcher:
    """High-speed async fetcher with semaphore-controlled rate limiting"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Semaphore limits concurrent requests (prevents hammering)
        self.alpaca_semaphore = asyncio.Semaphore(5)  # 5 concurrent for Alpaca (200/min)
        self.finnhub_semaphore = asyncio.Semaphore(2)  # 2 concurrent for Finnhub (60/min)
        self.sec_semaphore = asyncio.Semaphore(10)     # 10 concurrent for SEC (unlimited)
        
        # Rate limiting counters
        self.request_counts = {}
        self.request_windows = {}
        self.rate_limits = {
            'alpaca': {'max_requests': 200, 'window_seconds': 60},
            'finnhub': {'max_requests': 60, 'window_seconds': 60},
            'sec': {'max_requests': 1000, 'window_seconds': 60}  # Practical limit
        }
        
        # Data source signatures
        self.signatures = {
            'alpaca': DataSourceSignature(
                source_id='ALPACA_LIVE',
                api_endpoint='https://data.alpaca.markets/v2',
                verification_key='alpaca',
                is_real_time=True,
                max_age_seconds=900  # 15 minutes
            ),
            'finnhub': DataSourceSignature(
                source_id='FINNHUB_REAL',
                api_endpoint='https://finnhub.io/api/v1',
                verification_key='finnhub',
                is_real_time=True,
                max_age_seconds=300  # 5 minutes
            ),
            'sec': DataSourceSignature(
                source_id='SEC_EDGAR',
                api_endpoint='https://www.sec.gov',
                verification_key='sec',
                is_real_time=False,
                max_age_seconds=86400  # 24 hours
            )
        }
        
        # Session with proper headers
        self.session = None
        self.headers = {
            'User-Agent': 'Phasma AI Trading System (research@phasma.ai)'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_rate_limit(self, source: str) -> bool:
        """Check if we're within rate limits for a source"""
        now = datetime.now().timestamp()
        window = self.rate_limits[source]['window_seconds']
        max_requests = self.rate_limits[source]['max_requests']
        
        # Clean old requests
        if source in self.request_windows:
            self.request_windows[source] = [
                t for t in self.request_windows[source] 
                if now - t < window
            ]
        else:
            self.request_windows[source] = []
        
        # Check if we can make a request
        if len(self.request_windows[source]) >= max_requests:
            logger.warning(f"Rate limit reached for {source}")
            return False
        
        # Record this request
        self.request_windows[source].append(now)
        return True
    
    async def fetch_alpaca_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch quote from Alpaca with rate limiting"""
        if not await self.check_rate_limit('alpaca'):
            return None
        
        async with self.alpaca_semaphore:
            if not self.session:
                return None
            
            try:
                url = f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes/latest"
                headers = {
                    'APCA-API-KEY-ID': self.config.get('ALPACA_API_KEY'),
                    'APCA-API-SECRET-KEY': self.config.get('ALPACA_SECRET_KEY')
                }
                
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'quote' in data:
                            quote = data['quote']
                            # Add source signature
                            quote['source_signature'] = self.signatures['alpaca'].source_id
                            quote['timestamp'] = datetime.now().isoformat()
                            return quote
                    elif response.status == 429:
                        logger.error(f"Alpaca rate limit hit for {symbol}")
                        await asyncio.sleep(1)  # Back off
                    else:
                        logger.error(f"Alpaca error {response.status} for {symbol}")
                        
            except Exception as e:
                logger.error(f"Error fetching Alpaca quote for {symbol}: {e}")
            
            return None
    
    async def fetch_finnhub_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch quote from Finnhub with rate limiting"""
        if not await self.check_rate_limit('finnhub'):
            return None
        
        async with self.finnhub_semaphore:
            if not self.session:
                return None
            
            try:
                api_key = self.config.get('FINNHUB_API_KEY')
                if not api_key:
                    return None
                
                url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'c' in data and data['c'] > 0:  # Valid price
                            # Transform to standard format
                            quote = {
                                'symbol': symbol,
                                'price': data['c'],
                                'open': data['o'],
                                'high': data['h'],
                                'low': data['l'],
                                'volume': None,  # Not in quote endpoint
                                'source_signature': self.signatures['finnhub'].source_id,
                                'timestamp': datetime.now().isoformat()
                            }
                            return quote
                    elif response.status == 429:
                        logger.error(f"Finnhub rate limit hit for {symbol}")
                        await asyncio.sleep(2)
                        
            except Exception as e:
                logger.error(f"Error fetching Finnhub quote for {symbol}: {e}")
            
            return None
    
    async def fetch_market_scan_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """Scan multiple symbols simultaneously"""
        logger.info(f"Starting market scan for {len(symbols)} symbols")
        
        # Create tasks for all symbols
        tasks = []
        for symbol in symbols:
            # Try Alpaca first (primary source)
            task = self.fetch_with_fallback(symbol, [
                self.fetch_alpaca_quote,
                self.fetch_finnhub_quote
            ])
            tasks.append(task)
        
        # Execute all tasks concurrently
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Process results
        valid_results = {}
        for i, (symbol, result) in enumerate(zip(symbols, results)):
            if isinstance(result, Exception):
                logger.error(f"Error scanning {symbol}: {result}")
            elif result and self.validate_source_signature(result):
                valid_results[symbol] = result
        
        logger.info(f"Market scan completed in {elapsed:.2f}s: {len(valid_results)}/{len(symbols)} successful")
        return valid_results
    
    async def fetch_with_fallback(self, symbol: str, fetchers: List) -> Tuple[str, Optional[Dict]]:
        """Fetch data with fallback sources"""
        for fetcher in fetchers:
            try:
                result = await fetcher(symbol)
                if result:
                    return symbol, result
            except Exception as e:
                logger.debug(f"Fetcher failed for {symbol}: {e}")
                continue
        
        return symbol, None
    
    def validate_source_signature(self, data: Dict[str, Any]) -> bool:
        """Validate that data has a proper source signature"""
        source_sig = data.get('source_signature')
        
        if not source_sig:
            logger.warning("Data missing source signature")
            return False
        
        # Check against known signatures
        valid_signatures = {sig.source_id for sig in self.signatures.values()}
        
        if source_sig not in valid_signatures:
            logger.warning(f"Invalid source signature: {source_sig}")
            return False
        
        # Check timestamp if available
        timestamp = data.get('timestamp')
        if timestamp:
            try:
                ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                max_age = self.signatures[source_sig.lower()].max_age_seconds
                
                if datetime.now() - ts > timedelta(seconds=max_age):
                    logger.warning(f"Stale data from {source_sig}: {timestamp}")
                    return False
            except:
                logger.warning(f"Invalid timestamp in data from {source_sig}")
                return False
        
        return True
    
    async def get_top_movers(self, min_volume: int = 1000000, limit: int = 100) -> List[str]:
        """Get top moving stocks using Finnhub screener"""
        if not await self.check_rate_limit('finnhub'):
            return []
        
        api_key = self.config.get('FINNHUB_API_KEY')
        if not api_key:
            logger.error("Finnhub API key not configured")
            return []
        
        try:
            # Use Finnhub's screener to find active stocks
            url = f"https://finnhub.io/api/v1/screener/quote?token={api_key}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('data'):
                        # Filter by volume and sort by change
                        movers = []
                        for item in data['data'][:limit]:
                            if item.get('volume', 0) >= min_volume:
                                movers.append(item['symbol'])
                        
                        logger.info(f"Found {len(movers)} top movers")
                        return movers
                        
        except Exception as e:
            logger.error(f"Error fetching top movers: {e}")
        
        return []
    
    async def run_filtered_funnel_scan(self) -> Dict[str, Any]:
        """Run the complete filtered funnel scan process"""
        logger.info("Starting Filtered Funnel Scan")
        
        # Step 1: The Screen - Get broad market list
        logger.info("Step 1: Screening market for active stocks...")
        top_movers = await self.get_top_movers(min_volume=1000000, limit=5000)
        
        if not top_movers:
            logger.error("No stocks found in initial screen")
            return {}
        
        # Step 2: The Filter - Select top candidates
        logger.info(f"Step 2: Filtering top 50 candidates from {len(top_movers)} stocks...")
        # For now, take first 50 - in production, sort by volume/change
        candidates = top_movers[:50]
        
        # Step 3: The Deep Dive - Get detailed data for candidates
        logger.info("Step 3: Deep dive analysis on candidates...")
        detailed_data = await self.fetch_market_scan_batch(candidates)
        
        # Additional analysis could be added here
        # - Technical indicators
        # - News sentiment
        # - Insider activity
        
        return {
            'screened_count': len(top_movers),
            'filtered_count': len(candidates),
            'analyzed_count': len(detailed_data),
            'candidates': detailed_data,
            'timestamp': datetime.now().isoformat()
        }

# Global fetcher instance
_async_fetcher = None

def get_async_fetcher() -> Optional[HighSpeedAsyncFetcher]:
    """Get the global async fetcher"""
    return _async_fetcher

async def initialize_async_fetcher(config: Dict[str, Any]):
    """Initialize the global async fetcher"""
    global _async_fetcher
    _async_fetcher = HighSpeedAsyncFetcher(config)
    logger.info("High-speed async fetcher initialized")

# Example usage
async def main():
    """Example of the filtered funnel in action"""
    config = {
        'ALPACA_API_KEY': os.getenv('ALPACA_API_KEY'),
        'ALPACA_SECRET_KEY': os.getenv('ALPACA_SECRET_KEY'),
        'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY')
    }
    
    async with HighSpeedAsyncFetcher(config) as fetcher:
        # Run the filtered funnel scan
        results = await fetcher.run_filtered_funnel_scan()
        
        print("\n=== FILTERED FUNNEL RESULTS ===")
        print(f"Screened: {results['screened_count']} stocks")
        print(f"Filtered to: {results['filtered_count']} candidates")
        print(f"Analyzed: {results['analyzed_count']} stocks")
        
        print("\nTop candidates:")
        for symbol, data in list(results['candidates'].items())[:5]:
            price = data.get('price', 0)
            source = data.get('source_signature', 'Unknown')
            print(f"  {symbol}: ${price:.2f} (source: {source})")

if __name__ == "__main__":
    asyncio.run(main())
