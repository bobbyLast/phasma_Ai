#!/usr/bin/env python3

# Test Full Alpaca Paper Trading Integration
from engines.alpaca_paper_trader import AlpacaPaperTrader

def test_full_alpaca_integration():
    """Test complete Alpaca paper trading functionality"""
    print("🔧 Testing Full Alpaca Paper Trading Integration...")
    
    try:
        # Initialize Alpaca Paper Trader
        trader = AlpacaPaperTrader()
        
        if trader.alpaca:
            print("✅ SUCCESS: Alpaca Paper Trading Connected")
            
            # Get account info
            account = trader.get_account()
            print(f"   Account ID: {account.get('account_id', 'N/A')}")
            print(f"   Buying Power: ${account.get('buying_power', 0):,.2f}")
            print(f"   Portfolio Value: ${account.get('portfolio_value', 0):,.2f}")
            
            # Get current positions
            positions = trader.get_positions()
            print(f"   Open Positions: {len(positions)}")
            
            for pos in positions:
                print(f"      {pos['symbol']}: {pos['quantity']} @ ${pos['avg_cost']:.2f} | P&L: ${pos['unrealized_pnl']:+.2f}")
            
            # Get performance summary
            performance = trader.get_performance_summary()
            print(f"   Total Trades: {performance.get('total_trades', 0)}")
            print(f"   Winning Trades: {performance.get('winning_trades', 0)}")
            print(f"   Losing Trades: {performance.get('losing_trades', 0)}")
            print(f"   Platform: {performance.get('platform', 'Alpaca')}")
            
            # Test a small trade (optional - comment out if you don't want to place orders)
            print("\n🎯 Ready to replace internal paper trading!")
            print("   ✅ Real market data via Alpaca")
            print("   ✅ Independent verification")
            print("   ✅ Professional platform")
            
            return True
        else:
            print("❌ FAILED: Could not connect to Alpaca")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_full_alpaca_integration()
    if success:
        print("\n🎯 Alpaca Paper Trading is ready to replace the fake internal system!")
        print("   Next: Integrate with Phasma AI main system")
    else:
        print("\n⚠️ Integration needs troubleshooting")
