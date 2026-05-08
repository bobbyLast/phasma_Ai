#!/usr/bin/env python3
"""
Test the parallel data fetcher performance
"""

import asyncio
import time
import os

async def test_parallel_fetcher():
    """Test the parallel data fetcher"""
    print("🚀 Testing Parallel Data Fetcher")
    print("=" * 50)
    
    # Import the fetcher
    from utils.parallel_data_fetcher import ParallelDataFetcher
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    
    start_time = time.time()
    
    async with ParallelDataFetcher() as fetcher:
        print(f"Fetching data for {len(symbols)} symbols...")
        data = await fetcher.fetch_all_data(symbols)
        
        elapsed = time.time() - start_time
        
        print(f"\n✅ Completed in {elapsed:.2f} seconds")
        print("\nData Summary:")
        
        for key, value in data.items():
            if value is not None:
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items")
                elif isinstance(value, dict):
                    if 'latest' in value:
                        print(f"  {key}: Macro data available")
                    else:
                        print(f"  {key}: {len(value)} fields")
                else:
                    print(f"  {key}: {type(value).__name__}")
            else:
                print(f"  {key}: ❌ Failed")
        
        # Test market regime
        macro_data = data.get('fred_macro', {})
        if macro_data:
            regime = fetcher.get_market_regime_from_macro(macro_data)
            print(f"\n📊 Market Regime: {regime}")
        
        # Show speed improvement
        if elapsed < 60:
            print(f"\n🎯 Target achieved! Under 60 seconds ({elapsed:.2f}s)")
        else:
            print(f"\n⚠️  Above target of 60 seconds ({elapsed:.2f}s)")

if __name__ == "__main__":
    asyncio.run(test_parallel_fetcher())
