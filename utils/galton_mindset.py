"""
Galton Mindset Integration
Applies Emergent Order Theory to trading decisions
Helps the AI think in distributions, not certainties
"""

import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional
from core.emergent_order_theory import EmergentOrderTheory, PatternDetector
import json


class GaltonMindset:
    """
    Trading mindset based on Galton board principles
    Thinks probabilistically, recognizes patterns in chaos
    """
    
    def __init__(self):
        self.theory = EmergentOrderTheory()
        self.detector = PatternDetector()
        self.trade_history = []
        self.pattern_insights = {}
        
    def analyze_market_as_galton(self, returns_data: List[float], 
                                 asset_name: str = "Asset") -> Dict:
        """
        Analyze market returns through Galton board lens
        """
        analysis = self.theory.analyze_system_as_galton(returns_data, asset_name)
        
        # Add trading-specific insights
        if 'error' not in analysis:
            # Calculate probability metrics for trading
            positive_return_prob = len([r for r in returns_data if r > 0]) / len(returns_data)
            big_move_prob = len([r for r in returns_data if abs(r) > 0.05]) / len(returns_data)  # 5%+ moves
            
            analysis['trading_insights'] = {
                'win_probability': positive_return_prob * 100,
                'big_move_probability': big_move_prob * 100,
                'expected_range': (analysis['mean'] - 2*analysis['std_dev'], 
                                 analysis['mean'] + 2*analysis['std_dev']),
                'position_sizing_advice': self._get_position_sizing_advice(analysis),
                'risk_warning': self._get_risk_warning(analysis)
            }
        
        return analysis
    
    def _get_position_sizing_advice(self, analysis: Dict) -> str:
        """Generate position sizing advice based on pattern strength"""
        
        strength = analysis.get('pattern_strength', 'WEAK')
        fat_tail = analysis.get('fat_tail_factor', 1.0)
        
        if strength == 'STRONG' and fat_tail < 1.5:
            return "Normal position sizing - patterns are reliable"
        elif strength == 'MODERATE' or fat_tail < 2.0:
            return "Reduce size by 25% - moderate pattern reliability"
        else:
            return "Reduce size by 50% - unpredictable system, fat tails present"
    
    def _get_risk_warning(self, analysis: Dict) -> str:
        """Generate risk warning based on fat tails"""
        
        fat_tail = analysis.get('fat_tail_factor', 1.0)
        
        if fat_tail > 2.0:
            return f"⚠️ EXTREME EVENTS: {fat_tail:.1f}x more common than expected - tight stops required"
        elif fat_tail > 1.5:
            return f"⚠️ BLACK SWANS: {fat_tail:.1f}x more extreme events than normal - hedge positions"
        else:
            return "✅ Normal risk profile - standard risk management applies"
    
    def generate_signal_with_galton_mindset(self, ticker: str, 
                                           historical_returns: List[float],
                                           current_price: float) -> Dict:
        """
        Generate trading signal using Galton board thinking
        """
        # Analyze the pattern
        pattern = self.analyze_market_as_galton(historical_returns, ticker)
        
        if 'error' in pattern:
            return {
                'ticker': ticker,
                'signal': 'HOLD',
                'reason': 'Insufficient data for pattern analysis',
                'confidence': 0
            }
        
        # Calculate probability-based signal
        mean_return = pattern['mean']
        volatility = pattern['std_dev']
        
        # Probability of positive return
        z_score = -mean_return / volatility if volatility > 0 else 0
        prob_positive = stats.norm.cdf(z_score)  # Probability return > 0
        
        # Generate signal
        if prob_positive > 0.60 and pattern['pattern_strength'] == 'STRONG':
            signal = 'BUY'
            confidence = prob_positive * 100
        elif prob_positive < 0.40:
            signal = 'SELL'  # or SHORT
            confidence = (1 - prob_positive) * 100
        else:
            signal = 'HOLD'
            confidence = 50
        
        return {
            'ticker': ticker,
            'signal': signal,
            'current_price': current_price,
            'expected_return': f"{mean_return*100:.2f}%",
            'volatility': f"{volatility*100:.2f}%",
            'success_probability': f"{prob_positive*100:.1f}%",
            'confidence': confidence,
            'pattern_strength': pattern['pattern_strength'],
            'reasoning': f"Based on {len(historical_returns)} data points, {ticker} shows {pattern['pattern_strength'].lower()} Galton patterns",
            'galton_insight': pattern['galton_insight'],
            'risk_warning': pattern['trading_insights']['risk_warning'],
            'position_sizing': pattern['trading_insights']['position_sizing_advice'],
            'mindset': "Thinking in distributions, not certainties"
        }
    
    def add_trade_outcome(self, ticker: str, entry: float, exit: float, 
                         days_held: int, signal: str):
        """Add trade outcome to learn from patterns"""
        
        pct_return = (exit - entry) / entry * 100
        
        trade = {
            'ticker': ticker,
            'entry': entry,
            'exit': exit,
            'pct_return': pct_return,
            'days_held': days_held,
            'signal': signal,
            'timestamp': pd.Timestamp.now()
        }
        
        self.trade_history.append(trade)
        
        # Update pattern insights every 20 trades
        if len(self.trade_history) % 20 == 0:
            self._update_pattern_insights()
    
    def _update_pattern_insights(self):
        """Update insights from trade history"""
        
        if len(self.trade_history) < 20:
            return
        
        returns = [t['pct_return'] for t in self.trade_history]
        
        # Analyze our trading patterns
        analysis = self.analyze_market_as_galton(returns, "Our Trades")
        
        self.pattern_insights = {
            'total_trades': len(self.trade_history),
            'average_return': analysis['mean'],
            'volatility': analysis['std_dev'],
            'win_rate': len([r for r in returns if r > 0]) / len(returns) * 100,
            'pattern_strength': analysis['pattern_strength'],
            'insight': f"Our trading follows {analysis['pattern_strength'].lower()} Galton patterns"
        }
        
        print(f"\n🎯 GALTON MINDSET UPDATE:")
        print(f"   Total Trades: {self.pattern_insights['total_trades']}")
        print(f"   Average Return: {self.pattern_insights['average_return']:.2f}%")
        print(f"   Win Rate: {self.pattern_insights['win_rate']:.1f}%")
        print(f"   Pattern: {self.pattern_insights['pattern_strength']}")
    
    def get_wisdom_for_current_market(self, market_data: Dict) -> str:
        """Get wisdom for current market conditions"""
        
        wisdom = """
        🎯 GALTON MINDSET - MARKET WISDOM:
        
        Remember: The market is a massive Galton board.
        • Each trader's decision = a ball bouncing randomly
        • News, sentiment, algorithms = the pegs
        • Price movements = the bell curve that emerges
        
        TODAY'S INSIGHTS:
        • Don't overreact to single price moves (one ball's path)
        • Trust the statistics (the overall distribution)
        • Most days will be moderate (middle of the bell curve)
        • Extreme days happen but are rare (tails of distribution)
        
        TRADING RULES:
        1. Think in probabilities, not certainties
        2. Size positions based on pattern strength
        3. Expect the mean reversion (bell curve center)
        4. Prepare for fat tails (extreme events)
        
        Remember: Your edge comes from understanding the pattern,
        not from predicting individual bounces.
        """
        
        return wisdom
    
    def explain_decision(self, decision: str, context: Dict) -> str:
        """Explain a decision using Galton board analogy"""
        
        explanations = {
            'BUY': """
            🎯 BUY DECISION - GALTON PERSPECTIVE:
            
            Why I'm buying:
            • Historical data shows strong bell curve pattern
            • Probability of positive return: {prob:.1f}%
            • We're likely seeing mean reversion to the bell curve center
            
            Like betting on balls landing in the middle bins -
            it's not guaranteed, but the odds are in our favor.
            
            Risk management: {sizing}
            """,
            
            'SELL': """
            🎯 SELL DECISION - GALTON PERSPECTIVE:
            
            Why I'm selling:
            • Distribution shows negative bias
            • Probability of further decline: {prob:.1f}%
            • Pattern suggests we're in the left tail
            
            Like seeing too many balls landing left of center -
            the pattern has shifted, we adapt.
            
            Risk management: {sizing}
            """,
            
            'HOLD': """
            🎯 HOLD DECISION - GALTON PERSPECTIVE:
            
            Why I'm holding:
            • Pattern is unclear or weak
            • Probability around 50% - no edge
            • Waiting for clearer pattern emergence
            
            Like watching balls bounce but not yet seeing
            a clear pattern emerge. Patience is wisdom.
            
            Risk management: {sizing}
            """
        }
        
        template = explanations.get(decision, explanations['HOLD'])
        
        return template.format(
            prob=context.get('probability', 50),
            sizing=context.get('sizing', 'Standard position')
        )


