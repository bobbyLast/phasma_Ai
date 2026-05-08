"""
Option Pricing Sources Manager
Handles multiple pricing sources for accuracy and comparison
"""

import yfinance as yf
from typing import Dict, Optional, Tuple
import logging

class PricingSourceManager:
    """
    Manages multiple option pricing sources for accuracy comparison
    Current: yfinance (delayed, free)
    Future: Broker APIs (real-time, authenticated)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_source = "yfinance"
        self.real_time_available = False
        
    def get_option_chain(self, symbol: str, expiry: str) -> Optional[Dict]:
        """
        Get option chain with pricing data
        Returns calls/puts with bid/ask/last/volume
        """
        try:
            stock = yf.Ticker(symbol)
            chain = stock.option_chain(expiry)
            
            # Add pricing metadata
            pricing_info = {
                'source': self.current_source,
                'delay': '15 minutes',
                'timestamp': yf.utils.get_now().isoformat(),
                'data_quality': 'analysis_grade'  # vs 'execution_grade'
            }
            
            return {
                'calls': chain.calls,
                'puts': chain.puts,
                'pricing_info': pricing_info
            }
            
        except Exception as e:
            self.logger.error(f"Error getting option chain for {symbol}: {e}")
            return None
    
    def get_executable_price(self, option_data: Dict, action: str = 'mid') -> float:
        """
        Calculate realistic executable price including spreads
        """
        if action == 'bid':
            return option_data.get('bid', option_data.get('lastPrice', 0))
        elif action == 'ask':
            return option_data.get('ask', option_data.get('lastPrice', 0))
        else:  # mid price
            bid = option_data.get('bid', option_data.get('lastPrice', 0))
            ask = option_data.get('ask', option_data.get('lastPrice', 0))
            return (bid + ask) / 2 if bid and ask else option_data.get('lastPrice', 0)
    
    def calculate_slippage_impact(self, option_data: Dict, position_size: float) -> Dict:
        """
        Calculate realistic slippage impact on execution
        """
        mid_price = self.get_executable_price(option_data, 'mid')
        ask_price = self.get_executable_price(option_data, 'ask')
        
        if mid_price and ask_price:
            spread_pct = (ask_price - mid_price) / mid_price * 100
            slippage_cost = (ask_price - mid_price) * position_size / 100  # per contract
            
            return {
                'spread_percentage': spread_pct,
                'slippage_cost_per_contract': slippage_cost,
                'realistic_entry_price': ask_price,
                'data_source': self.current_source,
                'execution_reality': 'paper_trading_estimate'
            }
        
        return {'error': 'Insufficient price data for slippage calculation'}
    
    def get_pricing_summary(self) -> Dict:
        """
        Get current pricing source status and recommendations
        """
        return {
            'current_source': self.current_source,
            'data_delay': '15 minutes',
            'accuracy_level': 'Analysis Grade (not execution ready)',
            'cost': 'Free',
            'recommended_for': ['Strategy development', 'Paper trading', 'Backtesting'],
            'not_recommended_for': ['Live execution', 'Day trading', 'High frequency'],
            'upgrade_path': {
                'live_trading': 'TD Ameritrade/IBKR/Schwab API integration',
                'real_time': 'Broker data subscription required',
                'cost_estimate': '$0-50/month depending on broker'
            }
        }

# Global pricing manager instance
pricing_manager = PricingSourceManager()
