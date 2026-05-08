#!/usr/bin/env python3
"""Test StockTwits social media monitoring"""

import asyncio
from engines.social_engine import StockTwitsClient

async def test_stocktwits():
    print("Testing StockTwits client...")
    
    # Initialize client
    client = StockTwitsClient()
    
    try:
        # Get trending symbols
        print("\nFetching trending symbols...")
        trending = await client.get_trending_symbols(limit=10)
        
        if trending:
            print(f"✅ Found {len(trending)} trending symbols:")
            for symbol, count in trending.items():
                print(f"  - {symbol}: {count} mentions")
        else:
            print("❌ No trending symbols found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_stocktwits())
