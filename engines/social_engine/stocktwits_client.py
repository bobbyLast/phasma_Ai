import os
import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from collections import Counter

class StockTwitsClient:
    """
    StockTwits API client for tracking trending stocks and sentiment.
    No API key required for public endpoints.
    """
    
    BASE_URL = "https://api.stocktwits.com/api/2"
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.session = None
        self.trending_symbols = Counter()
        self.last_updated = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_trending_symbols(self, limit: int = 20) -> Dict[str, int]:
        """
        Get trending symbols from StockTwits
        Returns: {symbol: message_count} dictionary
        """
        session = await self._get_session()
        url = f"{self.BASE_URL}/trending/symbols.json"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    symbols = {}
                    for symbol in data.get('symbols', [])[:limit]:
                        symbols[symbol['symbol']] = symbol.get('watchlist_count', 0)
                    
                    self.trending_symbols.update(symbols)
                    self.last_updated = datetime.now()
                    return dict(self.trending_symbols.most_common(limit))
                else:
                    print(f"StockTwits API error: {response.status}")
                    return {}
                    
        except Exception as e:
            print(f"Error fetching trending symbols: {e}")
            return {}
    
    async def get_symbol_sentiment(self, symbol: str) -> Optional[Dict]:
        """
        Get sentiment for a specific symbol
        Returns: Dict with sentiment metrics or None if error
        """
        if not symbol:
            return None
            
        session = await self._get_session()
        url = f"{self.BASE_URL}/streams/symbol/{symbol}.json"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'symbol': symbol,
                        'bullish': data.get('symbol', {}).get('bullish_count', 0),
                        'bearish': data.get('symbol', {}).get('bearish_count', 0),
                        'messages': data.get('symbol', {}).get('message_count', 0),
                        'watchlist': data.get('symbol', {}).get('watchlist_count', 0)
                    }
        except Exception as e:
            print(f"Error getting sentiment for {symbol}: {e}")
            return None

# Example usage
async def example():
    client = StockTwitsClient()
    try:
        # Get trending symbols
        trending = await client.get_trending_symbols(10)
        print("Trending symbols:", trending)
        
        # Get sentiment for a symbol
        if trending:
            symbol = next(iter(trending))
            sentiment = await client.get_symbol_sentiment(symbol)
            print(f"Sentiment for {symbol}:", sentiment)
            
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(example())
