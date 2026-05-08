#!/usr/bin/env python3
"""
Test Paper Trading Integration
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.paper_trading_portfolio import get_paper_trading_portfolio
from core.config import PhasmaConfig

def test_paper_trading():
    """Test paper trading functionality"""
    
    print("🧪 Testing Paper Trading System")
    print("="*50)
    
    # Load config
    config = PhasmaConfig()
    
    # Create a dict with paper trading settings
    paper_config = {
        'paper_trading': {
            'enabled': True,
            'starting_capital': 10000,
            'track_ai_performance': True,
            'auto_trade_signals': True,
            'min_confidence_threshold': 70,
            'max_position_size': 1000,
            'max_positions': 10
        }
    }
    
    # Update config with paper trading settings
    config.update(paper_config)
    
    # Get portfolio
    portfolio = get_paper_trading_portfolio(config)
    
    print(f"✅ Paper trading portfolio initialized")
    print(f"   Starting Capital: ${portfolio.state['starting_capital']:,.2f}")
    print(f"   Available Capital: ${portfolio.state['available_capital']:,.2f}")
    
    # Test a buy trade
    print("\n📊 Testing Buy Trade...")
    signal_data = {
        'symbol': 'AAPL',
        'action': 'BUY',
        'confidence': 85,
        'entry_price': 150.0,
        'source': 'test_signal'
    }
    
    result = portfolio.execute_buy(
        symbol='AAPL',
        quantity=10,
        price=150.0,
        signal_data=signal_data,
        confidence=85
    )
    
    if result['success']:
        print(f"✅ Buy executed: {result['quantity']} shares of {result['symbol']} at ${result['price']:.2f}")
        print(f"   Total Cost: ${result['total_cost']:.2f}")
        print(f"   Remaining Capital: ${result['remaining_capital']:.2f}")
    else:
        print(f"❌ Buy failed: {result['error']}")
    
    # Test a sell trade
    print("\n📊 Testing Sell Trade...")
    result = portfolio.execute_sell(
        symbol='AAPL',
        quantity=5,
        price=155.0,
        reason='Take profit'
    )
    
    if result['success']:
        print(f"✅ Sell executed: {result['quantity']} shares of {result['symbol']} at ${result['price']:.2f}")
        print(f"   Proceeds: ${result['proceeds']:.2f}")
        print(f"   Realized P&L: ${result['realized_pnl']:.2f}")
    else:
        print(f"❌ Sell failed: {result['error']}")
    
    # Get portfolio summary
    print("\n📈 Portfolio Summary:")
    summary = portfolio.get_portfolio_summary()
    print(f"   Total Value: ${summary['total_portfolio_value']:,.2f}")
    print(f"   Total Return: ${summary['total_return']:,.2f} ({summary['total_return_pct']:+.2f}%)")
    print(f"   Total Trades: {summary['total_trades']}")
    print(f"   Win Rate: {summary['win_rate']:.1f}%")
    
    # Test AI performance tracking
    print("\n🧠 AI Performance Analysis:")
    ai_perf = summary['ai_performance']
    print(f"   Avg Confidence: {ai_perf['avg_confidence']:.1f}%")
    print(f"   High Confidence Win Rate: {ai_perf['high_confidence_win_rate']:.1f}%")
    
    print("\n✅ Paper trading test completed successfully!")
    print("\nTo run the dashboard: python paper_trading_dashboard.py")
    print("To start the system with paper trading: python main.py --monitor")

if __name__ == "__main__":
    test_paper_trading()
