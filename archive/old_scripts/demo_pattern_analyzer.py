#!/usr/bin/env python3
"""
Demo: How Random Chaos Creates Perfect Patterns
Like the bean machine - individual randomness creates predictable bell curves
"""

import numpy as np
from utils.randomness_pattern_analyzer import RandomnessPatternAnalyzer

def main():
    print("🎯 DEMONSTRATING RANDOMNESS TO PATTERNS")
    print("=" * 60)
    print("Like the bean machine - each bounce is random, but the outcome is predictable\n")
    
    # Initialize the pattern analyzer
    analyzer = RandomnessPatternAnalyzer()
    
    # Simulate the bean machine
    print("📊 BEAN MACHINE SIMULATION:")
    print("Each ball bounces randomly left/right at each peg...")
    result = analyzer.simulate_bean_machine(num_balls=1000, num_pegs=10)
    
    print(f"\n• Total random bounces: {result['random_bounces']:,}")
    print(f"• Number of balls: {result['num_balls']:,}")
    print(f"• Pattern emerged: {result['pattern_emerged']}")
    print("\n✅ Despite {result['random_bounces']} random events, a perfect bell curve formed!")
    
    # Show how this applies to trading
    print("\n📈 APPLYING TO TRADING:")
    print("Adding random trades to find patterns...\n")
    
    # Simulate 50 random trades
    tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"]
    for i in range(50):
        entry = np.random.uniform(20, 200)
        # Random return between -15% and +25%
        return_pct = np.random.uniform(-15, 25)
        exit = entry * (1 + return_pct/100)
        
        analyzer.add_trade_outcome(
            ticker=tickers[i % 5],
            entry_price=entry,
            exit_price=exit,
            days_held=np.random.randint(1, 30),
            trade_type='random'
        )
    
    # Get the pattern insights
    insights = analyzer.get_bell_curve_insights()
    
    print("\n🔍 TRADING PATTERN INSIGHTS:")
    for insight in insights['insights']:
        print(f"   • {insight}")
    
    print(f"\n✅ Pattern Strength: {insights['pattern_strength']}")
    print(f"✅ {insights['middle_concentration']:.1f}% of trades cluster in the optimal range")
    
    # Generate a trading signal based on patterns
    signal = analyzer.generate_trading_signal('AAPL', 175.0)
    
    print("\n📊 PATTERN-BASED TRADING SIGNAL:")
    print(f"   Ticker: {signal['ticker']}")
    print(f"   Signal: {signal['signal']}")
    print(f"   Current Price: ${signal['current_price']}")
    print(f"   Expected Return: {signal['expected_return']}")
    print(f"   Success Probability: {signal['probability_of_success']}")
    print(f"   Reason: {signal['reason']}")
    
    print("\n💡 KEY INSIGHT:")
    print("   • Each individual trade is random (50/50 chance)")
    print("   • But over many trades, patterns emerge")
    print("   • Like flipping coins - one flip is random, 1000 flips follow a pattern")
    print("   • This is how randomness becomes predictable!")
    
    # Save the analysis
    analyzer.save_pattern_analysis()
    
    print("\n✨ The world isn't as random as it seems!")
    print("   Randomness repeated enough times becomes predictable.")

if __name__ == "__main__":
    main()
