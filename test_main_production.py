"""
============================================================
PHASMA AI - MAIN.PY PRODUCTION TEST
============================================================
Test that everything works when main is run
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import json
import subprocess
import time

def test_main_production():
    """Test the main production system"""
    
    print("=" * 80)
    print("PHASMA AI - MAIN.PY PRODUCTION TEST")
    print("=" * 80)
    print("Testing complete main.py execution...")
    print("=" * 80)
    
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {},
        'overall_status': 'unknown'
    }
    
    # Test 1: Check if main_production.py exists and is runnable
    print("\n[TEST 1] Checking main_production.py...")
    try:
        if os.path.exists('main_production.py'):
            print("  ✅ main_production.py exists")
            
            # Check if it's executable
            with open('main_production.py', 'r') as f:
                content = f.read()
                if 'def main():' in content and 'if __name__ == "__main__":' in content:
                    print("  ✅ main_production.py has proper structure")
                    test_results['tests']['main_exists'] = 'PASS'
                else:
                    print("  ❌ main_production.py structure invalid")
                    test_results['tests']['main_exists'] = 'FAIL'
        else:
            print("  ❌ main_production.py not found")
            test_results['tests']['main_exists'] = 'FAIL'
    except Exception as e:
        print(f"  ❌ Error: {e}")
        test_results['tests']['main_exists'] = 'FAIL'
    
    # Test 2: Run main_production.py in test mode
    print("\n[TEST 2] Running main_production.py --test...")
    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, 'main_production.py', '--test'],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.getcwd()
        )
        end_time = time.time()
        
        print(f"  Execution time: {end_time - start_time:.2f}s")
        print(f"  Exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("  ✅ main_production.py --test PASSED")
            test_results['tests']['main_test'] = 'PASS'
            
            # Check output for key indicators
            output = result.stdout
            if 'PRODUCTION READY' in output:
                print("  ✅ Production ready confirmed")
            if 'Signals detected:' in output:
                print("  ✅ Signal detection working")
            if 'Sources working:' in output:
                print("  ✅ Data sources working")
        else:
            print("  ❌ main_production.py --test FAILED")
            print(f"  Error: {result.stderr[:200]}")
            test_results['tests']['main_test'] = 'FAIL'
            
    except subprocess.TimeoutExpired:
        print("  ❌ Test timed out (60s)")
        test_results['tests']['main_test'] = 'FAIL'
    except Exception as e:
        print(f"  ❌ Error running test: {e}")
        test_results['tests']['main_test'] = 'FAIL'
    
    # Test 3: Check all dependencies
    print("\n[TEST 3] Checking dependencies...")
    dependencies = [
        'requests',
        'feedparser',
        'yfinance',
        'beautifulsoup4',
        'config.secure_config',
        'engines.final_100_percent_integration',
        'final_integration_test'
    ]
    
    deps_passed = 0
    for dep in dependencies:
        try:
            if '.' in dep:
                # Module with dots
                parts = dep.split('.')
                module = __import__(parts[0])
                for part in parts[1:]:
                    module = getattr(module, part)
            else:
                module = __import__(dep)
            print(f"  ✅ {dep}")
            deps_passed += 1
        except ImportError:
            print(f"  ❌ {dep} - NOT INSTALLED")
        except Exception as e:
            print(f"  ⚠️  {dep} - Error: {str(e)[:50]}")
    
    if deps_passed == len(dependencies):
        test_results['tests']['dependencies'] = 'PASS'
    else:
        test_results['tests']['dependencies'] = 'FAIL'
    
    # Test 4: Check configuration
    print("\n[TEST 4] Checking configuration...")
    try:
        from config.secure_config import config
        
        required_keys = [
            'world_news_api_key',
            'gnews_api_key',
            'mediastack_api_key',
            'currents_api_key'
        ]
        
        config_ok = True
        for key in required_keys:
            if hasattr(config, key) and getattr(config, key):
                print(f"  ✅ {key}")
            else:
                print(f"  ❌ {key} - missing")
                config_ok = False
        
        if config_ok:
            test_results['tests']['configuration'] = 'PASS'
        else:
            test_results['tests']['configuration'] = 'FAIL'
            
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        test_results['tests']['configuration'] = 'FAIL'
    
    # Test 5: Check data sources individually
    print("\n[TEST 5] Testing data sources...")
    try:
        from engines.final_100_percent_integration import Final100PercentIntegration
        
        integration = Final100PercentIntegration()
        results = integration.get_final_results()
        
        success_rate = results.get('success_rate', 0)
        if success_rate >= 90:
            print(f"  ✅ Data sources: {success_rate:.1f}% success rate")
            test_results['tests']['data_sources'] = 'PASS'
        elif success_rate >= 70:
            print(f"  ⚠️  Data sources: {success_rate:.1f}% success rate (degraded)")
            test_results['tests']['data_sources'] = 'WARN'
        else:
            print(f"  ❌ Data sources: {success_rate:.1f}% success rate")
            test_results['tests']['data_sources'] = 'FAIL'
            
    except Exception as e:
        print(f"  ❌ Data sources error: {e}")
        test_results['tests']['data_sources'] = 'FAIL'
    
    # Test 6: Check signal detection
    print("\n[TEST 6] Testing signal detection...")
    try:
        from final_integration_test import FinalIntegrationTest
        
        tester = FinalIntegrationTest()
        signals = tester.analyze_all_sources()
        
        if len(signals) > 0:
            print(f"  ✅ Signal detection: {len(signals)} signals found")
            test_results['tests']['signal_detection'] = 'PASS'
        else:
            print("  ⚠️  Signal detection: No signals found")
            test_results['tests']['signal_detection'] = 'WARN'
            
    except Exception as e:
        print(f"  ❌ Signal detection error: {e}")
        test_results['tests']['signal_detection'] = 'FAIL'
    
    # Calculate overall status
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for t in test_results['tests'].values() if t == 'PASS')
    warned = sum(1 for t in test_results['tests'].values() if t == 'WARN')
    failed = sum(1 for t in test_results['tests'].values() if t == 'FAIL')
    total = len(test_results['tests'])
    
    for test_name, status in test_results['tests'].items():
        status_symbol = {
            'PASS': '✅',
            'WARN': '⚠️',
            'FAIL': '❌'
        }.get(status, '❓')
        print(f"  {status_symbol} {test_name}: {status}")
    
    print(f"\nSUMMARY:")
    print(f"  Passed: {passed}/{total}")
    print(f"  Warnings: {warned}/{total}")
    print(f"  Failed: {failed}/{total}")
    
    # Determine overall status
    if failed == 0:
        if warned == 0:
            test_results['overall_status'] = 'PRODUCTION READY'
            print("\n🎉 OVERALL: PRODUCTION READY!")
        else:
            test_results['overall_status'] = 'READY WITH WARNINGS'
            print("\n✅ OVERALL: READY WITH WARNINGS")
    else:
        test_results['overall_status'] = 'NOT READY'
        print("\n❌ OVERALL: NOT READY - Fix failed tests")
    
    # Save test results
    with open('main_production_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"\n📄 Test results saved to: main_production_test_results.json")
    
    # Final recommendation
    print("\n" + "=" * 80)
    print("DEPLOYMENT RECOMMENDATION")
    print("=" * 80)
    
    if test_results['overall_status'] == 'PRODUCTION READY':
        print("✅ DEPLOY NOW!")
        print("   All systems are go for production")
        print("   Run: python main_production.py --production")
    elif test_results['overall_status'] == 'READY WITH WARNINGS':
        print("⚠️  DEPLOY WITH CAUTION")
        print("   System works but has warnings")
        print("   Review warnings before production")
    else:
        print("❌ DO NOT DEPLOY")
        print("   Fix failed tests first")
        print("   Review errors above")
    
    print("=" * 80)
    
    return test_results

def test_actual_main_run():
    """Test actual main.py run"""
    
    print("\n[ADDITIONAL TEST] Simulating actual main.py run...")
    
    # This simulates what would happen when main.py is executed
    try:
        # Import and initialize like main.py would
        from main_production import PhasmaAIProduction
        
        print("  ✅ Main production class imported")
        
        # Initialize system
        system = PhasmaAIProduction()
        print("  ✅ System initialized")
        
        # Check health
        health = system.check_system_health()
        if health['overall']:
            print("  ✅ System health check passed")
        
        # Run a quick test cycle
        print("  🔄 Running test cycle...")
        success = system.run_production_cycle()
        
        if success:
            print("  ✅ Test cycle completed")
            return True
        else:
            print("  ❌ Test cycle failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Main run simulation failed: {e}")
        return False

if __name__ == "__main__":
    # Run comprehensive tests
    results = test_main_production()
    
    # Run additional test
    if results['overall_status'] in ['PRODUCTION READY', 'READY WITH WARNINGS']:
        print("\n" + "=" * 80)
        actual_test = test_actual_main_run()
        
        if actual_test:
            print("\n✅ ALL TESTS PASSED - SYSTEM IS READY!")
        else:
            print("\n⚠️  Some tests failed - review above")
    
    # Exit with appropriate code
    if results['overall_status'] == 'PRODUCTION READY':
        sys.exit(0)
    elif results['overall_status'] == 'READY WITH WARNINGS':
        sys.exit(1)
    else:
        sys.exit(2)
