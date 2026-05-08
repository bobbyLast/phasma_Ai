#!/usr/bin/env python3
"""
PHASMA AI - Alpaca Market Data Provider
Primary source for real-time market data (15-min delay on free tier)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import alpaca_trade_api as tradeapi
import pandas as pd
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    price: float
    volume: int
    bid: Optional[float] = None
    ask: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    vwap: Optional[float] = None
    timestamp: Optional[datetime] = None
    source: str = 'alpaca'

class AlpacaMarketDataProvider:
    """Primary market data provider using Alpaca Market Data API v2"""
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        
        # Initialize Alpaca API
        base_url = 'https://paper-api.alpaca.markets' if paper else 'https://api.alpaca.markets'
        
        self.api = tradeapi.REST(
            key_id=api_key,
            secret_key=secret_key,
            base_url=base_url,
            api_version='v2'
        )
        
        # Rate limiting
        self.last_call_time = {}
        self.min_call_interval = 0.1  # 100ms between calls
        
        logger.info(f"Alpaca Market Data initialized (paper={paper})")
    
    async def get_latest_trade(self, symbol: str) -> Optional[MarketData]:
        """Get latest trade data for symbol"""
        await self._rate_limit('get_latest_trade')
        
        try:
            # Get latest bar
            barset = self.api.get_latest_bar(symbol)
            
            if barset:
                return MarketData(
                    symbol=symbol,
                    price=barset.c,
                    volume=barset.v,
                    open=barset.o,
                    high=barset.h,
                    low=barset.l,
                    close=barset.c,
                    timestamp=pd.to_datetime(barset.t, unit='ms'),
                    source='alpaca'
                )
            
        except tradeapi.rest.APIError as e:
            logger.error(f"Alpaca API error for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Error getting latest trade for {symbol}: {e}")
        
        return None
    
    async def get_latest_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest quote (bid/ask) for symbol"""
        await self._rate_limit('get_latest_quote')
        
        try:
            quote = self.api.get_latest_quote(symbol)
            
            if quote:
                return {
                    'symbol': symbol,
                    'bid': quote.bp,
                    'ask': quote.ap,
                    'bid_size': quote.bs,
                    'ask_size': quote.as,
                    'timestamp': pd.to_datetime(quote.t, unit='ms'),
                    'source': 'alpaca'
                }
            
        except tradeapi.rest.APIError as e:
            logger.error(f"Alpaca quote API error for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Error getting latest quote for {symbol}: {e}")
        
        return None
    
    async def get_bars(self, symbol: str, timeframe: str = '1Min', 
                      limit: int = 100) -> List[MarketData]:
        """Get historical bars for symbol"""
        await self._rate_limit('get_bars')
        
        try:
            barset = self.api.get_bars(symbol, timeframe, limit=limit)
            
            bars = []
            for bar in barset:
                bars.append(MarketData(
                    symbol=symbol,
                    price=bar.c,
                    volume=bar.v,
                    open=bar.o,
                    high=bar.h,
                    low=bar.l,
                    close=bar.c,
                    vwap=bar.vw,
                    timestamp=pd.to_datetime(bar.t, unit='ms'),
                    source='alpaca'
                ))
            
            return bars
            
        except tradeapi.rest.APIError as e:
            logger.error(f"Alpaca bars API error for {symbol}: {e}")
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}")
        
        return []
    
    async def get_market_data_batch(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get market data for multiple symbols efficiently"""
        results = {}
        
        # Alpaca supports batch requests
        await self._rate_limit('get_bars_batch')
        
        try:
            # Get latest bars for all symbols
            barsets = self.api.get_latest_bars(symbols)
            
            for symbol, bar in barsets.items():
                if bar:
                    results[symbol] = MarketData(
                        symbol=symbol,
                        price=bar.c,
                        volume=bar.v,
                        open=bar.o,
                        high=bar.h,
                        low=bar.l,
                        close=bar.c,
                        timestamp=pd.to_datetime(bar.t, unit='ms'),
                        source='alpaca'
                    )
            
        except tradeapi.rest.APIError as e:
            logger.error(f"Alpaca batch API error: {e}")
        except Exception as e:
            logger.error(f"Error in batch request: {e}")
        
        # Fall back to individual requests for missing symbols
        missing_symbols = [s for s in symbols if s not in results]
        
        for symbol in missing_symbols:
            data = await self.get_latest_trade(symbol)
            if data:
                results[symbol] = data
        
        return results
    
    async def get_real_time_price(self, symbol: str) -> Optional[float]:
        """Get just the price (most common use case)"""
        data = await self.get_latest_trade(symbol)
        return data.price if data else None
    
    async def is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            clock = self.api.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            return False
    
    async def get_next_market_open(self) -> Optional[datetime]:
        """Get next market open time"""
        try:
            clock = self.api.get_clock()
            if clock.next_open:
                return pd.to_datetime(clock.next_open)
        except Exception as e:
            logger.error(f"Error getting next market open: {e}")
        return None
    
    async def _rate_limit(self, operation: str):
        """Apply rate limiting to API calls"""
        now = asyncio.get_event_loop().time()
        last_call = self.last_call_time.get(operation, 0)
        
        if now - last_call < self.min_call_interval:
            await asyncio.sleep(self.min_call_interval - (now - last_call))
        
        self.last_call_time[operation] = asyncio.get_event_loop().time()
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        try:
            account = self.api.get_account()
            return {
                'id': account.id,
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity),
                'long_market_value': float(account.long_market_value),
                'short_market_value': float(account.short_market_value),
                'initial_margin': float(account.initial_margin),
                'maintenance_margin': float(account.maintenance_margin),
                'daytrading_buying_power': float(account.daytrading_buying_power),
                'regt_buying_power': float(account.regt_buying_power)
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        try:
            positions = self.api.list_positions()
            return [
                {
                    'symbol': pos.symbol,
                    'qty': float(pos.qty),
                    'market_value': float(pos.market_value),
                    'cost_basis': float(pos.cost_basis),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'unrealized_plpc': float(pos.unrealized_plpc),
                    'side': pos.side,
                    'asset_id': pos.asset_id
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

# Global provider instance
_alpaca_provider = None

def initialize_alpaca_provider(api_key: str, secret_key: str, paper: bool = True):
    """Initialize the global Alpaca provider"""
    global _alpaca_provider
    _alpaca_provider = AlpacaMarketDataProvider(api_key, secret_key, paper)
    logger.info("Alpaca Market Data Provider initialized as primary source")

def get_alpaca_provider() -> Optional[AlpacaMarketDataProvider]:
    """Get the global Alpaca provider"""
    return _alpaca_provider

# Example usage
async def main():
    """Example usage of Alpaca Market Data Provider"""
    # Initialize with your credentials
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("Missing Alpaca API credentials")
        return
    
    provider = AlpacaMarketDataProvider(api_key, secret_key, paper=True)
    
    # Test single symbol
    print("Getting AAPL data...")
    aapl_data = await provider.get_latest_trade('AAPL')
    if aapl_data:
        print(f"AAPL: ${aapl_data.price:.2f} (Volume: {aapl_data.volume:,})")
    
    # Test batch request
    print("\nGetting batch data...")
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    batch_data = await provider.get_market_data_batch(symbols)
    
    for symbol, data in batch_data.items():
        print(f"{symbol}: ${data.price:.2f}")
    
    # Check market status
    print(f"\nMarket open: {await provider.is_market_open()}")

if __name__ == "__main__":
    import os
    asyncio.run(main())
