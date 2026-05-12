#!/usr/bin/env python3

# Debug Step 5 - Method Integration
import sys
import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
def debug_step5():
    """Debug Step 5 - Method Integration"""
    print("🔧 Debugging Step 5: Method Integration...")
    
    try:
        print("\n📋 STEP 5A: Testing Main System Initialization...")
        from main import PhasmaTradingSystem
        system = PhasmaTradingSystem()
        
        print("✅ Main system initialized")
        
        print("\n📋 STEP 5B: Checking AlpacaPaperTrader in main system...")
        if hasattr(system, 'alpaca_paper_trader'):
            print("✅ alpaca_paper_trader attribute exists")
            
            if system.alpaca_paper_trader:
                print("✅ alpaca_paper_trader is not None")
                
                if hasattr(system.alpaca_paper_trader, 'alpaca'):
                    if system.alpaca_paper_trader.alpaca:
                        print("✅ alpaca client is connected")
                    else:
                        print("❌ alpaca client is None")
                else:
                    print("❌ alpaca attribute missing")
            else:
                print("❌ alpaca_paper_trader is None")
        else:
            print("❌ alpaca_paper_trader attribute missing")
            return False
        
        print("\n📋 STEP 5C: Testing _execute_alpaca_trade_from_signal method...")
        if hasattr(system, '_execute_alpaca_trade_from_signal'):
            print("✅ _execute_alpaca_trade_from_signal method exists")
            
            # Test signal
            test_signal = {
                'symbol': 'AAPL',
                'action': 'BUY',
                'confidence': 85,
                'position_size': 1000,
                'entry_price': 150.0,
                'trade_type': 'STOCK'
            }
            
            print(f"\n🔄 Calling _execute_alpaca_trade_from_signal...")
            print(f"   Signal: {test_signal}")
            
            # Call the method
            result = system._execute_alpaca_trade_from_signal(test_signal)
            
            print(f"\n📊 Method returned: {result}")
            print(f"   Type: {type(result)}")
            
            if result:
                if isinstance(result, dict):
                    print(f"   Keys: {list(result.keys())}")
                    if result.get('success'):
                        print("✅ Trade execution successful")
                        print(f"   Order ID: {result.get('order_id', 'N/A')}")
                    else:
                        print(f"❌ Trade execution failed: {result.get('error', 'Unknown error')}")
                else:
                    print(f"❌ Method returned non-dict: {result}")
            else:
                print("❌ Method returned None")
                
        else:
            print("❌ _execute_alpaca_trade_from_signal method missing")
            return False
            
    except Exception as e:
        print(f"❌ Step 5 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_step5()
