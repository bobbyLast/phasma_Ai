#!/usr/bin/env python3
"""Test full system integration with all signal sources working together"""

from main import PhasmaTradingSystem
from core.config import PhasmaConfig
import sys

def main():
    print("=== Full System Integration Test ===\n")
    
    # Initialize the system
    print("1. Initializing PhasmaTradingSystem...")
    engine = PhasmaTradingSystem('config.json')
    
    # Check all components are loaded
    print("\n2. Checking component initialization...")
    components = {
        "News Engine": hasattr(engine, 'news_engine') and engine.news_engine is not None,
        "Volatility Detector": hasattr(engine, 'vol_burst_detector') and engine.vol_burst_detector is not None,
        "Weekly Watchlist": hasattr(engine, 'weekend_watchlist') and engine.weekend_watchlist is not None,
        "Winners Gallery": hasattr(engine, 'winners_gallery') and engine.winners_gallery is not None,
        "Insider Monitor": hasattr(engine, 'insider_monitor') and engine.insider_monitor is not None,
        "Convergence Engine": hasattr(engine, 'convergence_engine') and engine.convergence_engine is not None,
    }
    
    for comp, status in components.items():
        status_str = "✅" if status else "❌"
        print(f"   {status_str} {comp}")
    
    # Test insider signal format
    print("\n3. Testing insider signal format...")
    if engine.insider_monitor:
        try:
            signals = engine.insider_monitor.get_recent_signals()
            print(f"   Insider signals returned: {len(signals)}")
            
            if signals:
                # Check signal format
                required_keys = ['ticker', 'score', 'source', 'confidence', 'action']
                signal = signals[0]
                missing_keys = [k for k in required_keys if k not in signal]
                
                if missing_keys:
                    print(f"   ❌ Missing signal keys: {missing_keys}")
                else:
                    print("   ✅ Signal format is correct")
                    print(f"   Sample: {signal['ticker']} - Score: {signal['score']}")
            else:
                print("   ℹ No insider signals (normal with high filters)")
        except Exception as e:
            print(f"   ❌ Error getting signals: {e}")
    
    # Test convergence analysis
    print("\n4. Testing convergence analysis...")
    try:
        # Run a quick convergence check
        convergence_results = engine.run_convergence_analysis()
        
        print(f"   Convergence analysis completed")
        print(f"   Total signals processed: {len(convergence_results.get('all_signals', []))}")
        print(f"   Top opportunities: {len(convergence_results.get('top_opportunities', []))}")
        
        # Check signal sources
        signal_sources = set()
        for signal in convergence_results.get('all_signals', []):
            signal_sources.add(signal.get('source', 'unknown'))
        
        print(f"   Signal sources: {', '.join(sorted(signal_sources))}")
        
        if 'insider_trading' in signal_sources:
            print("   ✅ Insider signals integrated into convergence")
        else:
            print("   ℹ No insider signals in current analysis")
            
    except Exception as e:
        print(f"   ❌ Error in convergence analysis: {e}")
        import traceback
        traceback.print_exc()
    
    # Check for conflicts
    print("\n5. Checking for module conflicts...")
    try:
        # Verify we're using the right insider module
        from utils.insider_opportunity_analyzer import InsiderOpportunityAnalyzer
        print("   ✅ Using InsiderOpportunityAnalyzer (correct module)")
        
        # Check if old module is still importable
        try:
            from utils.insider_monitor import InsiderMonitor
            print("   ⚠️ Warning: Old InsiderMonitor module is still importable")
        except ImportError:
            print("   ✅ Old InsiderMonitor module not found (good)")
            
    except Exception as e:
        print(f"   ❌ Module check error: {e}")
    
    print("\n=== Integration Test Complete ===")
    
    # Summary
    all_good = all(components.values())
    if all_good:
        print("✅ All components initialized successfully")
        print("✅ System is ready for trading")
    else:
        print("❌ Some components failed to initialize")
        print("   Check the logs above for details")

if __name__ == "__main__":
    main()
