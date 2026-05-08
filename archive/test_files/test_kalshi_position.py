#!/usr/bin/env python3
"""Test Kalshi position sizing based on confidence"""

from engines.day_trading_scanner import DayTradingScanner

def main():
    print("Testing Kalshi position sizing...")
    scanner = DayTradingScanner()
    bankroll = 50.0
    
    # Test different confidence levels for Kalshi bets
    test_cases = [
        (0.70, "Low confidence (70%)"),
        (0.80, "Min threshold (80%)"),
        (0.85, "Medium-high (85%)"),
        (0.90, "High confidence (90%)"),
        (0.95, "Very high (95%)"),
        (0.99, "Maximum (99%)")
    ]
    
    print(f"\nBankroll: ${bankroll}")
    print("\nKalshi bet amounts at different confidence levels:")
    print("-" * 60)
    
    for confidence, description in test_cases:
        risk_pct = scanner.calculate_dynamic_risk(confidence)
        bet_amount = bankroll * risk_pct
        
        print(f"{description}:")
        print(f"  Risk: {risk_pct*100:.1f}% of bankroll = ${bet_amount:.2f}")
        print(f"  Bet: ${bet_amount:.2f} on YES/NO contract")
        print()
    
    # Test with simulation adjustment
    print("Testing simulation adjustment:")
    print("-" * 60)
    ai_confidence = 0.90
    sim_win_rate = 0.40  # Simulation shows lower win rate
    
    print(f"AI Confidence: 90% | Simulation Win Rate: 40%")
    
    # Without simulation
    risk_no_sim = scanner.calculate_dynamic_risk(ai_confidence)
    bet_no_sim = bankroll * risk_no_sim
    print(f"Without simulation: Bet ${bet_no_sim:.2f} ({risk_no_sim*100:.1f}% of bankroll)")
    
    # With simulation (uses lower confidence)
    risk_with_sim = scanner.calculate_dynamic_risk(ai_confidence, sim_win_rate)
    bet_with_sim = bankroll * risk_with_sim
    print(f"With simulation: Bet ${bet_with_sim:.2f} ({risk_with_sim*100:.1f}% of bankroll)")
    print(f"Bet reduced by ${bet_no_sim - bet_with_sim:.2f} due to lower simulation win rate")

if __name__ == "__main__":
    main()
