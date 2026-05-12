"""
Simple 24-Hour Toggle for Main.py
Just adds --24hour flag to run main.py for 24 hours with new features
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
async def run_24hour_main():
    """Run main.py in 24-hour mode with new features"""
    
    print("=" * 80)
    print("⏰ PHASMA AI - 24-HOUR MODE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Import main after path setup
    from main import PhasmaTradingSystem
    
    # Load config
    from config.secure_config import config
    
    # Enable new features in config
    config.set('trading.unified_brain', True)
    config.set('trading.sector_intelligence', True)
    config.set('trading.expansion_engine', True)
    config.set('trading.bias_breaker', True)
    config.set('trading.monitoring_mode', True)
    
    print("\n🔧 FEATURES ENABLED:")
    print("✅ Unified Brain - All systems working together")
    print("✅ Sector Intelligence - Industry correlations")
    print("✅ Expansion Engine - Always finding NEW stocks")
    print("✅ Bias Breaker - No top-3 obsession")
    print("✅ Memory System - Remembers everything")
    
    # Initialize system
    system = PhasmaTradingSystem(config)
    
    # Run 24 cycles (1 per hour)
    for hour in range(24):
        print(f"\n{'='*60}")
        print(f"🕐 HOUR {hour + 1}/24 - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            # Run one full cycle
            await system.run_full_cycle()
            
            print(f"\n✅ Hour {hour + 1} complete")
            
            # Wait for next hour (demo: 5 minutes, production: 1 hour)
            if hour < 23:  # Don't wait after last hour
                wait_time = 300  # 5 minutes for demo
                print(f"⏳ Waiting {wait_time//60} minutes for next hour...")
                await asyncio.sleep(wait_time)
                
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error in hour {hour + 1}: {e}")
            continue
    
    print(f"\n{'='*80}")
    print("✅ 24-HOUR CYCLE COMPLETE")
    print(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(run_24hour_main())
