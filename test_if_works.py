#!/usr/bin/env python3

# Test if Alpaca integration actually works
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_integration_works():
    """Test if the Alpaca integration actually works"""
    print("🔧 Testing if Alpaca integration actually works...")
    
    try:
        # Test 1: Check if paper trading is enabled in config
        from core.config import PhasmaConfig
        config = PhasmaConfig()
        
        paper_trading_enabled = config.get('paper_trading', {}).get('enabled', False)
        print(f"   Paper trading enabled: {paper_trading_enabled}")
        
        if not paper_trading_enabled:
            print("❌ Paper trading is disabled in config - Alpaca won't initialize")
            return False
        
        # Test 2: Try to initialize the system
        print("\n🚀 Initializing Phasma AI...")
        from main import PhasmaTradingSystem
        
        system = PhasmaTradingSystem()
        
        # Test 3: Check if Alpaca was initialized
        if hasattr(system, 'alpaca_paper_trader'):
            if system.alpaca_paper_trader:
                if hasattr(system.alpaca_paper_trader, 'alpaca') and system.alpaca_paper_trader.alpaca:
                    print("✅ Alpaca Paper Trading is working!")
                    
                    # Test account info
                    account = system.alpaca_paper_trader.get_account()
                    print(f"   Account ID: {account.get('account_id', 'N/A')}")
                    print(f"   Buying Power: ${account.get('buying_power', 0):,.2f}")
                    
                    return True
                else:
                    print("❌ Alpaca Paper Trading initialized but not connected")
                    return False
            else:
                print("❌ Alpaca Paper Trading is None")
                return False
        else:
            print("❌ Alpaca Paper Trading not found in system")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration_works()
    if success:
        print("\n🎯 YES - Alpaca integration works!")
        print("   ✅ Real paper trading will replace fake internal system")
        print("   ✅ Trades will execute via Alpaca before Telegram")
    else:
        print("\n⚠️ NO - Integration has issues that need fixing")
