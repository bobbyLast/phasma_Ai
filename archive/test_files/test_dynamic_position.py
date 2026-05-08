#!/usr/bin/env python3
"""Test dynamic position sizing based on confidence"""

from engines.day_trading_scanner import DayTradingScanner

def main():
    print("Testing dynamic position sizing...")
    scanner = DayTradingScanner()
    bankroll = 50.0
    
    # Test different confidence levels
    test_cases = [
        (0.70, "Low confidence (70%)"),
        (0.80, "Min threshold (80%)"),
        (0.85, "Medium-high (85%)"),
        (0.90, "High confidence (90%)"),
        (0.95, "Very high (95%)"),
        (0.99, "Maximum (99%)")
    ]
    
    # Test with cheaper stock to show position differences
    stock_price = 2.50  # $2.50 stock
    
    print(f"\nBankroll: ${bankroll}")
    print(f"Stock price: ${stock_price}")
    print("\nPosition sizing at different confidence levels:")
    print("-" * 60)
    
    for confidence, description in test_cases:
        position = scanner.calculate_position_size(stock_price, bankroll, confidence)
        risk_pct = scanner.calculate_dynamic_risk(confidence)
        
        print(f"{description}:")
        print(f"  Risk: {risk_pct*100:.1f}% of bankroll = ${bankroll * risk_pct:.2f}")
        print(f"  Shares: {position['shares']} | Cost: ${position['cost']} | Used: {position['bankroll_used_pct']}%")
        print(f"  Max loss: ${position['risk_amount']}")
        print()
    
    # Test with simulation adjustment
    print("Testing simulation adjustment:")
    print("-" * 60)
    ai_confidence = 0.90
    sim_win_rate = 0.40  # Simulation shows lower win rate
    
    print(f"AI Confidence: 90% | Simulation Win Rate: 40%")
    
    # Without simulation
    pos_no_sim = scanner.calculate_position_size(stock_price, bankroll, ai_confidence)
    risk_no_sim = scanner.calculate_dynamic_risk(ai_confidence)
    print(f"Without simulation: Risk = {risk_no_sim*100:.1f}% of bankroll = ${bankroll * risk_no_sim:.2f}")
    print(f"  Position: {pos_no_sim['shares']} shares, {pos_no_sim['bankroll_used_pct']}% of bankroll")
    
    # With simulation (uses lower confidence)
    pos_with_sim = scanner.calculate_position_size(stock_price, bankroll, ai_confidence, sim_win_rate)
    risk_with_sim = scanner.calculate_dynamic_risk(ai_confidence, sim_win_rate)
    print(f"With simulation: Risk = {risk_with_sim*100:.1f}% of bankroll = ${bankroll * risk_with_sim:.2f}")
    print(f"  Position: {pos_with_sim['shares']} shares, {pos_with_sim['bankroll_used_pct']}% of bankroll")
    print(f"Position reduced by {pos_no_sim['shares'] - pos_with_sim['shares']} shares due to lower simulation win rate")
    print(f"Risk reduced from {risk_no_sim*100:.1f}% to {risk_with_sim*100:.1f}% of bankroll")

if __name__ == "__main__":
    main()
