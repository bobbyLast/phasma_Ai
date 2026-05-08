#!/usr/bin/env python3
"""
Test the main system with error handling
"""

import asyncio
import sys
sys.path.append('.')

from main import PhasmaTradingSystem

async def test_main():
    """Test the main system"""
    
    print("🚀 Starting Phasma AI Trading System...")
    
    try:
        # Initialize system
        system = PhasmaTradingSystem()
        print("✅ System initialized")
        
        # Run one cycle
        print("\n🔄 Running analysis cycle...")
        results = await system.run_full_cycle()
        print("✅ Cycle completed")
        
        # Show results
        print(f"\n📊 Results:")
        print(f"   Total opportunities: {len(results) if isinstance(results, list) else 'N/A'}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean shutdown
        try:
            if 'system' in locals():
                await system.shutdown()
                print("✅ System shutdown")
        except Exception as e:
            print(f"⚠️ Shutdown error: {e}")

if __name__ == "__main__":
    asyncio.run(test_main())
