#!/usr/bin/env python3
"""Test day trading scanner independently"""

from engines.day_trading_scanner import DayTradingScanner

def main():
    print("Testing day trading scanner with position sizing...")
    scanner = DayTradingScanner()
    bankroll = 50.0  # Test with $50 bankroll
    print(f"Bankroll: ${bankroll}")
    signals = scanner.scan_momentum_stocks(limit=30, bankroll=bankroll)
    
    print(f"\nFound {len(signals)} signals:")
    for sig in signals:
        print(f"  {sig['symbol']}: ${sig['entry_price']} - {sig['title']}")
        print(f"    Shares to buy: {sig['shares_to_buy']} | Cost: ${sig['position_cost']} | Risk: ${sig['position_risk']} ({sig['bankroll_used_pct']}% of bankroll)")
    
    # Test simulation on first signal if found
    if signals:
        from engines.monte_carlo_engine import get_monte_carlo_engine
        signal = signals[0]
        
        print(f"\nRunning Monte Carlo simulation for {signal['symbol']}...")
        monte_carlo = get_monte_carlo_engine()
        
        stock_signal = {
            'symbol': signal['symbol'],
            'current_price': signal['entry_price'],
            'target_price': signal['target_price'],
            'stop_loss': signal['entry_price'] * 0.95,
            'confidence': signal['confidence'] / 100,
            'sector': signal['sector'],
            'holding_days': 5
        }
        
        sim_results = monte_carlo.run_stock_simulation(stock_signal)
        
        if sim_results:
            print(f"  Win Rate: {sim_results.get('win_rate', 0):.1%}")
            print(f"  Target: ${sim_results.get('target_price', 0):.2f}")
            print(f"  Stop: ${sim_results.get('stop_loss', 0):.2f}")
            print(f"  Profit Potential: {sim_results.get('profit_potential', 0):.1%}")

if __name__ == "__main__":
    main()
