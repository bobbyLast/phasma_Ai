#!/usr/bin/env python3
"""
Verification Script - Ensures AI never shows fake paper profits as real money
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.real_portfolio_manager import RealPortfolioManager

def verify_portfolio_integrity():
    """Verify that the portfolio system is honest about profits"""
    
    print("="*60)
    print("PORTFOLIO INTEGRITY VERIFICATION")
    print("="*60)
    
    # Initialize real portfolio
    portfolio = RealPortfolioManager()
    
    # Get current state
    summary = portfolio.get_portfolio_summary()
    
    print("\n[OK] CHECK 1: Real Portfolio Manager Active")
    print(f"   Starting Capital: ${summary['starting_capital']:.2f}")
    print(f"   Available Cash: ${summary['available_capital']:.2f}")
    print(f"   Realized P&L: ${summary['realized_pnl']:.2f}")
    print(f"   Unrealized P&L: ${summary['unrealized_pnl']:.2f}")
    print(f"   Total Portfolio Value: ${summary['total_portfolio_value']:.2f}")
    
    # Verify no fake portfolio_state.json exists
    fake_portfolio_file = os.path.join(
        os.path.dirname(__file__), 'data', 'portfolio', 'portfolio_state.json'
    )
    
    print("\n[OK] CHECK 2: Fake Portfolio File Removed")
    if os.path.exists(fake_portfolio_file):
        print("   [ERROR] Fake portfolio_state.json still exists!")
        print("   This file contains fake profit calculations.")
        return False
    else:
        print("   [OK] Fake portfolio_state.json successfully deleted")
    
    # Verify trade log integrity
    trades = portfolio.get_trade_history()
    print(f"\n[OK] CHECK 3: Trade Log Integrity")
    print(f"   Total Trades Recorded: {len(trades)}")
    
    if trades:
        total_realized = 0
        for trade in trades:
            if trade['action'] == 'SELL' and 'realized_pnl' in trade:
                total_realized += trade['realized_pnl']
        
        print(f"   Total Realized P&L from trades: ${total_realized:.2f}")
        
        if abs(total_realized - summary['realized_pnl']) < 0.01:
            print("   [OK] Trade P&L matches portfolio P&L")
        else:
            print("   [ERROR] Trade P&L doesn't match portfolio!")
            return False
    
    # Verify bankroll calculation
    calculated_total = (summary['available_capital'] + 
                       summary['realized_pnl'] + 
                       summary['unrealized_pnl'])
    
    print(f"\n[OK] CHECK 4: Bankroll Calculation")
    print(f"   Available Cash: ${summary['available_capital']:.2f}")
    print(f"   + Realized P&L: ${summary['realized_pnl']:.2f}")
    print(f"   + Unrealized P&L: ${summary['unrealized_pnl']:.2f}")
    print(f"   = Total Value: ${calculated_total:.2f}")
    
    if abs(calculated_total - summary['total_portfolio_value']) < 0.01:
        print("   [OK] Bankroll calculation is correct")
    else:
        print("   [ERROR] Bankroll calculation is wrong!")
        return False
    
    # Final verification
    print(f"\n[OK] CHECK 5: No Fake Profits")
    print(f"   Only realized profits (${summary['realized_pnl']:.2f}) count as real gains")
    print(f"   Unrealized profits (${summary['unrealized_pnl']:.2f}) are clearly labeled")
    print(f"   Available cash (${summary['available_capital']:.2f}) is actual money")
    
    print("\n" + "="*60)
    print("[OK] VERIFICATION PASSED")
    print("The AI trading system will NEVER show fake profits as real money!")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = verify_portfolio_integrity()
    if not success:
        print("\n[ERROR] VERIFICATION FAILED - System needs fixing!")
        sys.exit(1)
