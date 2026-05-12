#!/usr/bin/env python3
"""
Run Phasma AI with ALL News Sources
- Uses all 58 RSS feeds
- Uses your API keys (Finnhub, Alpha Vantage, etc.)
- Activates moonshot detection
- Scans crypto + stocks
"""

import asyncio
import os
from main import PhasmaTradingSystem

async def main():
    print("=" * 70)
    print("🚀 PHASMA AI - FULL POWER MODE")
    print("=" * 70)
    
    # Check API keys
    print("\n🔑 CHECKING API KEYS:")
    api_keys = {
        'Telegram Bot': os.getenv('TELEGRAM_BOT_TOKEN'),
        'Finnhub': os.getenv('FINNHUB_API_KEY'),
        'Alpha Vantage': os.getenv('ALPHA_VANTAGE_KEY'),
        'FMP': os.getenv('FMP_API_KEY'),
    }
    
    for name, key in api_keys.items():
        if key and key != 'your_key_here':
            print(f"   ✅ {name}: Configured")
        else:
            print(f"   ⚠️  {name}: Not configured")
    
    # Initialize system
    print("\n📊 INITIALIZING PHASMA AI...")
    system = PhasmaTradingSystem()
    
    # Show configuration
    print("\n⚙️  CONFIGURATION:")
    print(f"   Min IV: {system.config.get('trading.min_implied_volatility')}%")
    print(f"   Min Volume: {system.config.get('trading.min_options_volume')}")
    print(f"   Auto-start RSS: {system.config.get('news.auto_start_news_collection')}")
    
    # Start 24/7 news collection
    print("\n📰 STARTING 24/7 NEWS COLLECTION...")
    print("   This will activate all 58 RSS feeds")
    
    success = await system.start_news_collection()
    
    if success:
        print("\n✅ NEWS COLLECTION ACTIVE!")
        print("   📡 58 RSS feeds monitoring:")
        print("      - 16 Financial (Reuters, CNBC, Bloomberg, etc.)")
        print("      - 9 Tech/AI (TechCrunch, Wired, VentureBeat)")
        print("      - 5 Crypto (CoinTelegraph, CoinDesk, Bitcoin Magazine)")
        print("      - 4 Biotech (FierceBiotech, FiercePharma)")
        print("      - 4 Energy (OilPrice, Rigzone)")
        print("      - 5 Social (Reddit WSB, r/stocks, r/investing)")
        print("      - Plus business, economic, and news wires")
        
        # Wait for initial fetch
        print("\n⏳ Waiting 90 seconds for first news batch...")
        await asyncio.sleep(90)
        
        # Show stats
        print("\n📊 NEWS COLLECTION STATS:")
        system.get_news_memory_stats()
        
    else:
        print("\n⚠️  News collection not started - using basic 2 sources")
    
    # Run trading cycle
    print("\n" + "=" * 70)
    print("🔄 RUNNING TRADING CYCLE WITH ALL SOURCES")
    print("=" * 70)
    
    signals = await system.run_full_cycle()
    
    # Show results
    print("\n" + "=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    
    if signals:
        print(f"\n✅ FOUND {len(signals)} TRADING SIGNALS!")
        
        moonshot_count = 0
        for i, signal in enumerate(signals[:10], 1):  # Show first 10
            print(f"\n{i}. {signal.get('symbol')} - {signal.get('title', '')[:60]}")
            print(f"   Industry: {signal.get('industry', 'Unknown')}")
            print(f"   Recommendation: {signal.get('options_recommendation', 'UNKNOWN')}")
            
            # Check moonshot
            moonshot = signal.get('moonshot_analysis', {})
            if moonshot.get('is_moonshot'):
                moonshot_count += 1
                print(f"   🚀 MOONSHOT! Score: {moonshot.get('score')}/100")
                print(f"   Potential: {moonshot.get('potential_move')}")
                keywords = [kw['keyword'] for kw in moonshot.get('keywords_found', [])]
                print(f"   Keywords: {keywords}")
        
        if moonshot_count > 0:
            print(f"\n🚀 Found {moonshot_count} MOONSHOT opportunities!")
    
    else:
        print("\n💤 NO SIGNALS FOUND THIS CYCLE")
        print("\n   This could mean:")
        print("   1. No major catalysts in current news")
        print("   2. All opportunities filtered out by criteria")
        print("   3. After market hours (less activity)")
        
        print("\n   💡 TIP: Keep the news collection running")
        print("   Run this script again in 5-10 minutes to check for new opportunities")
    
    print("\n" + "=" * 70)
    print("✅ CYCLE COMPLETE")
    print("=" * 70)
    
    # Keep running option
    print("\n🔄 OPTIONS:")
    print("   1. Press Ctrl+C to stop")
    print("   2. Let it run - news collection continues in background")
    print("   3. Run 'python main.py' anytime to check for new signals")
    
    try:
        print("\n⏸️  Keeping news collection active for 5 minutes...")
        print("   (You can stop anytime with Ctrl+C)")
        await asyncio.sleep(300)
        
        # Check again after 5 minutes
        print("\n🔄 Running another cycle...")
        signals = await system.run_full_cycle()
        print(f"📊 Found {len(signals)} signals this time")
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Stopping...")
    
    # Cleanup
    await system.stop_news_collection()
    print("\n✅ News collection stopped")
    print("🎯 Run this script again anytime to restart!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted by user")
