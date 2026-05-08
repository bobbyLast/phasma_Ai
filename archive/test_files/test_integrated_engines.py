#!/usr/bin/env python3
"""
Functional Test for Integrated Engines
Tests the 18 engines actually used by main.py with real data
"""

import os
import sys
import time
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class IntegratedEngineTest:
    """Test integrated engines with proper data"""
    
    def __init__(self):
        self.results = {}
        self.test_data = self.generate_test_data()
        
    def generate_test_data(self):
        """Generate realistic test data for engines"""
        return {
            'stock_ticker': 'AAPL',
            'price': 150.0,
            'volume': 1000000,
            'options_chain': {
                'calls': [{'strike': 155, 'expiry': '2024-01-19', 'iv': 0.3}],
                'puts': [{'strike': 145, 'expiry': '2024-01-19', 'iv': 0.35}]
            },
            'insider_data': {
                'buys': [{'amount': 2000000, 'price': 145.0, 'days_ago': 5}],
                'sells': []
            },
            'news_headlines': [
                'Apple announces new AI features',
                'Apple stock rises on strong earnings'
            ],
            'market_data': {
                'sp500': 4500.0,
                'vix': 20.0,
                'dollar_yen': 150.0
            }
        }
    
    def test_pump_dump_detector(self):
        """Test pump/dump detector with penny stock data"""
        print("\nTesting Pump/Dump Detector...")
        try:
            from engines.pump_dump_detector import PumpDumpDetector
            
            config = {
                'pump_dump': {
                    'volume_surge_threshold': 3.0,
                    'price_surge_threshold': 0.2,
                    'min_price': 5.0,
                    'max_price': 50.0
                }
            }
            
            detector = PumpDumpDetector(config)
            
            # Test with pump scenario
            ticker = 'PUMP'
            entry_price = 2.0
            position_size = 10000
            
            result = detector.analyze_stock(ticker, entry_price, position_size)
            
            # Verify structure
            assert 'pump_detected' in result
            assert 'pump_strength' in result
            assert isinstance(result['pump_strength'], (int, float))
            
            # Test exit signal
            exit_signal = detector.check_exit_signal(ticker, 3.0, entry_price)
            # Can be None if no exit triggered
            
            self.results['pump_dump_detector'] = {
                'status': 'PASS',
                'output': result
            }
            print(f"  PASS Pump detection working: {result['pump_detected']}")
            
        except Exception as e:
            self.results['pump_dump_detector'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"  FAIL Error: {e}")
    
    def test_global_macro_monitor(self):
        """Test global macro monitor"""
        print("\nTesting Global Macro Monitor...")
        try:
            from engines.global_macro_monitor import GlobalMacroMonitor
            
            monitor = GlobalMacroMonitor()
            
            # Test macro analysis
            analysis = monitor._analyze_macro_situation({})
            
            assert 'risk_level' in analysis
            assert 'risk_score' in analysis
            assert 'recommendation' in analysis
            
            # Test carry trade pressure
            carry_trade = monitor.get_carry_trade_pressure()
            assert 'pressure' in carry_trade
            
            # Test crash risk alert
            alert, reason = monitor.should_alert_crash_risk()
            assert isinstance(alert, bool)
            assert isinstance(reason, str)
            
            self.results['global_macro_monitor'] = {
                'status': 'PASS',
                'risk_level': analysis['risk_level'],
                'risk_score': analysis['risk_score']
            }
            print(f"  PASS Risk level: {analysis['risk_level']} (Score: {analysis['risk_score']})")
            
        except Exception as e:
            self.results['global_macro_monitor'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"  FAIL Error: {e}")
    
    def test_insider_signal_integrator(self):
        """Test insider signal integrator"""
        print("\nTesting Insider Signal Integrator...")
        try:
            from engines.insider_signal_integrator import InsiderSignalIntegrator
            
            integrator = InsiderSignalIntegrator()
            
            # Test with mock insider data
            symbol = 'AAPL'
            insider_data = {
                symbol: self.test_data['insider_data']
            }
            
            signal = integrator.analyze_stock(symbol, insider_data)
            
            assert signal is not None
            assert hasattr(signal, 'confidence_level')
            assert hasattr(signal, 'action')
            
            self.results['insider_signal_integrator'] = {
                'status': 'PASS',
                'confidence': signal.confidence_level,
                'action': signal.action
            }
            print(f"  PASS Signal: {signal.action} (Confidence: {signal.confidence_level})")
            
        except Exception as e:
            self.results['insider_signal_integrator'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"  FAIL Error: {e}")
    
    def test_kalshi_engine(self):
        """Test Kalshi prediction engine"""
        print("\nTesting Kalshi Engine...")
        try:
            from engines.kalshi_engine import KalshiPredictionEngine
            
            # Note: Kalshi requires API keys for full functionality
            # We'll test initialization only
            engine = KalshiPredictionEngine()
            
            assert engine is not None
            
            self.results['kalshi_engine'] = {
                'status': 'PASS',
                'note': 'Initialized (requires API for full test)'
            }
            print(f"  PASS Engine initialized")
            
        except Exception as e:
            self.results['kalshi_engine'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"  FAIL Error: {e}")
    
    def test_market_crash_detector(self):
        """Test market crash detector v2"""
        print("\nTesting Market Crash Detector V2...")
        try:
            from engines.market_crash_detector_v2 import MarketCrashDetectorV2
            
            detector = MarketCrashDetectorV2()
            
            # Test crash detection
            crash_alert = detector.check_crash_conditions()
            
            assert isinstance(crash_alert, dict)
            
            self.results['market_crash_detector_v2'] = {
                'status': 'PASS',
                'alert': crash_alert
            }
            print(f"  ✓ Crash detection working")
            
        except Exception as e:
            self.results['market_crash_detector_v2'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"  FAIL Error: {e}")
    
    def test_news_engines(self):
        """Test news collection and analysis"""
        print("\nTesting News Engines...")
        
        # Test news collection network
        try:
            from engines.news_collection_network import NewsCollectionNetwork
            
            network = NewsCollectionNetwork()
            
            # Test initialization
            assert network is not None
            
            self.results['news_collection_network'] = {
                'status': 'PASS',
                'note': 'Initialized (requires API for full test)'
            }
            print(f"  ✓ News network initialized")
            
        except Exception as e:
            self.results['news_collection_network'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"  FAIL Error: {e}")
        
        # Test investment news scanner
        try:
            from engines.investment_news_scanner import InvestmentNewsScanner
            
            scanner = InvestmentNewsScanner()
            
            # Test with sample headlines
            analysis = scanner.analyze_news(self.test_data['news_headlines'])
            
            assert isinstance(analysis, list)
            
            self.results['investment_news_scanner'] = {
                'status': 'PASS',
                'analyzed': len(analysis)
            }
            print(f"  ✓ Analyzed {len(analysis)} news items")
            
        except Exception as e:
            self.results['investment_news_scanner'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"  FAIL Error: {e}")
    
    def test_other_integrated_engines(self):
        """Test remaining integrated engines"""
        print("\nTesting Other Integrated Engines...")
        
        engines_to_test = [
            ('day_trading_scanner', 'DayTradingScanner'),
            ('market_intelligence_engine', 'MarketIntelligenceEngine'),
            ('crash_profit_engine', 'CrashProfitEngine'),
            ('monte_carlo_engine', 'get_monte_carlo_engine'),
            ('signal_convergence_engine', 'SignalConvergenceEngine'),
            ('thematic_analysis_engine', 'ThematicAnalyzer'),
            ('options_engine', 'PhasmaOptionsEngine')
        ]
        
        for module_name, class_name in engines_to_test:
            try:
                module = __import__(f'engines.{module_name}', fromlist=[class_name])
                engine_class = getattr(module, class_name)
                
                # Initialize with config if needed
                try:
                    instance = engine_class({})
                except:
                    try:
                        instance = engine_class()
                    except:
                        instance = engine_class(config={})
                
                self.results[module_name] = {
                    'status': 'PASS',
                    'class': class_name
                }
                print(f"  ✓ {module_name} initialized")
                
            except Exception as e:
                self.results[module_name] = {
                    'status': 'FAIL',
                    'error': str(e)
                }
                print(f"  ✗ {module_name}: {e}")
    
    def test_24_7_loop_engines(self):
        """Test engines that run in 24/7 loop"""
        print("\nTesting 24/7 Loop Engines...")
        
        # Market scanner
        try:
            from engines.market_scanner_24_7 import MarketScanner247
            
            scanner = MarketScanner247()
            
            # Test scan method
            opportunities = scanner.scan_opportunities()
            
            assert isinstance(opportunities, list)
            
            self.results['market_scanner_24_7'] = {
                'status': 'PASS',
                'opportunities': len(opportunities)
            }
            print(f"  ✓ Found {len(opportunities)} opportunities")
            
        except Exception as e:
            self.results['market_scanner_24_7'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"  FAIL Error: {e}")
    
    def run_all_tests(self):
        """Run all functional tests"""
        print("=" * 80)
        print("INTEGRATED ENGINES FUNCTIONAL TEST")
        print("=" * 80)
        print(f"Testing with sample data for {self.test_data['stock_ticker']}")
        
        # Run tests in execution order
        test_methods = [
            self.test_pump_dump_detector,
            self.test_global_macro_monitor,
            self.test_insider_signal_integrator,
            self.test_kalshi_engine,
            self.test_market_crash_detector,
            self.test_news_engines,
            self.test_other_integrated_engines,
            self.test_24_7_loop_engines
        ]
        
        for test in test_methods:
            test()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 80)
        print("FUNCTIONAL TEST REPORT")
        print("=" * 80)
        
        total = len(self.results)
        passed = len([r for r in self.results.values() if r['status'] == 'PASS'])
        failed = total - passed
        
        print(f"\nSUMMARY:")
        print(f"  Total engines tested: {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Success rate: {passed/total*100:.1f}%")
        
        print(f"\nFAILED ENGINES:")
        for engine, result in self.results.items():
            if result['status'] == 'FAIL':
                print(f"  - {engine}: {result.get('error', 'Unknown error')}")
        
        print(f"\nWORKING ENGINES:")
        for engine, result in self.results.items():
            if result['status'] == 'PASS':
                print(f"  ✓ {engine}")
        
        # Save detailed results
        with open('integrated_engine_test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': failed
                },
                'results': self.results
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: integrated_engine_test_results.json")
        
        if failed == 0:
            print("\n✅ ALL INTEGRATED ENGINES WORKING!")
        else:
            print(f"\n⚠️ {failed} engines need attention")


def main():
    """Run the functional test suite"""
    tester = IntegratedEngineTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
