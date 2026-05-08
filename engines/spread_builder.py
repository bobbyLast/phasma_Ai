"""
Spread Builder - Multi-Leg Options Strategies
Implements AI Feedback: Vertical spreads, iron condors, defined-risk strategies
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np

class SpreadBuilder:
    """Build multi-leg options strategies with defined risk"""
    
    SPREAD_TYPES = {
        'BULL_CALL_SPREAD': 'Bullish defined-risk spread',
        'BEAR_PUT_SPREAD': 'Bearish defined-risk spread',
        'BULL_PUT_SPREAD': 'Bullish credit spread',
        'BEAR_CALL_SPREAD': 'Bearish credit spread',
        'IRON_CONDOR': 'Neutral high-probability spread',
        'BUTTERFLY': 'Neutral low-risk spread'
    }
    
    def __init__(self, options_engine=None):
        """Initialize spread builder"""
        self.options_engine = options_engine
        self.logger = logging.getLogger(__name__)
    
    def build_bull_call_spread(
        self, 
        chain: List[Dict], 
        target_pop: float = 0.70,
        buy_delta: float = 0.60,
        sell_delta: float = 0.40
    ) -> Dict:
        """
        Build bull call spread (debit spread)
        Buy lower strike call, sell higher strike call
        
        Args:
            chain: Options chain data
            target_pop: Target probability of profit
            buy_delta: Delta for long leg (default 0.60)
            sell_delta: Delta for short leg (default 0.40)
            
        Returns:
            Complete spread details with risk/reward
        """
        try:
            # Find buy strike (ATM-ish, delta ~0.60)
            buy_strike = self._find_strike_by_delta(chain, buy_delta, 'call')
            
            # Find sell strike (OTM, delta ~0.40)
            sell_strike = self._find_strike_by_delta(chain, sell_delta, 'call')
            
            if not buy_strike or not sell_strike:
                return {'error': 'Unable to find suitable strikes'}
            
            # Calculate costs and profits
            debit_paid = buy_strike['ask'] - sell_strike['bid']  # Net debit
            max_profit = (sell_strike['strike'] - buy_strike['strike']) - debit_paid
            max_loss = debit_paid
            
            # Risk/reward ratio
            risk_reward_ratio = max_profit / max_loss if max_loss > 0 else 0
            
            # Calculate breakeven
            breakeven = buy_strike['strike'] + debit_paid
            
            # Estimate POP (probability of profit)
            pop = self._calculate_spread_pop(buy_strike, sell_strike, 'bull_call')
            
            return {
                'strategy': 'BULL_CALL_SPREAD',
                'type': 'DEBIT_SPREAD',
                'sentiment': 'BULLISH',
                'legs': [
                    {
                        'action': 'BUY',
                        'strike': buy_strike['strike'],
                        'type': 'CALL',
                        'price': buy_strike['ask'],
                        'delta': buy_strike.get('delta', 0.60),
                        'quantity': 1
                    },
                    {
                        'action': 'SELL',
                        'strike': sell_strike['strike'],
                        'type': 'CALL',
                        'price': sell_strike['bid'],
                        'delta': sell_strike.get('delta', 0.40),
                        'quantity': 1
                    }
                ],
                'costs': {
                    'debit_paid': debit_paid,
                    'max_profit': max_profit,
                    'max_loss': max_loss,
                    'breakeven': breakeven
                },
                'metrics': {
                    'risk_reward_ratio': risk_reward_ratio,
                    'pop': pop,
                    'max_profit_pct': (max_profit / max_loss) * 100 if max_loss > 0 else 0
                },
                'status': 'READY'
            }
            
        except Exception as e:
            self.logger.error(f"Error building bull call spread: {e}")
            return {'error': str(e)}
    
    def build_bear_put_spread(
        self, 
        chain: List[Dict], 
        target_pop: float = 0.70,
        buy_delta: float = -0.60,
        sell_delta: float = -0.40
    ) -> Dict:
        """
        Build bear put spread (debit spread)
        Buy higher strike put, sell lower strike put
        """
        try:
            # Find buy strike (ATM-ish, delta ~-0.60)
            buy_strike = self._find_strike_by_delta(chain, abs(buy_delta), 'put')
            
            # Find sell strike (OTM, delta ~-0.40)
            sell_strike = self._find_strike_by_delta(chain, abs(sell_delta), 'put')
            
            if not buy_strike or not sell_strike:
                return {'error': 'Unable to find suitable strikes'}
            
            # Calculate costs and profits
            debit_paid = buy_strike['ask'] - sell_strike['bid']
            max_profit = (buy_strike['strike'] - sell_strike['strike']) - debit_paid
            max_loss = debit_paid
            
            risk_reward_ratio = max_profit / max_loss if max_loss > 0 else 0
            breakeven = buy_strike['strike'] - debit_paid
            pop = self._calculate_spread_pop(buy_strike, sell_strike, 'bear_put')
            
            return {
                'strategy': 'BEAR_PUT_SPREAD',
                'type': 'DEBIT_SPREAD',
                'sentiment': 'BEARISH',
                'legs': [
                    {
                        'action': 'BUY',
                        'strike': buy_strike['strike'],
                        'type': 'PUT',
                        'price': buy_strike['ask'],
                        'delta': buy_strike.get('delta', -0.60),
                        'quantity': 1
                    },
                    {
                        'action': 'SELL',
                        'strike': sell_strike['strike'],
                        'type': 'PUT',
                        'price': sell_strike['bid'],
                        'delta': sell_strike.get('delta', -0.40),
                        'quantity': 1
                    }
                ],
                'costs': {
                    'debit_paid': debit_paid,
                    'max_profit': max_profit,
                    'max_loss': max_loss,
                    'breakeven': breakeven
                },
                'metrics': {
                    'risk_reward_ratio': risk_reward_ratio,
                    'pop': pop,
                    'max_profit_pct': (max_profit / max_loss) * 100 if max_loss > 0 else 0
                },
                'status': 'READY'
            }
            
        except Exception as e:
            self.logger.error(f"Error building bear put spread: {e}")
            return {'error': str(e)}
    
    def build_iron_condor(
        self,
        chain: List[Dict],
        target_pop: float = 0.80,
        wing_width: float = 5.0
    ) -> Dict:
        """
        Build iron condor (credit spread)
        Sell OTM put spread + Sell OTM call spread
        High probability, defined risk
        """
        try:
            # Get current price
            current_price = chain[0].get('underlying_price', 100)
            
            # Find strikes
            # Sell put at delta ~0.20 (below current)
            sell_put = self._find_strike_by_delta(chain, 0.20, 'put')
            # Buy put at delta ~0.10 (further below)
            buy_put = self._find_strike_by_delta(chain, 0.10, 'put')
            
            # Sell call at delta ~0.20 (above current)
            sell_call = self._find_strike_by_delta(chain, 0.20, 'call')
            # Buy call at delta ~0.10 (further above)
            buy_call = self._find_strike_by_delta(chain, 0.10, 'call')
            
            if not all([sell_put, buy_put, sell_call, buy_call]):
                return {'error': 'Unable to find suitable strikes for iron condor'}
            
            # Calculate credits and costs
            put_credit = sell_put['bid'] - buy_put['ask']
            call_credit = sell_call['bid'] - buy_call['ask']
            total_credit = put_credit + call_credit
            
            max_loss = wing_width - total_credit
            
            return {
                'strategy': 'IRON_CONDOR',
                'type': 'CREDIT_SPREAD',
                'sentiment': 'NEUTRAL',
                'legs': [
                    {'action': 'BUY', 'strike': buy_put['strike'], 'type': 'PUT', 'price': buy_put['ask']},
                    {'action': 'SELL', 'strike': sell_put['strike'], 'type': 'PUT', 'price': sell_put['bid']},
                    {'action': 'SELL', 'strike': sell_call['strike'], 'type': 'CALL', 'price': sell_call['bid']},
                    {'action': 'BUY', 'strike': buy_call['strike'], 'type': 'CALL', 'price': buy_call['ask']}
                ],
                'costs': {
                    'credit_received': total_credit,
                    'max_profit': total_credit,
                    'max_loss': max_loss,
                    'breakeven_lower': sell_put['strike'] - total_credit,
                    'breakeven_upper': sell_call['strike'] + total_credit
                },
                'metrics': {
                    'risk_reward_ratio': total_credit / max_loss if max_loss > 0 else 0,
                    'pop': 0.80,  # Typically 80%+ for iron condors
                    'profit_zone': f"{sell_put['strike']:.2f} - {sell_call['strike']:.2f}"
                },
                'status': 'READY'
            }
            
        except Exception as e:
            self.logger.error(f"Error building iron condor: {e}")
            return {'error': str(e)}
    
    def select_best_spread(
        self,
        symbol: str,
        sentiment: str,
        risk_tolerance: str = 'MODERATE'
    ) -> Dict:
        """
        Select optimal spread strategy based on market conditions
        
        Args:
            symbol: Stock ticker
            sentiment: 'BULLISH', 'BEARISH', or 'NEUTRAL'
            risk_tolerance: 'CONSERVATIVE', 'MODERATE', 'AGGRESSIVE'
            
        Returns:
            Recommended spread with details
        """
        recommendations = {
            'BULLISH': {
                'CONSERVATIVE': 'BULL_CALL_SPREAD',
                'MODERATE': 'BULL_CALL_SPREAD',
                'AGGRESSIVE': 'BULL_PUT_SPREAD'
            },
            'BEARISH': {
                'CONSERVATIVE': 'BEAR_PUT_SPREAD',
                'MODERATE': 'BEAR_PUT_SPREAD',
                'AGGRESSIVE': 'BEAR_CALL_SPREAD'
            },
            'NEUTRAL': {
                'CONSERVATIVE': 'IRON_CONDOR',
                'MODERATE': 'IRON_CONDOR',
                'AGGRESSIVE': 'BUTTERFLY'
            }
        }
        
        strategy = recommendations.get(sentiment, {}).get(risk_tolerance, 'BULL_CALL_SPREAD')
        
        return {
            'recommended_strategy': strategy,
            'sentiment': sentiment,
            'risk_tolerance': risk_tolerance,
            'description': self.SPREAD_TYPES.get(strategy, 'Unknown strategy')
        }
    
    def _find_strike_by_delta(
        self, 
        chain: List[Dict], 
        target_delta: float, 
        option_type: str
    ) -> Optional[Dict]:
        """Find strike closest to target delta"""
        if not chain:
            return None
        
        # Filter by option type
        filtered = [opt for opt in chain if opt.get('type', '').lower() == option_type.lower()]
        
        if not filtered:
            return None
        
        # Find closest delta
        best_match = min(
            filtered,
            key=lambda x: abs(abs(x.get('delta', 0)) - abs(target_delta))
        )
        
        return best_match
    
    def _calculate_spread_pop(
        self,
        long_leg: Dict,
        short_leg: Dict,
        spread_type: str
    ) -> float:
        """Calculate probability of profit for spread"""
        # Simplified POP calculation
        # In production, use more sophisticated models
        
        if spread_type in ['bull_call', 'bear_put']:
            # Debit spreads: POP based on delta of short leg
            short_delta = abs(short_leg.get('delta', 0.40))
            return min(0.95, short_delta + 0.20)  # Add 20% buffer
        else:
            # Credit spreads: Higher POP
            return 0.75
    
    def calculate_spread_greeks(self, spread: Dict) -> Dict:
        """Calculate net Greeks for the spread"""
        try:
            net_delta = 0.0
            net_gamma = 0.0
            net_theta = 0.0
            net_vega = 0.0
            
            for leg in spread.get('legs', []):
                multiplier = 1 if leg['action'] == 'BUY' else -1
                
                net_delta += leg.get('delta', 0) * multiplier
                net_gamma += leg.get('gamma', 0) * multiplier
                net_theta += leg.get('theta', 0) * multiplier
                net_vega += leg.get('vega', 0) * multiplier
            
            return {
                'net_delta': net_delta,
                'net_gamma': net_gamma,
                'net_theta': net_theta,
                'net_vega': net_vega
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating spread Greeks: {e}")
            return {}
    
    def print_spread_details(self, spread: Dict):
        """Print formatted spread details"""
        if 'error' in spread:
            print(f"Error: {spread['error']}")
            return
        
        print("\n" + "="*70)
        print(f"SPREAD STRATEGY: {spread['strategy']}")
        print("="*70)
        print(f"Type: {spread['type']}")
        print(f"Sentiment: {spread['sentiment']}")
        
        print("\nLEGS:")
        for i, leg in enumerate(spread['legs'], 1):
            print(f"  {i}. {leg['action']} {leg['type']} @ ${leg['strike']:.2f} for ${leg['price']:.2f}")
        
        costs = spread['costs']
        print("\nCOSTS & PROFITS:")
        if 'debit_paid' in costs:
            print(f"  Debit Paid: ${costs['debit_paid']:.2f}")
        if 'credit_received' in costs:
            print(f"  Credit Received: ${costs['credit_received']:.2f}")
        print(f"  Max Profit: ${costs['max_profit']:.2f}")
        print(f"  Max Loss: ${costs['max_loss']:.2f}")
        if 'breakeven' in costs:
            print(f"  Breakeven: ${costs['breakeven']:.2f}")
        
        metrics = spread['metrics']
        print("\nMETRICS:")
        print(f"  Risk/Reward: {metrics['risk_reward_ratio']:.2f}")
        print(f"  POP: {metrics['pop']:.1%}")
        print(f"  Max Profit %: {metrics.get('max_profit_pct', 0):.1f}%")
        
        print("="*70 + "\n")
