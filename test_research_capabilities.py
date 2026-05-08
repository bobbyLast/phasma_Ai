#!/usr/bin/env python3
"""
Test script to demonstrate the new comprehensive research capabilities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.market_crash_detector_v2 import MarketCrashDetectorV2
from utils.market_data_cache import MarketDataCache

def test_bitcoin_research():
    """Test comprehensive research on Bitcoin"""
    print("="*70)
    print("TESTING COMPREHENSIVE RESEARCH - BITCOIN")
    print("="*70)
    
    # Initialize components
    config = {}
    market_cache = MarketDataCache()
    
    # Initialize crash detector with research engines
    crash_detector = MarketCrashDetectorV2(config=config, market_cache=market_cache)
    
    # Generate comprehensive research report
    print("\nGenerating comprehensive research for Bitcoin...")
    report = crash_detector.generate_comprehensive_research('BTC-USD', 'CRYPTO')
    
    print("\n✅ Bitcoin research complete!")
    print(f"Overall Signal: {report['synthesis']['overall_signal']}")
    print(f"Risk Level: {report['synthesis']['risk_level']}")
    print(f"Opportunity Level: {report['synthesis']['opportunity_level']}")
    
    return report

def test_stock_research():
    """Test comprehensive research on a stock"""
    print("\n" + "="*70)
    print("TESTING COMPREHENSIVE RESEARCH - APPLE (AAPL)")
    print("="*70)
    
    # Initialize components
    config = {}
    market_cache = MarketDataCache()
    
    # Initialize crash detector with research engines
    crash_detector = MarketCrashDetectorV2(config=config, market_cache=market_cache)
    
    # Generate comprehensive research report
    print("\nGenerating comprehensive research for Apple...")
    report = crash_detector.generate_comprehensive_research('AAPL', 'STOCK')
    
    print("\n✅ Apple research complete!")
    print(f"Overall Signal: {report['synthesis']['overall_signal']}")
    print(f"Risk Level: {report['synthesis']['risk_level']}")
    print(f"Opportunity Level: {report['synthesis']['opportunity_level']}")
    
    return report

def test_crash_detection():
    """Test enhanced crash detection"""
    print("\n" + "="*70)
    print("TESTING ENHANCED CRASH DETECTION")
    print("="*70)
    
    # Initialize components
    config = {}
    market_cache = MarketDataCache()
    
    # Initialize crash detector
    crash_detector = MarketCrashDetectorV2(config=config, market_cache=market_cache)
    
    # Test crash risk assessment
    print("\nAssessing crash risk for Bitcoin...")
    assessment = crash_detector.detect_crash_risk('BTC-USD')
    
    print(f"\nCrash Score: {assessment.get('crash_score', 0):.1%}")
    print(f"Alert Level: {assessment.get('alert_level', 0)}/3")
    print(f"Crash Probability: {assessment.get('crash_probability', 0):.1%}")
    
    # Check component scores
    components = assessment.get('component_scores', {})
    if components:
        print("\nComponent Scores:")
        for component, score in components.items():
            print(f"  {component}: {score:.1%}")
    
    return assessment

def main():
    """Run all tests"""
    print("\n🚀 TESTING PHASMA AI RESEARCH CAPABILITIES")
    print("="*70)
    
    try:
        # Test Bitcoin research
        btc_report = test_bitcoin_research()
        
        # Test stock research
        aapl_report = test_stock_research()
        
        # Test crash detection
        crash_assessment = test_crash_detection()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nThe system now provides:")
        print("• Deep fundamental analysis for any asset")
        print("• Real-time sentiment tracking (Fear & Greed, VIX)")
        print("• Whale activity monitoring")
        print("• Catalyst identification and tracking")
        print("• Historical pattern matching")
        print("• Comprehensive risk assessment")
        print("• Actionable trading plans")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
