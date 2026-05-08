"""
============================================================
PHASMA AI - FINAL MAIN TEST
============================================================
Confirm main.py works perfectly
"""

import subprocess
import sys
import os
import time

def test_main_final():
    """Test the final main script"""
    
    print("=" * 80)
    print("PHASMA AI - FINAL MAIN.PY TEST")
    print("=" * 80)
    print("Testing main_final.py execution...")
    print("=" * 80)
    
    tests = {
        'default_run': False,
        'test_mode': False,
        'production_mode': False
    }
    
    # Test 1: Default run
    print("\n[TEST 1] Default run (python main_final.py)...")
    try:
        result = subprocess.run(
            [sys.executable, 'main_final.py'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0 and 'SUCCESS: Phasma AI is production ready!' in result.stdout:
            print("  ✅ Default run PASSED")
            tests['default_run'] = True
        else:
            print("  ❌ Default run FAILED")
            print(f"  Exit code: {result.returncode}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 2: Test mode
    print("\n[TEST 2] Test mode (python main_final.py --test)...")
    try:
        result = subprocess.run(
            [sys.executable, 'main_final.py', '--test'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0 and 'Running in test mode...' in result.stdout:
            print("  ✅ Test mode PASSED")
            tests['test_mode'] = True
        else:
            print("  ❌ Test mode FAILED")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 3: Production mode (quick test)
    print("\n[TEST 3] Production mode (python main_final.py --production)...")
    try:
        # Start production mode but kill after 5 seconds
        proc = subprocess.Popen(
            [sys.executable, 'main_final.py', '--production'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        
        # Wait 5 seconds
        time.sleep(5)
        
        # Terminate
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5)
        
        if 'Running in production mode...' in stdout:
            print("  ✅ Production mode STARTED successfully")
            tests['production_mode'] = True
        else:
            print("  ❌ Production mode failed to start")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Results
    print("\n" + "=" * 80)
    print("FINAL TEST RESULTS")
    print("=" * 80)
    
    passed = sum(tests.values())
    total = len(tests)
    
    for test_name, passed in tests.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\nSummary: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ main_final.py is PRODUCTION READY!")
        print("\nUsage:")
        print("  python main_final.py           - Default test run")
        print("  python main_final.py --test    - Test mode")
        print("  python main_final.py --production - Production mode")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("❌ Review errors above")
        return False

if __name__ == "__main__":
    success = test_main_final()
    sys.exit(0 if success else 1)
