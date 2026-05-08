#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Engine Test - No Unicode Characters
Tests core functionality of integrated engines
"""

import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pump_dump_detector():
    """Test pump/dump detector"""
    print("\nTesting Pump/Dump Detector...")
    try:
        from engines.pump_dump_detector import PumpDumpDetector
        
        config = {'pump_dump': {'volume_surge_threshold': 3.0}}
        detector = PumpDumpDetector(config)
        
        result = detector.analyze_stock('TEST', 2.0, 1000)
        
        assert 'pump_detected' in result
        assert 'pump_strength' in result
        
        print("  PASS: Pump detector working")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_global_macro_monitor():
    """Test global macro monitor"""
    print("\nTesting Global Macro Monitor...")
    try:
        from engines.global_macro_monitor import GlobalMacroMonitor
        
        monitor = GlobalMacroMonitor()
        analysis = monitor._analyze_macro_situation({})
        
        assert 'risk_level' in analysis
        
        print("  PASS: Macro monitor working")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_insider_signal_integrator():
    """Test insider signal integrator"""
    print("\nTesting Insider Signal Integrator...")
    try:
        from engines.insider_signal_integrator import InsiderSignalIntegrator
        
        integrator = InsiderSignalIntegrator()
        
        print("  PASS: Insider integrator initialized")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_market_crash_detector():
    """Test market crash detector"""
    print("\nTesting Market Crash Detector V2...")
    try:
        from engines.market_crash_detector_v2 import MarketCrashDetectorV2
        
        detector = MarketCrashDetectorV2()
        alert = detector.detect_crash_risk()
        
        assert isinstance(alert, dict)
        
        print("  PASS: Crash detector working")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_news_engines():
    """Test news engines"""
    print("\nTesting News Engines...")
    results = []
    
    # Test news collection
    try:
        from engines.news_collection_network import NewsCollectionNetwork
        network = NewsCollectionNetwork()
        print("  PASS: News network initialized")
        results.append(True)
    except Exception as e:
        print(f"  FAIL News network: {e}")
        results.append(False)
    
    # Test news scanner
    try:
        from engines.investment_news_scanner import InvestmentNewsScanner
        scanner = InvestmentNewsScanner()
        print("  PASS: News scanner initialized")
        results.append(True)
    except Exception as e:
        print(f"  FAIL News scanner: {e}")
        results.append(False)
    
    return all(results)

def test_other_engines():
    """Test other integrated engines"""
    print("\nTesting Other Engines...")
    
    engines = [
        ('kalshi_engine', 'KalshiPredictionEngine'),
        ('day_trading_scanner', 'DayTradingScanner'),
        ('market_intelligence_engine', 'MarketIntelligenceEngine'),
        ('signal_convergence_engine', 'SignalConvergenceEngine'),
        ('thematic_analysis_engine', 'ThematicAnalyzer'),
        ('options_engine', 'PhasmaOptionsEngine')
    ]
    
    results = []
    
    for module_name, class_name in engines:
        try:
            module = __import__(f'engines.{module_name}', fromlist=[class_name])
            engine_class = getattr(module, class_name)
            
            # Try to initialize
            try:
                instance = engine_class({})
            except:
                try:
                    instance = engine_class()
                except:
                    instance = engine_class(config={})
            
            print(f"  PASS: {module_name}")
            results.append(True)
        except Exception as e:
            print(f"  FAIL {module_name}: {str(e)[:50]}...")
            results.append(False)
    
    return results

def main():
    """Run all tests"""
    print("=" * 60)
    print("SIMPLE ENGINE FUNCTIONALITY TEST")
    print("=" * 60)
    
    tests = [
        test_pump_dump_detector,
        test_global_macro_monitor,
        test_insider_signal_integrator,
        test_market_crash_detector,
        test_news_engines
    ]
    
    # Run individual tests
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    # Test other engines
    other_results = test_other_engines()
    passed += sum(other_results)
    
    total = len(tests) + len(other_results)
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"  Total engines: {total}")
    print(f"  Working: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\nALL ENGINES WORKING!")
    else:
        print(f"\n{total - passed} engines need attention")

if __name__ == "__main__":
    main()
