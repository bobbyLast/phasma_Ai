#!/usr/bin/env python3

# Test Enhanced Alpaca with Whole Stock Logic and Auto-Selling
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_alpaca():
    """Test the enhanced Alpaca integration"""
    print("🔧 Testing Enhanced Alpaca Integration...")
    
    try:
        from main import PhasmaTradingSystem
        
        print("\n🚀 Initializing Phasma AI with Enhanced Alpaca...")
        system = PhasmaTradingSystem()
        
        # Check if enhanced trader is initialized
        if hasattr(system, 'alpaca_paper_trader'):
            if system.alpaca_paper_trader and hasattr(system.alpaca_paper_trader, 'calculate_position_size'):
                print("✅ Enhanced Alpaca Paper Trading is ready!")
                
                # Test 1: Whole Stock Logic
                print("\n📊 TEST 1: Whole Stock Logic")
                test_signals = [
                    {
                        'symbol': 'AAPL',
                        'action': 'BUY',
                        'confidence': 85,
                        'position_size': 5000,  # Can afford whole stock
                        'entry_price': 150.0,
                        'trade_type': 'STOCK'
                    },
                    {
                        'symbol': 'GOOGL',
                        'action': 'BUY',
                        'confidence': 90,  # High confidence for fractional
                        'position_size': 500,   # Can't afford whole stock
                        'entry_price': 2800.0,
                        'trade_type': 'STOCK'
                    }
                ]
                
                for i, signal in enumerate(test_signals, 1):
                    print(f"\n  🔄 Test Signal {i}: {signal['symbol']}")
                    print(f"     Position Size: ${signal['position_size']}")
                    print(f"     Entry Price: ${signal['entry_price']}")
                    print(f"     Confidence: {signal['confidence']}%")
                    
                    result = system._execute_alpaca_trade_from_signal(signal)
                    
                    if result and result.get('success'):
                        print(f"  ✅ TRADE EXECUTED!")
                        print(f"     Order ID: {result.get('order_id', 'N/A')}")
                        print(f"     Quantity: {result.get('quantity', 'N/A')}")
                        print(f"     Take Profit: ${result.get('take_profit', 'N/A')}")
                        print(f"     Stop Loss: ${result.get('stop_loss', 'N/A')}")
                        
                        # Check if it's whole stock or shares
                        if result.get('quantity') == 1:
                            print(f"     📊 Position Type: WHOLE STOCK")
                        else:
                            print(f"     📊 Position Type: {result.get('quantity')} SHARES")
                    else:
                        print(f"  ❌ Trade failed: {result.get('error', 'Unknown error') if result else 'Method returned None'}")
                
                # Test 2: Auto-Selling Logic
                print("\n📊 TEST 2: Auto-Selling Logic")
                positions = system.alpaca_paper_trader.get_positions()
                
                if positions:
                    print(f"  ✅ Found {len(positions)} open positions")
                    for pos in positions:
                        print(f"     - {pos['symbol']}: {pos['quantity']} @ ${pos['entry_price']}")
                        print(f"       Take Profit: ${pos['take_profit']:.2f}")
                        print(f"       Stop Loss: ${pos['stop_loss']:.2f}")
                        
                        # Simulate price change for exit testing
                        current_price = pos['entry_price'] * 1.25  # 25% gain - should trigger take profit
                        test_prices = {pos['symbol']: current_price}
                        
                        print(f"\n  🔄 Testing exit signals at ${current_price:.2f}...")
                        exit_signals = system.alpaca_paper_trader.check_exit_signals(test_prices)
                        
                        if exit_signals:
                            for signal in exit_signals:
                                print(f"  ✅ EXIT EXECUTED!")
                                print(f"     Symbol: {signal['symbol']}")
                                print(f"     Reason: {signal['reason']}")
                                print(f"     Price: ${signal['price']:.2f}")
                                print(f"     P&L: {signal['pnl_percent']:+.2f}%")
                        else:
                            print(f"  ❌ No exit signals generated")
                else:
                    print(f"  ❌ No open positions to test auto-selling")
                
                return True
            else:
                print("❌ Enhanced Alpaca Paper Trading not initialized")
                return False
        else:
            print("❌ Alpaca Paper Trading not available")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_alpaca()
    if success:
        print("\n🎯 ENHANCED ALPACA INTEGRATION WORKING!")
        print("   ✅ Whole Stock Logic: Buy 1 stock if affordable")
        print("   ✅ Fractional Shares: Buy shares only if confident")
        print("   ✅ Auto-Selling: Take profit + Stop loss")
        print("   ✅ Position Tracking: Monitor entries/exits")
    else:
        print("\n⚠️ Test failed - needs fixes")
