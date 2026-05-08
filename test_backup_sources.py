"""Test the performance of backup data sources"""

import asyncio
import sys
sys.path.append('.')
from main import PhasmaTradingSystem

async def test_performance():
    print('🚀 TESTING PHASMA AI WITH BACKUP DATA SOURCES')
    print('=' * 60)
    
    system = PhasmaTradingSystem()
    
    # Check if enhanced options detector is loaded
    has_enhanced = hasattr(system, 'enhanced_options_detector')
    print(f'✅ Enhanced Options Detector: {"Loaded" if has_enhanced else "Not Found"}')
    
    # Check symbol provider
    if system.symbol_provider:
        print(f'✅ Symbol Provider: {system.symbol_provider.get_total_symbol_count()} symbols available')
    else:
        print('⚠️ Symbol Provider: Not loaded')
    
    print('\n=== RUNNING TRADING CYCLE ===\n')
    await system.run_full_cycle()
    
    print('\n=== PERFORMANCE SUMMARY ===')
    
if __name__ == "__main__":
    asyncio.run(test_performance())
