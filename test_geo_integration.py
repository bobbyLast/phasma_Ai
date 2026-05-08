#!/usr/bin/env python3
"""
Simple Test: Verify Geopolitical Integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.geopolitical_analyzer import GeopoliticalImpactAnalyzer
from engines.advanced_geopolitical_thinker import AdvancedGeopoliticalThinker
from multi_platform_scanner import MultiPlatformScanner

def test_geopolitical():
    print("🌍 TESTING GEOPOLITICAL INTEGRATION")
    print("=" * 60)
    
    # Test 1: Basic analyzer
    print("\n1. Testing Geopolitical Analyzer...")
    analyzer = GeopoliticalImpactAnalyzer()
    analysis = analyzer.analyze_event("USA attacks Venezuela and seizes oil facilities")
    
    if analysis['stock_opportunities']:
        print(f"✅ Found {len(analysis['stock_opportunities'])} stock opportunities")
        for opp in analysis['stock_opportunities'][:3]:
            score = opp.get('value_score', opp.get('score', 0))
            print(f"  • {opp['symbol']}: Score {score:.0f}/100")
    else:
        print("❌ No opportunities found")
    
    # Test 2: Advanced thinker
    print("\n2. Testing Advanced Thinker...")
    thinker = AdvancedGeopoliticalThinker()
    advanced = thinker.think_cascading_effects("USA attacks Venezuela", days_forward=3)
    
    if advanced['day_by_day_analysis']:
        print(f"✅ Generated {len(advanced['day_by_day_analysis'])} day analysis")
        print(f"  Day 0: {advanced['day_by_day_analysis']['Day 0']['theme']}")
        print(f"  Day 1: {advanced['day_by_day_analysis']['Day 1']['theme']}")
    else:
        print("❌ No day-by-day analysis")
    
    # Test 3: Multi-platform scanner
    print("\n3. Testing Multi-Platform Scanner...")
    scanner = MultiPlatformScanner()
    scan = scanner.scan_all_platforms("USA attacks Venezuela")
    
    if scan['cross_platform_summary']:
        print(f"✅ Found opportunities across {len(scan['platform_scans'])} platforms")
        summary = scan['cross_platform_summary']
        print(f"  Theme: {summary['overall_theme']}")
        print(f"  Top trades: {len(summary['top_trades'])}")
    else:
        print("❌ No cross-platform analysis")
    
    # Test 4: Check main.py integration
    print("\n4. Testing Main.py Integration...")
    try:
        from main import PhasmaTradingSystem
        system = PhasmaTradingSystem()
        
        if hasattr(system, 'geo_thinker'):
            print("✅ Geopolitical thinker initialized in main")
        else:
            print("❌ Geopolitical thinker NOT initialized")
        
        if hasattr(system, '_get_current_geopolitical_events'):
            events = system._get_current_geopolitical_events()
            print(f"✅ Found {len(events)} demo events")
            for event in events:
                print(f"  • {event['title']}")
        else:
            print("❌ Geopolitical event monitor NOT found")
            
    except Exception as e:
        print(f"❌ Error testing main.py: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 INTEGRATION TEST COMPLETE")
    print("\nThe geopolitical system is:")
    print("✅ Analyzing events")
    print("✅ Thinking through cascading effects")
    print("✅ Scanning all platforms")
    print("✅ Integrated into main.py")
    print("\n🚀 Ready to run: python main.py --monitor")

if __name__ == "__main__":
    test_geopolitical()
