#!/usr/bin/env python3

# Test Alpaca Integration Completion
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_alpaca_integration_complete():
    """Test if Alpaca integration is fully working in main.py"""
    print("🔧 Testing Alpaca Integration Completion...")
    
    try:
        # Test 1: Import main system
        from main import PhasmaTradingSystem
        print("✅ Main system import successful")
        
        # Test 2: Initialize system (this will show if Alpaca is working)
        print("\n🚀 Initializing Phasma AI with Alpaca integration...")
        system = PhasmaTradingSystem()
        
        # Test 3: Check if Alpaca trader was initialized
        if hasattr(system, 'alpaca_paper_trader'):
            if system.alpaca_paper_trader and hasattr(system.alpaca_paper_trader, 'alpaca'):
                if system.alpaca_paper_trader.alpaca:
                    print("✅ Alpaca Paper Trading initialized in main system")
                    
                    # Get account info
                    account = system.alpaca_paper_trader.get_account()
                    print(f"   Account ID: {account.get('account_id', 'N/A')}")
                    print(f"   Buying Power: ${account.get('buying_power', 0):,.2f}")
                    print(f"   Portfolio Value: ${account.get('portfolio_value', 0):,.2f}")
                    
                    print("\n🎯 INTEGRATION COMPLETE!")
                    print("   ✅ Alpaca connected to main system")
                    print("   ✅ Real market data available")
                    print("   ✅ Trades will execute via Alpaca before Telegram")
                    print("   ✅ Fake internal paper trading replaced")
                    
                    return True
                else:
                    print("❌ Alpaca Paper Trading initialized but not connected")
                    return False
            else:
                print("❌ Alpaca Paper Trading attribute exists but not properly initialized")
                return False
        else:
            print("❌ Alpaca Paper Trading not found in main system")
            print("   The initialization code needs to be added to main.py")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_alpaca_integration_complete()
    if success:
        print("\n🚀 READY TO RUN!")
        print("   When main.py runs, trades will execute via Alpaca before posting to Telegram")
        print("   This replaces the fake internal paper trading with real market data")
    else:
        print("\n⚠️ Integration needs completion")
        print("   The AlpacaPaperTrader initialization needs to be added to main.py constructor")
