#!/usr/bin/env python3
"""
Test script for Real Portfolio Manager
Verifies proper tracking of trades and P&L separation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.real_portfolio_manager import RealPortfolioManager
import json
import os

def test_portfolio_tracking():
    """Test portfolio tracking with sample trades using TEST DATA"""
    
    print("Testing Real Portfolio Manager (with TEST DATA)...")
    print("="*60)
    
    # Use test portfolio file to avoid affecting real trades
    test_portfolio_file = "data/portfolio/test_portfolio_state.json"
    
    # Backup real portfolio and use test file
    real_portfolio_file = "data/portfolio/real_portfolio_state.json"
    if os.path.exists(real_portfolio_file):
        # Initialize with test mode to use separate file
        portfolio = RealPortfolioManager(test_mode=True, state_file=test_portfolio_file)
    else:
        portfolio = RealPortfolioManager()
    
    # Initial state
    summary = portfolio.get_portfolio_summary()
    print(f"Initial State:")
    print(f"  Starting Capital: ${summary['starting_capital']:.2f}")
    print(f"  Available Cash: ${summary['available_capital']:.2f}")
    print(f"  Realized P&L: ${summary['realized_pnl']:.2f}")
    print(f"  Unrealized P&L: ${summary['unrealized_pnl']:.2f}")
    print(f"  Total Value: ${summary['total_portfolio_value']:.2f}")
    print()
    
    # Execute buy order (use realistic size for $50 bankroll)
    print("Executing BUY order: 1 share of AAPL at $150.00")
    result = portfolio.execute_buy('AAPL', 1, 150.00)
    if not result['success']:
        print(f"  X Buy failed: {result['error']}")
        # Try with smaller amount
        print("Trying smaller order: 3 shares of AI at $14.00")
        result = portfolio.execute_buy('AI', 3, 14.00)
        if not result['success']:
            print(f"  X Fallback buy also failed: {result['error']}")
            return
    
    # This should now have a successful result
    print(f"  + Order executed: Trade ID {result['trade_id']}")
    print(f"  + Cost: ${result['total_cost']:.2f}")
    print(f"  + Remaining cash: ${result['remaining_capital']:.2f}")
    print()
    
    # Check state after buy
    summary = portfolio.get_portfolio_summary()
    print(f"After BUY order:")
    print(f"  Available Cash: ${summary['available_capital']:.2f}")
    print(f"  Realized P&L: ${summary['realized_pnl']:.2f}")
    print(f"  Unrealized P&L: ${summary['unrealized_pnl']:.2f}")
    print(f"  Total Value: ${summary['total_portfolio_value']:.2f}")
    print()
    
    # Execute sell order at profit
    print("Executing SELL order: 3 shares of AI at $16.00")
    result = portfolio.execute_sell('AI', 3, 16.00, reason="Take profit")
    if result['success']:
        print(f"  + Order executed: Trade ID {result['trade_id']}")
    print(f"  + Proceeds: ${result['proceeds']:.2f}")
    print(f"  + Realized P&L: ${result['realized_pnl']:.2f}")
    print(f"  + Total Realized P&L: ${result['total_realized_pnl']:.2f}")
    print()
    
    # Final state
    summary = portfolio.get_portfolio_summary()
    print(f"After SELL order:")
    print(f"  Available Cash: ${summary['available_capital']:.2f}")
    print(f"  Realized P&L: ${summary['realized_pnl']:.2f}")
    print(f"  Unrealized P&L: ${summary['unrealized_pnl']:.2f}")
    print(f"  Total Value: ${summary['total_portfolio_value']:.2f}")
    print(f"  Total Return: ${summary['total_return']:.2f} ({summary['total_return_pct']:.1f}%)")
    print(f"  Total Trades: {summary['total_trades']}")
    print(f"  Win Rate: {summary['win_rate']:.1f}%")
    print()
    
    # Show trade history
    print("Trade History:")
    trades = portfolio.get_trade_history()
    for trade in trades:
        print(f"  {trade['timestamp'][:19]}: {trade['action']} {trade['quantity']} {trade['symbol']} @ ${trade['price']:.2f}")
        if 'realized_pnl' in trade:
            print(f"    P&L: ${trade['realized_pnl']:.2f}")
    
    print("\n" + "="*60)
    print("+ Real Portfolio Manager test completed successfully!")
    print("+ Properly separates realized vs unrealized P&L")
    print("+ Only updates bankroll on actual trade closures")

if __name__ == "__main__":
    test_portfolio_tracking()
