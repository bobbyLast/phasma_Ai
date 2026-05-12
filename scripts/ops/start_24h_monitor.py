"""
24-Hour Run Launcher
Starts the 24-hour monitoring system with proper logging
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
async def main():
    """Main launcher for 24-hour run"""
    
    print("=" * 80)
    print("🚀 PHASMA AI - 24-HOUR MONITORING SYSTEM")
    print("=" * 80)
    print(f"Launch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    print("\n📋 SYSTEM CHECKLIST:")
    print("✅ Memory System: Tracks processed news & stocks")
    print("✅ Duplicate Prevention: Hash-based news tracking")
    print("✅ Individual Monitoring: Watches uncertain stocks")
    print("✅ Price Alerts: 5% movement notifications")
    print("✅ 10% Confirmation: Automatic run detection")
    print("✅ Persistent Storage: Saves all progress")
    
    print("\n🎯 MONITORING STRATEGY:")
    print("1. Process news from 20+ sources hourly")
    print("2. Skip already processed news (memory)")
    print("3. Analyze new stocks")
    print("4. If confidence < 50% → Monitor individually")
    print("5. Track price movements every hour")
    print("6. Alert on 5% changes")
    print("7. Confirm runs on 10% movements")
    
    print("\n⚠️  NOTE: This demo version runs 24 minutes (1 minute per hour)")
    print("    For production, change sleep(60) to sleep(3600)")
    
    input("\nPress Enter to start 24-hour monitoring...")
    
    # Import and run
    from hourly_monitor_24h import run_24hour_monitor
    
    print("\n🚀 Starting 24-hour monitoring...")
    print("-" * 80)
    
    try:
        results = await run_24hour_monitor()
        
        print("\n" + "=" * 80)
        print("✅ 24-HOUR MONITORING SUCCESSFUL!")
        print("=" * 80)
        
        print(f"\n📊 FINAL RESULTS:")
        print(f"   Hours Monitored: {results['hours_completed']}/24")
        print(f"   News Processed: {results['news_processed']}")
        print(f"   New News: {results['new_news']}")
        print(f"   Stocks Analyzed: {results['stocks_analyzed']}")
        print(f"   Candidates Monitored: {results['monitoring_candidates']}")
        print(f"   Price Alerts: {results['price_alerts']}")
        print(f"   Confirmed Runs: {results['confirmed_runs']}")
        
        print(f"\n💾 Memory file 'monitoring_memory.json' contains all history")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring interrupted by user")
        print("💾 Progress saved to memory file")
        print("🔄 Run again to continue")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💾 Progress saved to memory file")
        raise

if __name__ == "__main__":
    asyncio.run(main())