# Integration helper
def integrate_galton_mindset(trading_system):
    """Integrate Galton mindset into existing trading system"""
    
    # Create the mindset module
    mindset = GaltonMindset()
    
    # Add to trading system
    trading_system.galton_mindset = mindset
    
    # Override signal generation to use Galton thinking
    original_generate = trading_system.generate_trading_signal
    
    def generate_with_galton_mindset(ticker, data):
        # Get original signal
        original = original_generate(ticker, data)
        
        # Enhance with Galton mindset
        if 'returns_history' in data:
            galton_signal = mindset.generate_signal_with_galton_mindset(
                ticker, data['returns_history'], data.get('current_price', 0)
            )
            
            # Merge insights
            original['galton_insight'] = galton_signal.get('galton_insight', '')
            original['pattern_strength'] = galton_signal.get('pattern_strength', 'UNKNOWN')
            original['mindset'] = galton_signal.get('mindset', '')
        
        return original
    
    trading_system.generate_trading_signal = generate_with_galton_mindset
    
    print("✅ Galton mindset integrated - AI now thinks in distributions")
    
    return mindset


if __name__ == "__main__":
    # Test the Galton mindset
    mindset = GaltonMindset()
    
    print("🎯 TESTING GALTON MINDSET")
    print("=" * 50)
    
    # Generate sample market data
    returns = np.random.normal(0.001, 0.02, 252)  # Daily returns for 1 year
    
    # Analyze as Galton board
    analysis = mindset.analyze_market_as_galton(returns.tolist(), "SPY")
    
    print(f"\nPattern Strength: {analysis['pattern_strength']}")
    print(f"Middle Concentration: {analysis['middle_concentration']:.1f}%")
    print(f"Fat Tail Factor: {analysis['fat_tail_factor']:.2f}")
    
    # Generate signal
    signal = mindset.generate_signal_with_galton_mindset("SPY", returns.tolist(), 450.0)
    
    print(f"\nSignal: {signal['signal']}")
    print(f"Reasoning: {signal['reasoning']}")
    print(f"Mindset: {signal['mindset']}")
    
    # Get wisdom
    print(mindset.get_wisdom_for_current_market({}))
