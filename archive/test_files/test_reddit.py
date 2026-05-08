#!/usr/bin/env python3
"""Test Reddit social media monitoring"""

import os
import asyncio
from dotenv import load_dotenv
from engines.social_engine import RedditTrendingTracker

async def test_reddit():
    # Load environment variables
    load_dotenv()
    
    print("Testing Reddit client...")
    print(f"REDDIT_CLIENT_ID: {os.getenv('REDDIT_CLIENT_ID')[:10]}..." if os.getenv('REDDIT_CLIENT_ID') else "Not found")
    print(f"REDDIT_SECRET: {os.getenv('REDDIT_SECRET')[:10]}..." if os.getenv('REDDIT_SECRET') else "Not found")
    print(f"REDDIT_USER_AGENT: {os.getenv('REDDIT_USER_AGENT')}")
    
    # Initialize client
    client = RedditTrendingTracker()
    
    try:
        # Get trending symbols
        print("\nFetching trending symbols...")
        trending = await client.get_trending_symbols(limit=5)
        
        if trending:
            print(f"Found {len(trending)} trending symbols:")
            for symbol, count in trending.items():
                print(f"  - {symbol}: {count} mentions")
        else:
            print("No trending symbols found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if hasattr(client, 'close'):
            await client.close()

if __name__ == "__main__":
    asyncio.run(test_reddit())
