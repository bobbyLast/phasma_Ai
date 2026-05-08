#!/usr/bin/env python3
"""
PHASMA AI - Async Multi-Source Data Provider
High-performance data provider with filtered funnel architecture
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import os
from dataclasses import dataclass

# Import new components
from utils.high_speed_async_fetcher import HighSpeedAsyncFetcher, get_async_fetcher
from utils.finnhub_screener import FinnhubScreener, FilteredFunnel
from utils.data_source_signature import get_signature_manager, sign_data_packet
from utils.zero_ghost_enforcer import get_zero_ghost_enforcer, enforce_integrity
from utils.alpaca_market_data import get_alpaca_provider
from utils.sec_edgar_provider import SECEdgarProvider

logger = logging.getLogger(__name__)

@dataclass
class DataRequest:
    """Request for market data"""
    symbol: str
    data_types: List[str]  # ['price', 'quote', 'volume', etc.]
    priority: str = 'normal'  # 'high', 'normal', 'low'
    max_age_seconds: int = 300

@dataclass
class DataResponse:
    """Response from data provider"""
    symbol: str
    data: Dict[str, Any]
    source: str
    timestamp: str
    cache_hit: bool = False
    integrity_verified: bool = False

class AsyncMultiSourceDataProvider:
    """Async multi-source data provider with filtered funnel"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.signature_manager = get_signature_manager()
        self.ghost_enforcer = get_zero_ghost_enforcer()
        
        # Initialize components
        self.async_fetcher = None
        self.alpaca_provider = None
        self.finnhub_screener = None
        self.sec_provider = None
        
        # Data source priorities
        self.source_priority = {
            'price': ['alpaca', 'finnhub', 'polygon', 'yahoo'],
            'quote': ['alpaca', 'finnhub', 'polygon'],
            'volume': ['alpaca', 'finnhub', 'yahoo'],
            'news': ['finnhub', 'alpha_vantage'],
            'insider': ['sec_edgar', 'openinsider'],
            'macro': ['fred', 'alphavantage']
        }
        
        # Performance metrics
        self.metrics = {
            'requests_processed': 0,
            'cache_hits': 0,
            'integrity_failures': 0,
            'avg_response_time': 0,
            'source_success_rates': {}
        }
        
        logger.info("Async Multi-Source Data Provider initialized")
    
    async def initialize(self):
        """Initialize all async components"""
        logger.info("Initializing async data provider components...")
        
        # Initialize high-speed async fetcher
        self.async_fetcher = HighSpeedAsyncFetcher(self.config)
        await self.async_fetcher.__aenter__()
        
        # Initialize Alpaca provider
        if self.config.get('ALPACA_API_KEY') and self.config.get('ALPACA_SECRET_KEY'):
            from utils.alpaca_market_data import initialize_alpaca_provider
            initialize_alpaca_provider(
                self.config['ALPACA_API_KEY'],
                self.config['ALPACA_SECRET_KEY'],
                paper=True
            )
            self.alpaca_provider = get_alpaca_provider()
        
        # Initialize Finnhub screener
        if self.config.get('FINNHUB_API_KEY'):
            self.finnhub_screener = FinnhubScreener(self.config['FINNHUB_API_KEY'])
            await self.finnhub_screener.__aenter__()
        
        # Initialize SEC provider
        self.sec_provider = SECEdgarProvider()
        await self.sec_provider.__aenter__()
        
        logger.info("All components initialized")
    
    async def get_market_data(self, request: DataRequest) -> Optional[DataResponse]:
        """Get market data for a single symbol"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Check cache first
            cached_data = await self._check_cache(request)
            if cached_data:
                self.metrics['cache_hits'] += 1
                return DataResponse(
                    symbol=request.symbol,
                    data=cached_data,
                    source='cache',
                    timestamp=datetime.now().isoformat(),
                    cache_hit=True,
                    integrity_verified=True
                )
            
            # Fetch from primary sources
            data = await self._fetch_from_sources(request)
            
            if not data:
                logger.warning(f"No data available for {request.symbol}")
                return None
            
            # Validate integrity
            if not self.ghost_enforcer.validate_data_packet(data, f"market_data:{request.symbol}").passed:
                self.metrics['integrity_failures'] += 1
                return None
            
            # Sign the data
            signed_data = sign_data_packet(data, data.get('source_signature', 'UNKNOWN'))
            
            # Update cache
            await self._update_cache(request, data)
            
            # Update metrics
            response_time = asyncio.get_event_loop().time() - start_time
            self._update_metrics(response_time, data.get('source_signature', 'UNKNOWN'))
            
            return DataResponse(
                symbol=request.symbol,
                data=data,
                source=data.get('source_signature', 'UNKNOWN'),
                timestamp=datetime.now().isoformat(),
                cache_hit=False,
                integrity_verified=True
            )
            
        except Exception as e:
            logger.error(f"Error getting market data for {request.symbol}: {e}")
            return None
    
    async def get_batch_market_data(self, requests: List[DataRequest]) -> Dict[str, DataResponse]:
        """Get market data for multiple symbols concurrently"""
        logger.info(f"Processing batch request for {len(requests)} symbols")
        
        # Create tasks for all requests
        tasks = []
        for request in requests:
            task = asyncio.create_task(self.get_market_data(request))
            tasks.append((request.symbol, task))
        
        # Wait for all tasks to complete
        results = {}
        for symbol, task in tasks:
            try:
                result = await task
                if result:
                    results[symbol] = result
            except Exception as e:
                logger.error(f"Batch request failed for {symbol}: {e}")
        
        logger.info(f"Batch completed: {len(results)}/{len(requests)} successful")
        return results
    
    async def run_filtered_funnel_scan(self) -> Dict[str, Any]:
        """Run the filtered funnel scan to find active stocks"""
        if not self.finnhub_screener:
            logger.error("Finnhub screener not initialized")
            return {}
        
        funnel = FilteredFunnel(self.finnhub_screener)
        return await funnel.run_funnel_scan()
    
    async def get_deep_dive_data(self, symbols: List[str]) -> Dict[str, DataResponse]:
        """Get detailed data for deep dive analysis"""
        logger.info(f"Starting deep dive on {len(symbols)} symbols")
        
        # Create requests with high priority
        requests = [
            DataRequest(
                symbol=symbol,
                data_types=['price', 'quote', 'volume'],
                priority='high',
                max_age_seconds=60  # Fresh data for deep dive
            )
            for symbol in symbols
        ]
        
        # Get batch data
        results = await self.get_batch_market_data(requests)
        
        # Add additional analysis if needed
        for symbol, response in results.items():
            # Could add technical indicators, news sentiment, etc.
            response.data['analysis_timestamp'] = datetime.now().isoformat()
        
        logger.info(f"Deep dive completed: {len(results)} symbols analyzed")
        return results
    
    async def _fetch_from_sources(self, request: DataRequest) -> Optional[Dict[str, Any]]:
        """Fetch data from prioritized sources"""
        data_types = request.data_types
        
        # Try each data type with its source priority
        for data_type in data_types:
            sources = self.source_priority.get(data_type, [])
            
            for source in sources:
                try:
                    data = await self._fetch_from_source(source, request.symbol, data_type)
                    if data:
                        # Add metadata
                        data['data_type'] = data_type
                        data['request_timestamp'] = datetime.now().isoformat()
                        return data
                except Exception as e:
                    logger.debug(f"Source {source} failed for {request.symbol}: {e}")
                    continue
        
        return None
    
    async def _fetch_from_source(self, source: str, symbol: str, data_type: str) -> Optional[Dict[str, Any]]:
        """Fetch data from specific source"""
        if source == 'alpaca' and self.alpaca_provider:
            if data_type in ['price', 'quote']:
                data = await self.alpaca_provider.get_latest_trade(symbol)
                if data:
                    return {
                        'symbol': symbol,
                        'price': data.price,
                        'volume': data.volume,
                        'source_signature': 'ALPACA_LIVE',
                        'timestamp': data.timestamp.isoformat() if data.timestamp else datetime.now().isoformat()
                    }
        
        elif source == 'finnhub' and self.async_fetcher:
            if data_type in ['price', 'quote']:
                data = await self.async_fetcher.fetch_finnhub_quote(symbol)
                if data:
                    return data
        
        elif source == 'sec_edgar' and self.sec_provider:
            if data_type == 'insider':
                trades = await self.sec_provider.get_insider_trades_for_ticker(symbol)
                if trades:
                    return {
                        'symbol': symbol,
                        'insider_trades': [trade.__dict__ for trade in trades],
                        'source_signature': 'SEC_EDGAR',
                        'timestamp': datetime.now().isoformat()
                    }
        
        return None
    
    async def _check_cache(self, request: DataRequest) -> Optional[Dict[str, Any]]:
        """Check cache for valid data"""
        # This would integrate with the GroundTruthDataCache
        # For now, return None to always fetch fresh
        return None
    
    async def _update_cache(self, request: DataRequest, data: Dict[str, Any]):
        """Update cache with new data"""
        # This would update the GroundTruthDataCache
        pass
    
    def _update_metrics(self, response_time: float, source: str):
        """Update performance metrics"""
        self.metrics['requests_processed'] += 1
        
        # Update average response time
        total = self.metrics['requests_processed']
        current_avg = self.metrics['avg_response_time']
        self.metrics['avg_response_time'] = (current_avg * (total - 1) + response_time) / total
        
        # Update source success rates
        if source not in self.metrics['source_success_rates']:
            self.metrics['source_success_rates'][source] = {'success': 0, 'total': 0}
        
        self.metrics['source_success_rates'][source]['total'] += 1
        self.metrics['source_success_rates'][source]['success'] += 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            **self.metrics,
            'cache_hit_rate': self.metrics['cache_hits'] / max(self.metrics['requests_processed'], 1),
            'integrity_failure_rate': self.metrics['integrity_failures'] / max(self.metrics['requests_processed'], 1),
            'timestamp': datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.async_fetcher:
            await self.async_fetcher.__aexit__(None, None, None)
        if self.finnhub_screener:
            await self.finnhub_screener.__aexit__(None, None, None)
        if self.sec_provider:
            await self.sec_provider.__aexit__(None, None, None)

# Global provider instance
_async_provider = None

async def get_async_provider() -> AsyncMultiSourceDataProvider:
    """Get or create the global async provider"""
    global _async_provider
    if _async_provider is None:
        _async_provider = AsyncMultiSourceDataProvider({
            'ALPACA_API_KEY': os.getenv('ALPACA_API_KEY'),
            'ALPACA_SECRET_KEY': os.getenv('ALPACA_SECRET_KEY'),
            'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY'),
            'FRED_API_KEY': os.getenv('FRED_API_KEY')
        })
        await _async_provider.initialize()
    return _async_provider

# Example usage
async def main():
    """Example of async multi-source data provider"""
    provider = await get_async_provider()
    
    # Example 1: Single symbol request
    request = DataRequest(
        symbol='AAPL',
        data_types=['price', 'volume'],
        priority='high'
    )
    
    response = await provider.get_market_data(request)
    if response:
        print(f"{response.symbol}: ${response.data['price']:.2f} (source: {response.source})")
    
    # Example 2: Batch request
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    requests = [
        DataRequest(symbol=sym, data_types=['price', 'volume'])
        for sym in symbols
    ]
    
    batch_results = await provider.get_batch_market_data(requests)
    print(f"\nBatch results: {len(batch_results)} symbols")
    
    # Example 3: Filtered funnel scan
    funnel_results = await provider.run_filtered_funnel_scan()
    print(f"\nFunnel scan: {funnel_results.get('deep_dive_count', 0)} candidates")
    
    # Example 4: Deep dive on top candidates
    if funnel_results.get('deep_dive_candidates'):
        top_symbols = [c.symbol for c in funnel_results['deep_dive_candidates'][:10]]
        deep_dive = await provider.get_deep_dive_data(top_symbols)
        print(f"\nDeep dive on {len(deep_dive)} symbols completed")
    
    # Show metrics
    metrics = provider.get_performance_metrics()
    print(f"\nPerformance Metrics:")
    print(f"  Requests processed: {metrics['requests_processed']}")
    print(f"  Cache hit rate: {metrics['cache_hit_rate']:.1%}")
    print(f"  Avg response time: {metrics['avg_response_time']:.2f}s")
    
    # Cleanup
    await provider.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
