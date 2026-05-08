#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, r'c:\Users\kyran\CascadeProjects\phasma_Ai')

from core.meta_brain import PhasmaConfig
from engines.news_engine_core import NewsAPIIntegration

async def verify_system():
    print('🔍 VERIFYING: Real Trades vs Simulation')
    print('=' * 50)

    config = PhasmaConfig()
    news_engine = NewsAPIIntegration(config)

    print(f'📊 Company database: {len(news_engine.company_db)} real companies')
    print(f'🎯 Tracking: {list(news_engine.company_db.keys())[:5]}...')

    # Test real news scanning
    print('\n📡 Testing Real News Scanning...')
    news_items = await news_engine.scan_all_sources()

    print(f'📊 Found {len(news_items)} news items')

    if news_items:
        print('\n📰 SAMPLE NEWS ITEMS:')
        for item in news_items[:3]:
            fact_check = item.get('fact_check', {})
            company_info = fact_check.get('company_info', {})

            print(f'   📈 {item.get("symbol", "UNKNOWN")}: {item.get("title", "No title")[:50]}...')
            print(f'      🏢 Company: {company_info.get("full_name", "Unknown")}')
            print(f'      ✅ Real Company: {fact_check.get("is_valid", False)}')
            print(f'      📊 Volume: {company_info.get("avg_volume", "N/A")} | Price: {company_info.get("price_range", "N/A")}')
            print(f'      🎯 Sentiment: {item.get("sentiment", 0):.2f} | Catalyst: {item.get("catalyst_score", 0):.2f}')
            print(f'      📍 Source: {item.get("source", "unknown")}')
            print()

    # Check if fallback was used
    fallback_used = any(item.get('source') == 'fallback_news' for item in news_items)
    real_api_used = any(item.get('source') != 'fallback_news' for item in news_items)

    print('📋 SYSTEM STATUS:')
    print(f'   🔄 Real APIs used: {real_api_used}')
    print(f'   📈 Fallback used: {fallback_used}')
    print(f'   ✅ Real companies validated: {sum(1 for item in news_items if item.get("fact_check", {}).get("is_valid", False))}')

    if real_api_used:
        print('\n🎯 SYSTEM IS USING REAL DATA!')
    elif fallback_used:
        print('\n📊 SYSTEM USING FALLBACK DATA (still based on real companies)')
    else:
        print('\n❌ No data sources working')

if __name__ == "__main__":
    asyncio.run(verify_system())
