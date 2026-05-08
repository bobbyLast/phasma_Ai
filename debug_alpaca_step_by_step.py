#!/usr/bin/env python3

# Step-by-Step Alpaca Debug
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_alpaca_step_by_step():
    """Debug Alpaca integration step by step"""
    print("🔧 Step-by-Step Alpaca Debug...")
    
    # Step 1: Import Test
    print("\n📋 STEP 1: Testing Import...")
    try:
        from engines.alpaca_paper_trader import AlpacaPaperTrader
        print("✅ AlpacaPaperTrader imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Step 2: Initialization Test
    print("\n📋 STEP 2: Testing Initialization...")
    try:
        trader = AlpacaPaperTrader()
        print("✅ AlpacaPaperTrader initialized")
        
        # Check credentials
        print(f"   API Key: {trader.api_key[:10]}...")
        print(f"   Base URL: {trader.base_url}")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # Step 3: Connection Test
    print("\n📋 STEP 3: Testing Connection...")
    try:
        if hasattr(trader, 'alpaca') and trader.alpaca:
            print("✅ Alpaca client exists")
            
            # Test connection with get_account
            account = trader.alpaca.get_account()
            print("✅ Connection successful")
            print(f"   Account ID: {account.id}")
            print(f"   Buying Power: ${float(account.buying_power):,.2f}")
            
        else:
            print("❌ Alpaca client not initialized")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Step 4: Order Placement Test
    print("\n📋 STEP 4: Testing Order Placement...")
    try:
        # Create a test order (but don't actually submit)
        test_order = {
            'symbol': 'AAPL',
            'side': 'buy',
            'type': 'market',
            'qty': 1,
            'time_in_force': 'day'
        }
        
        print(f"   Test order: {test_order}")
        
        # Try to submit the order
        order = trader.alpaca.submit_order(
            symbol=test_order['symbol'],
            side=test_order['side'],
            type=test_order['type'],
            qty=test_order['qty'],
            time_in_force=test_order['time_in_force']
        )
        
        print(f"✅ Order submitted successfully")
        print(f"   Order ID: {order.id}")
        print(f"   Status: {order.status}")
        
        # Cancel the test order immediately
        trader.alpaca.cancel_order(order.id)
        print(f"✅ Test order cancelled")
        
        return True
        
    except Exception as e:
        print(f"❌ Order placement failed: {e}")
        return False
    
    # Step 5: Method Integration Test
    print("\n📋 STEP 5: Testing Method Integration...")
    try:
        from main import PhasmaTradingSystem
        system = PhasmaTradingSystem()
        
        if hasattr(system, 'alpaca_paper_trader'):
            if system.alpaca_paper_trader:
                print("✅ AlpacaPaperTrader integrated in main system")
                
                # Test the trade execution method
                test_signal = {
                    'symbol': 'AAPL',
                    'action': 'BUY',
                    'confidence': 85,
                    'position_size': 1000,
                    'entry_price': 150.0,
                    'trade_type': 'STOCK'
                }
                
                result = system._execute_alpaca_trade_from_signal(test_signal)
                print(f"   Method result: {result}")
                
                if result and result.get('success'):
                    print("✅ Trade execution method working")
                else:
                    print("❌ Trade execution method failed")
                    return False
            else:
                print("❌ AlpacaPaperTrader is None in main system")
                return False
        else:
            print("❌ AlpacaPaperTrader not found in main system")
            return False
            
    except Exception as e:
        print(f"❌ Method integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_alpaca_step_by_step()
    if success:
        print("\n🎯 ALL STEPS PASSED - ALPACA INTEGRATION WORKING!")
    else:
        print("\n⚠️ SOME STEPS FAILED - NEED TO FIX ISSUES")
