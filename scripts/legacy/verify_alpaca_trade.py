#!/usr/bin/env python3

# Verify Real Alpaca Trade
import sys
import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
def verify_alpaca_trade():
    """Check if trade was actually placed on Alpaca"""
    print("🔍 Verifying Real Alpaca Trade...")
    
    try:
        from engines.alpaca_paper_trader import AlpacaPaperTrader
        
        # Initialize Alpaca trader
        trader = AlpacaPaperTrader()
        
        if trader.alpaca:
            print("✅ Connected to Alpaca")
            
            # Check recent orders
            print("\n📋 Checking Recent Orders...")
            orders = trader.alpaca.list_orders(status='all', limit=10)
            
            if orders:
                print(f"✅ Found {len(orders)} recent orders:")
                for order in orders[-3:]:  # Show last 3 orders
                    print(f"   - {order.symbol} {order.side} {order.qty} @ ${order.filled_avg_price or 'pending'}")
                    print(f"     Status: {order.status}")
                    print(f"     Order ID: {order.id}")
                    print(f"     Created: {order.created_at}")
            else:
                print("❌ No recent orders found")
                
            # Check positions
            print("\n💼 Checking Current Positions...")
            positions = trader.get_positions()
            
            if positions:
                print(f"✅ Current positions:")
                for pos in positions:
                    print(f"   - {pos['symbol']}: {pos['qty']} shares @ ${pos['avg_price']}")
            else:
                print("❌ No open positions")
                
            # Check account
            print("\n💰 Account Status:")
            account = trader.get_account()
            print(f"   Portfolio Value: ${account.get('portfolio_value', 0):,.2f}")
            print(f"   Buying Power: ${account.get('buying_power', 0):,.2f}")
            
        else:
            print("❌ Not connected to Alpaca")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_alpaca_trade()
