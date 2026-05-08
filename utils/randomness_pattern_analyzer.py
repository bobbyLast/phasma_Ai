"""
Randomness to Pattern Analyzer
Understanding how random chaos creates predictable patterns
Based on the Central Limit Theorem - individual randomness creates predictable distributions
"""

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json


class RandomnessPatternAnalyzer:
    """
    Analyzes how random trading events create predictable patterns
    Like the bean machine - each bounce is random, but the outcome is predictable
    """
    
    def __init__(self):
        self.trade_history = []
        self.pattern_confidence = {}
        self.distribution_params = {}
        
    def add_trade_outcome(self, ticker: str, entry_price: float, exit_price: float, 
                          days_held: int, trade_type: str):
        """Add a trade outcome to the pattern analysis"""
        
        pct_return = ((exit_price - entry_price) / entry_price) * 100
        
        trade_data = {
            'ticker': ticker,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pct_return': pct_return,
            'days_held': days_held,
            'trade_type': trade_type,
            'timestamp': datetime.now()
        }
        
        self.trade_history.append(trade_data)
        
        # Update pattern analysis every 10 trades
        if len(self.trade_history) % 10 == 0:
            self._analyze_patterns()
    
    def _analyze_patterns(self):
        """Analyze the emerging patterns from random trades"""
        
        if len(self.trade_history) < 20:
            return
        
        returns = [t['pct_return'] for t in self.trade_history]
        
        # Fit normal distribution to returns
        mu, sigma = stats.norm.fit(returns)
        self.distribution_params['mean'] = mu
        self.distribution_params['std'] = sigma
        
        # Calculate pattern confidence
        # Test if returns follow normal distribution (Central Limit Theorem)
        _, p_value = stats.normaltest(returns)
        self.pattern_confidence['normal_distribution'] = p_value
        
        # Calculate probability metrics
        self.pattern_confidence['positive_return_prob'] = len([r for r in returns if r > 0]) / len(returns)
        self.pattern_confidence['high_return_prob'] = len([r for r in returns if r > 10]) / len(returns)
        
        # Find the "sweet spot" - like the middle of the bean machine
        self.pattern_confidence['optimal_range'] = (mu - sigma, mu + sigma)
        
        print(f"\n📊 PATTERN ANALYSIS UPDATE ({len(self.trade_history)} trades):")
        print(f"   Average Return: {mu:.2f}%")
        print(f"   Volatility: {sigma:.2f}%")
        print(f"   Win Rate: {self.pattern_confidence['positive_return_prob']*100:.1f}%")
        print(f"   Pattern Confidence: {(1-p_value)*100:.1f}% (Normal Distribution)")
        print(f"   Optimal Range: {self.pattern_confidence['optimal_range'][0]:.1f}% to {self.pattern_confidence['optimal_range'][1]:.1f}%")
    
    def predict_next_trade_probability(self, expected_return: float) -> Dict:
        """
        Predict probability of achieving certain returns
        Based on the established patterns from random trades
        """
        
        if not self.distribution_params:
            return {'error': 'Insufficient data for prediction'}
        
        mu = self.distribution_params['mean']
        sigma = self.distribution_params['std']
        
        # Calculate Z-score and probability
        z_score = (expected_return - mu) / sigma
        probability = 1 - stats.norm.cdf(z_score)
        
        return {
            'expected_return': expected_return,
            'probability': probability * 100,
            'z_score': z_score,
            'confidence': 'HIGH' if probability > 0.7 else 'MEDIUM' if probability > 0.4 else 'LOW'
        }
    
    def get_bell_curve_insights(self) -> Dict:
        """
        Get insights about the bell curve pattern in trading
        Like the bean machine - most results cluster in the middle
        """
        
        if not self.trade_history:
            return {'error': 'No trade data available'}
        
        returns = [t['pct_return'] for t in self.trade_history]
        
        # Divide returns into thirds (like bean machine bins)
        n = len(returns)
        third = n // 3
        
        sorted_returns = sorted(returns)
        lower_third = sorted_returns[:third]
        middle_third = sorted_returns[third:2*third]
        upper_third = sorted_returns[2*third:]
        
        insights = {
            'total_trades': n,
            'middle_concentration': len(middle_third) / n * 100,
            'pattern_strength': 'STRONG' if len(middle_third) / n > 0.4 else 'MODERATE',
            'insights': [
                f"Like the bean machine, {len(middle_third)}/{n} trades cluster in the middle",
                f"Random individual trades create predictable patterns at scale",
                f"The bell curve emerges from chaos - {len(middle_third)} trades in the optimal range"
            ]
        }
        
        return insights
    
    def simulate_bean_machine(self, num_balls: int = 1000, num_pegs: int = 10) -> Dict:
        """
        Simulate the bean machine to demonstrate randomness creating patterns
        Each ball bounces randomly left/right, but creates a bell curve
        """
        
        # Simulate random bounces
        outcomes = []
        for _ in range(num_balls):
            position = 0
            for _ in range(num_pegs):
                # Random bounce left or right (like coin flip)
                position += np.random.choice([-1, 1])
            outcomes.append(position)
        
        # Analyze the pattern
        counts = {}
        for outcome in outcomes:
            counts[outcome] = counts.get(outcome, 0) + 1
        
        # Calculate probabilities
        probabilities = {k: v/num_balls for k, v in counts.items()}
        
        return {
            'num_balls': num_balls,
            'num_pegs': num_pegs,
            'random_bounces': num_pegs * num_balls,
            'pattern_emerged': True,
            'distribution': probabilities,
            'message': f"Each of {num_balls * num_pegs} bounces was random, yet created a predictable pattern"
        }
    
    def generate_trading_signal(self, ticker: str, current_price: float) -> Dict:
        """
        Generate a trading signal based on pattern recognition
        Understanding that individual trades are random but patterns emerge
        """
        
        if not self.distribution_params:
            return {
                'ticker': ticker,
                'signal': 'HOLD',
                'reason': 'Insufficient pattern data - need more trades',
                'confidence': 0
            }
        
        # Expected return based on historical patterns
        expected_return = self.distribution_params['mean']
        
        # Calculate probability of positive return
        prediction = self.predict_next_trade_probability(5.0)  # 5% target
        
        signal = 'BUY' if prediction['probability'] > 60 else 'HOLD'
        
        return {
            'ticker': ticker,
            'signal': signal,
            'current_price': current_price,
            'expected_return': f"{expected_return:.2f}%",
            'probability_of_success': f"{prediction['probability']:.1f}%",
            'reason': f"Pattern analysis shows {prediction['probability']:.1f}% chance of 5%+ return",
            'pattern_confidence': prediction['confidence'],
            'insight': "Individual trades are random, but patterns emerge at scale"
        }
    
    def save_pattern_analysis(self, filename: str = None):
        """Save the pattern analysis to file"""
        
        if not filename:
            filename = f"pattern_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_trades': len(self.trade_history),
            'distribution_params': self.distribution_params,
            'pattern_confidence': self.pattern_confidence,
            'bell_curve_insights': self.get_bell_curve_insights()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Pattern analysis saved to {filename}")


