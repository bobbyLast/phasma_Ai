"""
Debug script to check what our integrated sources are returning
"""

import asyncio
import sys
import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
async def debug_news_sources():
    """Debug what news sources are returning"""
    
    print("=" * 80)
    print("DEBUGGING NEWS SOURCES")
    print("=" * 80)
    
    # Load config
    from config.secure_config import config
    
    # Initialize news engine
    from engines.news_engine_core import NewsAPIIntegration
    news_engine = NewsAPIIntegration(config)
    
    # Get integrated sources
    print("\n[DEBUG] Fetching from integrated sources...")
    integrated_news = await news_engine.integrated_sources.fetch_all_integrated_sources()
    
    print(f"\n[DEBUG] Total items from integrated sources: {len(integrated_news)}")
    
    # Show first 10 items
    print("\n[DEBUG] First 10 items:")
    for i, item in enumerate(integrated_news[:10]):
        print(f"\n{i+1}. {item.get('title', 'NO TITLE')[:80]}...")
        print(f"   Source: {item.get('source', 'NO SOURCE')}")
        print(f"   Symbol: {item.get('symbol', 'NO SYMBOL')}")
        print(f"   Sentiment: {item.get('sentiment', 'NO SENTIMENT')}")
    
    # Count items with symbols
    with_symbols = [item for item in integrated_news if item.get('symbol')]
    print(f"\n[DEBUG] Items with symbols: {len(with_symbols)}")
    
    # Show unique symbols
    unique_symbols = set(item.get('symbol') for item in with_symbols if item.get('symbol'))
    print(f"[DEBUG] Unique symbols found: {list(unique_symbols)[:10]}")
    
    # Now test the full scan
    print("\n" + "=" * 80)
    print("TESTING FULL SCAN")
    print("=" * 80)
    
    all_news = await news_engine.scan_all_sources()
    print(f"\n[DEBUG] Total items from full scan: {len(all_news)}")
    
    # Check first 20 items (what the system uses)
    print("\n[DEBUG] First 20 items (what system processes):")
    for i, item in enumerate(all_news[:20]):
        if item.get('symbol'):
            print(f"{i+1}. {item.get('symbol')}: {item.get('title', '')[:60]}...")

if __name__ == "__main__":
    asyncio.run(debug_news_sources())
