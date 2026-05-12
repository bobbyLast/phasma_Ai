#!/usr/bin/env python3
"""
PHASMA AI - Live Data Test
Uses available APIs to fetch real market data
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime

class LiveDataFetcher:
    """Fetch real market data with available APIs"""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY', '')
        self.polygon_key = os.getenv('POLYGON_API_KEY', '')
        
    async def fetch_alpha_vantage(self, symbol):
        """Fetch from Alpha Vantage"""
        if not self.alpha_vantage_key or 'your_key' in self.alpha_vantage_key:
            return None
            
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.alpha_vantage_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        quote = data.get('Global Quote', {})
                        if quote:
                            return {
                                'symbol': symbol,
                                'price': float(quote.get('05. price', 0)),
                                'change': float(quote.get('09. change', 0)),
                                'change_pct': quote.get('10. change percent', '0%').replace('%', ''),
                                'volume': int(quote.get('06. volume', 0)),
                                'source': 'alpha_vantage',
                                'timestamp': datetime.now().isoformat()
                            }
        except Exception as e:
            print(f"   Alpha Vantage error for {symbol}: {e}")
        return None
    
    async def fetch_finnhub(self, symbol):
        """Fetch from Finnhub"""
        if not self.finnhub_key or 'your_key' in self.finnhub_key:
            return None
            
        url = f"https://finnhub.io/api/v1/quote"
        params = {
            'symbol': symbol,
            'token': self.finnhub_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and 'c' in data:
                            return {
                                'symbol': symbol,
                                'price': data.get('c', 0),
                                'change': data.get('c', 0) - data.get('pc', 0),
                                'change_pct': ((data.get('c', 0) / data.get('pc', 1)) - 1) * 100 if data.get('pc') else 0,
                                'volume': data.get('v', 0),
                                'source': 'finnhub',
                                'timestamp': datetime.now().isoformat()
                            }
        except Exception as e:
            print(f"   Finnhub error for {symbol}: {e}")
        return None
    
    async def fetch_polygon(self, symbol):
        """Fetch from Polygon"""
        if not self.polygon_key or 'your_key' in self.polygon_key:
            return None
            
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
        params = {'apiKey': self.polygon_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get('results', [])
                        if results:
                            r = results[0]
                            return {
                                'symbol': symbol,
                                'price': r.get('c', 0),
                                'change': r.get('c', 0) - r.get('o', 0),
                                'change_pct': ((r.get('c', 0) / r.get('o', 1)) - 1) * 100,
                                'volume': r.get('v', 0),
                                'source': 'polygon',
                                'timestamp': datetime.now().isoformat()
                            }
        except Exception as e:
            print(f"   Polygon error for {symbol}: {e}")
        return None
    
    async def get_stock_data(self, symbol):
        """Try all sources and return first successful"""
        # Try each source in order
        sources = [
            ('Alpha Vantage', self.fetch_alpha_vantage),
            ('Finnhub', self.fetch_finnhub),
            ('Polygon', self.fetch_polygon)
        ]
        
        for name, fetch_func in sources:
            try:
                result = await fetch_func(symbol)
                if result and result['price'] > 0:
                    print(f"   ✓ {symbol}: ${result['price']:.2f} ({result['change']:+.2f}) from {name}")
                    return result
            except Exception as e:
                continue
        
        print(f"   ✗ {symbol}: All sources failed")
        return None

async def run_live_test():
    """Run live data test"""
    print("🚀 PHASMA AI - LIVE DATA TEST")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check available keys
    print("\n🔑 CHECKING API KEYS")
    print("-" * 40)
    
    fetcher = LiveDataFetcher()
    
    has_alpha = fetcher.alpha_vantage_key and 'your_key' not in fetcher.alpha_vantage_key
    has_finnhub = fetcher.finnhub_key and 'your_key' not in fetcher.finnhub_key
    has_polygon = fetcher.polygon_key and 'your_key' not in fetcher.polygon_key
    
    print(f"Alpha Vantage: {'✅' if has_alpha else '❌'}")
    print(f"Finnhub: {'✅' if has_finnhub else '❌'}")
    print(f"Polygon: {'✅' if has_polygon else '❌'}")
    
    if not any([has_alpha, has_finnhub, has_polygon]):
        print("\n⚠️  No live market data APIs configured!")
        print("Add these to your .env file:")
        print("  ALPHA_VANTAGE_KEY=your_key_here")
        print("  FINNHUB_API_KEY=your_key_here")
        print("  POLYGON_API_KEY=your_key_here")
        return
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BTC-USD']
    
    print(f"\n📊 FETCHING LIVE DATA")
    print("-" * 40)
    print(f"Testing {len(symbols)} symbols...\n")
    
    # Fetch all symbols
    results = []
    for symbol in symbols:
        data = await fetcher.get_stock_data(symbol)
        if data:
            results.append(data)
        await asyncio.sleep(0.5)  # Rate limit protection
    
    # Summary
    print(f"\n📈 RESULTS")
    print("=" * 60)
    print(f"Symbols tested: {len(symbols)}")
    print(f"Successful: {len(results)}")
    print(f"Success rate: {len(results)/len(symbols):.1%}")
    
    if results:
        print(f"\nLive Price Data:")
        for r in results:
            change_pct = float(r.get('change_pct', 0))
            emoji = "📈" if change_pct > 0 else "📉"
            print(f"  {emoji} {r['symbol']:8s} ${r['price']:>8.2f} ({change_pct:+.2f}%) [{r['source']}]")
        
        # Save results
        with open('live_data_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to live_data_results.json")
    else:
        print("\n❌ No live data retrieved - check API keys")

if __name__ == "__main__":
    asyncio.run(run_live_test())