# Test the analyzer
if __name__ == "__main__":
    analyzer = RandomnessPatternAnalyzer()
    
    print("🎯 RANDOMNESS TO PATTERN ANALYZER")
    print("=" * 50)
    print("Understanding how chaos creates predictable patterns\n")
    
    # Simulate the bean machine
    print("📊 Simulating Bean Machine (Random Bounces → Pattern):")
    result = analyzer.simulate_bean_machine()
    print(f"   {result['message']}")
    print(f"   Most balls end up in the middle - creating a bell curve\n")
    
    # Add some sample trades
    print("📈 Adding random trades to find patterns...")
    for i in range(30):
        entry = np.random.uniform(10, 50)
        # Random return between -10% and +20%
        return_pct = np.random.uniform(-10, 20)
        exit = entry * (1 + return_pct/100)
        
        analyzer.add_trade_outcome(
            ticker=f"STOCK{i%5}",
            entry_price=entry,
            exit_price=exit,
            days_held=np.random.randint(1, 30),
            trade_type='mock'
        )
    
    # Get insights
    insights = analyzer.get_bell_curve_insights()
    print("\n🔍 BELL CURVE INSIGHTS:")
    for insight in insights['insights']:
        print(f"   • {insight}")
    
    print(f"\n✅ Pattern Strength: {insights['pattern_strength']}")
    print(f"✅ Middle Concentration: {insights['middle_concentration']:.1f}%")
    
    # Generate a signal
    signal = analyzer.generate_trading_signal('AAPL', 150.0)
    print(f"\n📊 TRADING SIGNAL for {signal['ticker']}:")
    print(f"   Signal: {signal['signal']}")
    print(f"   Reason: {signal['reason']}")
    print(f"   Expected Return: {signal['expected_return']}")
    print(f"   Insight: {signal['insight']}")
