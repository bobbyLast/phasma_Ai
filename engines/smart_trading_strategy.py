#!/usr/bin/env python3
"""
Smart Trading Strategy Selector
Adjusts trading approach based on market hours and conditions
"""

from datetime import datetime, timedelta
from typing import List, Dict
import pytz
from engines.market_hours_detector import MarketHoursDetector
from engines.undervalued_stock_scanner import UndervaluedStockScanner

class SmartTradingStrategy:
    """Intelligently selects trading strategies based on market conditions"""
    
    def __init__(self, config):
        self.config = config
        self.market_hours = MarketHoursDetector()
        self.value_scanner = UndervaluedStockScanner()
        self.current_strategy = None
        self.last_strategy_update = None
        
    def get_recommended_strategy(self, dt=None):
        """Get the recommended trading strategy based on current conditions"""
        market_status = self.market_hours.get_market_status(dt)
        
        # Base strategy on market hours
        if market_status['is_market_open']:
            # Market is open - can do shorter term trades
            return {
                'strategy': 'SWING_TRADING',
                'timeframe': 'hours_to_days',
                'hold_period': '1-5 days',
                'focus': 'momentum + technicals',
                'risk_level': 'medium',
                'reason': 'Market open - swing trading optimal'
            }
        elif market_status['is_pre_market']:
            # Pre-market - prepare for opening
            return {
                'strategy': 'PREPARE_FOR_OPEN',
                'timeframe': 'minutes',
                'hold_period': 'ready at open',
                'focus': 'gap analysis, news catalysts',
                'risk_level': 'high',
                'reason': 'Pre-market - prepare for opening bell'
            }
        elif market_status['is_after_hours']:
            # After hours - analyze for tomorrow
            return {
                'strategy': 'AFTER_HOURS_ANALYSIS',
                'timeframe': 'daily',
                'hold_period': 'next day',
                'focus': 'earnings, news flow',
                'risk_level': 'medium',
                'reason': 'After hours - research for tomorrow'
            }
        else:
            # Market closed - focus on long-term investments
            return {
                'strategy': 'INVESTING',
                'timeframe': 'weeks_to_months',
                'hold_period': 'weeks+',
                'focus': 'fundamentals, value, growth',
                'risk_level': 'low_to_medium',
                'reason': 'Market closed - focus on investments'
            }
    
    def find_value_opportunities(self, limit: int = 5) -> List[Dict]:
        """Find undervalued stocks for long-term investing"""
        market_status = self.market_hours.get_market_status()
        
        # Only scan for value stocks when market is closed or during analysis time
        if market_status['recommended_strategy'] not in ['INVESTING', 'AFTER_HOURS_ANALYSIS']:
            return []
        
        print("\n🔍 MARKET CLOSED - SCANNING FOR UNDERVALUED STOCKS...")
        undervalued = self.value_scanner.find_undervalued_stocks(min_score=60)
        
        # Return top opportunities
        return undervalued[:limit]
    
    def get_investment_recommendations(self) -> List[Dict]:
        """Get investment recommendations for when markets are closed"""
        opportunities = self.find_value_opportunities()
        recommendations = []
        
        for stock in opportunities:
            # Create investment recommendation
            rec = {
                'symbol': stock['symbol'],
                'name': stock['name'],
                'action': 'BUY',
                'type': 'VALUE_INVESTMENT',
                'price': stock['price'],
                'value_score': stock['value_score'],
                'confidence': min(90, 60 + stock['value_score'] * 0.3),  # Base confidence on value score
                'holding_period': '3-12 months',
                'thesis': self.value_scanner.get_investment_thesis(stock),
                'metrics': {
                    'pe_ratio': stock.get('pe_ratio'),
                    'pb_ratio': stock.get('pb_ratio'),
                    'roe': stock.get('roe'),
                    'dividend_yield': stock.get('dividend_yield'),
                    'debt_to_equity': stock.get('debt_to_equity')
                },
                'risk_level': 'LOW_TO_MEDIUM',
                'reason': f"Undervalued with score {stock['value_score']:.0f}/100"
            }
            recommendations.append(rec)
        
        return recommendations
    
    def should_day_trade(self, dt=None):
        """Determine if day trading is appropriate"""
        market_status = self.market_hours.get_market_status(dt)
        
        # Only day trade if:
        # 1. Market is open
        # 2. High volatility expected
        # 3. Sufficient volume
        
        if not market_status['is_market_open']:
            return False, "Market is closed"
        
        # Add more conditions here:
        # - Check VIX for volatility
        # - Check volume indicators
        # - Check for news catalysts
        
        return True, "Market conditions suitable for day trading"
    
    def adjust_signals_for_market_hours(self, signals):
        """Adjust signals based on market hours"""
        if not signals:
            return signals
        
        strategy = self.get_recommended_strategy()
        adjusted_signals = []
        
        for signal in signals:
            # Skip day trading signals if market is closed
            if strategy['strategy'] == 'INVESTING':
                # Filter out very short-term signals
                if hasattr(signal, 'timeframe') and signal.timeframe in ['1m', '5m', '15m']:
                    continue
                # Adjust confidence for longer-term
                if hasattr(signal, 'confidence'):
                    signal.confidence *= 0.9  # Slightly lower confidence for longer-term
            
            # For swing trading, allow medium-term signals
            elif strategy['strategy'] == 'SWING_TRADING':
                if hasattr(signal, 'timeframe') and signal.timeframe in ['1m', '5m']:
                    continue  # Skip very short-term
            
            adjusted_signals.append(signal)
        
        return adjusted_signals
    
    def get_position_sizing_rules(self):
        """Get position sizing rules based on current strategy"""
        strategy = self.get_recommended_strategy()
        
        if strategy['strategy'] == 'INVESTING':
            return {
                'max_positions': 10,
                'position_size_percent': 0.1,  # 10% per position
                'risk_per_trade': 0.02,  # 2% risk
                'holding_period': 'weeks+'
            }
        elif strategy['strategy'] == 'SWING_TRADING':
            return {
                'max_positions': 5,
                'position_size_percent': 0.15,  # 15% per position
                'risk_per_trade': 0.03,  # 3% risk
                'holding_period': '1-5 days'
            }
        else:
            # Conservative default
            return {
                'max_positions': 3,
                'position_size_percent': 0.05,
                'risk_per_trade': 0.01,
                'holding_period': 'intraday'
            }

# Example usage in main.py:
"""
# In PhasmaTradingSystem.__init__:
self.smart_strategy = SmartTradingStrategy(self.config)

# In signal processing:
signals = self.smart_strategy.adjust_signals_for_market_hours(raw_signals)

# In position sizing:
sizing_rules = self.smart_strategy.get_position_sizing_rules()
"""
