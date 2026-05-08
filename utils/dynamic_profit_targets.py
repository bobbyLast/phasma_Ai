"""
Dynamic Profit Target Calculator - Predicts maximum potential moves based on catalyst type and sector
Uses historical data to set realistic exit targets for maximum profit
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from .impact_analyzer import get_impact_analyzer

class DynamicProfitTargetCalculator:
    """Calculates dynamic profit targets based on catalyst type, sector, and market conditions"""
    
    def __init__(self):
        # Initialize impact analyzer
        self.impact_analyzer = get_impact_analyzer()
        
        # Historical average moves by catalyst type and sector (based on market research)
        self.catalyst_potential = {
            # Biotechnology catalysts
            'FDA Approval': {
                'biotechnology': {'min': 0.50, 'avg': 1.20, 'max': 3.00},  # 50% to 300%
                'pharmaceuticals': {'min': 0.30, 'avg': 0.80, 'max': 2.00},
                'healthcare': {'min': 0.20, 'avg': 0.50, 'max': 1.50}
            },
            'Clinical Trial Results': {
                'biotechnology': {'min': 0.40, 'avg': 0.90, 'max': 2.50},
                'pharmaceuticals': {'min': 0.25, 'avg': 0.60, 'max': 1.80},
                'healthcare': {'min': 0.15, 'avg': 0.40, 'max': 1.20}
            },
            'Partnership Deal': {
                'technology': {'min': 0.10, 'avg': 0.25, 'max': 0.60},
                'biotechnology': {'min': 0.20, 'avg': 0.50, 'max': 1.20},
                'energy': {'min': 0.15, 'avg': 0.35, 'max': 0.80},
                'industrial': {'min': 0.08, 'avg': 0.20, 'max': 0.50}
            },
            'Earnings Beat': {
                'technology': {'min': 0.05, 'avg': 0.12, 'max': 0.30},
                'finance': {'min': 0.04, 'avg': 0.10, 'max': 0.25},
                'consumer': {'min': 0.03, 'avg': 0.08, 'max': 0.20},
                'industrial': {'min': 0.03, 'avg': 0.07, 'max': 0.18}
            },
            'Product Launch': {
                'technology': {'min': 0.08, 'avg': 0.20, 'max': 0.50},
                'consumer': {'min': 0.05, 'avg': 0.15, 'max': 0.40},
                'healthcare': {'min': 0.06, 'avg': 0.18, 'max': 0.45}
            },
            'Contract Award': {
                'industrial': {'min': 0.05, 'avg': 0.15, 'max': 0.40},
                'technology': {'min': 0.06, 'avg': 0.18, 'max': 0.45},
                'aerospace': {'min': 0.08, 'avg': 0.20, 'max': 0.50},
                'defense': {'min': 0.07, 'avg': 0.18, 'max': 0.45}
            },
            'Merger/Acquisition': {
                'all': {'min': 0.15, 'avg': 0.30, 'max': 0.60}  # Premium typically 15-60%
            },
            'Buyback Announcement': {
                'finance': {'min': 0.02, 'avg': 0.05, 'max': 0.12},
                'technology': {'min': 0.03, 'avg': 0.06, 'max': 0.15},
                'industrial': {'min': 0.02, 'avg': 0.04, 'max': 0.10}
            },
            'Insider Buying': {
                'technology': {'min': 0.05, 'avg': 0.15, 'max': 0.40},
                'biotechnology': {'min': 0.10, 'avg': 0.25, 'max': 0.60},
                'finance': {'min': 0.03, 'avg': 0.08, 'max': 0.20},
                'energy': {'min': 0.04, 'avg': 0.10, 'max': 0.25}
            },
            'Upgrade/Initiation': {
                'all': {'min': 0.02, 'avg': 0.06, 'max': 0.15}
            },
            'Momentum Surge': {
                'technology': {'min': 0.10, 'avg': 0.25, 'max': 0.60},
                'consumer': {'min': 0.08, 'avg': 0.20, 'max': 0.50},
                'biotechnology': {'min': 0.15, 'avg': 0.35, 'max': 0.80}
            },
            'Sector News': {
                'all': {'min': 0.02, 'avg': 0.05, 'max': 0.12}
            },
            'Default': {
                'all': {'min': 0.03, 'avg': 0.08, 'max': 0.20}
            }
        }
        
        # Market cap adjustments
        self.market_cap_multipliers = {
            'small_cap': {'min': 1.2, 'avg': 1.3, 'max': 1.5},  # Small caps move more
            'mid_cap': {'min': 1.0, 'avg': 1.0, 'max': 1.2},
            'large_cap': {'min': 0.8, 'avg': 0.8, 'max': 1.0}  # Large caps move less
        }
        
        # Market condition adjustments
        self.market_condition_adjustments = {
            'bull_market': {'min': 1.2, 'avg': 1.3, 'max': 1.5},
            'normal_market': {'min': 1.0, 'avg': 1.0, 'max': 1.0},
            'bear_market': {'min': 0.7, 'avg': 0.7, 'max': 0.8}
        }
    
    def calculate_profit_targets(self, symbol: str, catalyst_type: str, 
                              current_price: float, confidence: float = 0.7) -> Dict:
        """
        Calculate dynamic profit targets for a stock based on catalyst and market conditions
        
        Returns:
            {
                'quick_target': 0.15,  # 15% - quick profit target
                'realistic_target': 0.35,  # 35% - most likely outcome
                'optimistic_target': 0.80,  # 80% - best case scenario
                'maximum_potential': 1.50,  # 150% - absolute maximum
                'exit_levels': [0.10, 0.25, 0.50, 0.80, 1.20],  # Partial exit levels
                'impact_analysis': {...},  # Current market impact
                'reasoning': 'Based on FDA Approval in biotechnology sector...'
            }
        """
        
        # First analyze current impact to see if catalyst is priced in
        impact_analysis = self.impact_analyzer.analyze_impact(symbol, current_price=current_price)
        
        # Get sector and market cap
        sector = self._get_sector(symbol)
        market_cap_category = self._get_market_cap_category(symbol)
        market_condition = self._get_market_condition()
        
        # Get base potential for this catalyst type and sector
        base_potential = self._get_base_potential(catalyst_type, sector)
        
        # Adjust for market cap
        mc_multiplier = self.market_cap_multipliers.get(market_cap_category, 
                                                      self.market_cap_multipliers['mid_cap'])
        
        # Adjust for market conditions
        market_multiplier = self.market_condition_adjustments.get(market_condition, 
                                                                self.market_condition_adjustments['normal_market'])
        
        # Adjust for confidence level
        confidence_multiplier = 0.7 + (confidence * 0.6)  # 0.7 to 1.3 based on confidence
        
        # Calculate final targets BEFORE impact adjustment
        targets = {}
        for level in ['min', 'avg', 'max']:
            targets[level] = (base_potential[level] * 
                           mc_multiplier[level] * 
                           market_multiplier[level] * 
                           confidence_multiplier)
        
        # Apply impact adjustment - reduce targets if catalyst is already priced in
        remaining_potential = impact_analysis['remaining_potential']
        for level in targets:
            targets[level] *= remaining_potential
        
        # Create structured targets
        quick_target = min(targets['min'], 0.20)  # Cap at 20% for quick profits
        realistic_target = targets['avg']
        optimistic_target = targets['max']
        maximum_potential = targets['max'] * 1.2  # Add 20% buffer for exceptional cases
        
        # Generate exit levels for partial selling
        exit_levels = [
            quick_target * 0.7,  # Early exit at 70% of quick target
            quick_target,
            realistic_target * 0.6,
            realistic_target,
            optimistic_target * 0.8
        ]
        exit_levels = sorted(set([round(x, 3) for x in exit_levels if x > 0]))
        
        # Get ATR for volatility adjustment
        atr_multiplier = self._get_atr_multiplier(symbol)
        
        # Apply ATR adjustment (more volatile stocks get higher targets)
        for key in targets:
            targets[key] *= atr_multiplier
        
        # Build comprehensive reasoning
        reasoning = f"{catalyst_type} in {sector} | {market_cap_category} cap | "
        reasoning += f"Market: {market_condition} | ATR adj: {atr_multiplier:.1f}x | "
        reasoning += f"Impact: {impact_analysis['awareness_level']} ({impact_analysis['pricing_in_pct']*100:.0f}% priced in)"
        
        return {
            'quick_target': round(quick_target, 3),
            'realistic_target': round(realistic_target, 3),
            'optimistic_target': round(optimistic_target, 3),
            'maximum_potential': round(maximum_potential, 3),
            'exit_levels': exit_levels,
            'atr_multiplier': round(atr_multiplier, 2),
            'sector': sector,
            'market_cap_category': market_cap_category,
            'market_condition': market_condition,
            'impact_analysis': impact_analysis,
            'reasoning': reasoning
        }
    
    def _get_sector(self, symbol: str) -> str:
        """Get sector for symbol"""
        sector_map = {
            'AAPL': 'technology', 'MSFT': 'technology', 'GOOGL': 'technology', 'META': 'technology',
            'NVDA': 'technology', 'AMD': 'technology', 'INTC': 'technology', 'CSCO': 'technology',
            'AMZN': 'consumer', 'TSLA': 'consumer', 'DIS': 'consumer', 'NFLX': 'consumer',
            'JPM': 'finance', 'BAC': 'finance', 'WFC': 'finance', 'GS': 'finance',
            'JNJ': 'healthcare', 'PFE': 'healthcare', 'UNH': 'healthcare', 'ABT': 'healthcare',
            'MRK': 'pharmaceuticals', 'ABBV': 'pharmaceuticals', 'BMY': 'pharmaceuticals',
            'BIIB': 'biotechnology', 'GILD': 'biotechnology', 'AMGN': 'biotechnology',
            'XOM': 'energy', 'CVX': 'energy', 'COP': 'energy', 'SLB': 'energy',
            'BA': 'industrial', 'CAT': 'industrial', 'GE': 'industrial', 'MMM': 'industrial',
            'RTX': 'aerospace', 'LMT': 'aerospace', 'NOC': 'aerospace', 'GD': 'defense',
            'HD': 'retail', 'WMT': 'retail', 'COST': 'retail', 'MCD': 'retail',
            'KO': 'consumer', 'PEP': 'consumer', 'PG': 'consumer', 'CL': 'consumer'
        }
        return sector_map.get(symbol.upper(), 'technology')
    
    def _get_market_cap_category(self, symbol: str) -> str:
        """Get market cap category: small_cap, mid_cap, or large_cap"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            market_cap = info.get('marketCap', 0)
            
            if market_cap < 2e9:  # Less than $2B
                return 'small_cap'
            elif market_cap < 10e9:  # Less than $10B
                return 'mid_cap'
            else:
                return 'large_cap'
        except:
            return 'mid_cap'  # Default assumption
    
    def _get_market_condition(self) -> str:
        """Determine current market condition"""
        try:
            # Use S&P 500 as market proxy
            spy = yf.Ticker('SPY')
            hist = spy.history(period="3mo")
            
            if len(hist) < 50:
                return 'normal_market'
            
            # Calculate 50-day SMA
            current_price = hist['Close'][-1]
            sma_50 = hist['Close'].rolling(50).mean()[-1]
            
            # Determine market condition
            if current_price > sma_50 * 1.05:
                return 'bull_market'
            elif current_price < sma_50 * 0.95:
                return 'bear_market'
            else:
                return 'normal_market'
        except:
            return 'normal_market'
    
    def _get_base_potential(self, catalyst_type: str, sector: str) -> Dict:
        """Get base potential for catalyst type and sector"""
        catalyst_data = self.catalyst_potential.get(catalyst_type, 
                                                   self.catalyst_potential['Default'])
        
        if 'all' in catalyst_data:
            return catalyst_data['all']
        elif sector in catalyst_data:
            return catalyst_data[sector]
        else:
            # Find closest sector match
            for key in catalyst_data:
                if sector.lower() in key.lower() or key.lower() in sector.lower():
                    return catalyst_data[key]
            
            # Default to technology sector data
            return catalyst_data.get('technology', self.catalyst_potential['Default']['all'])
    
    def _get_atr_multiplier(self, symbol: str, period: int = 14) -> float:
        """
        Get ATR (Average True Range) multiplier for volatility adjustment
        More volatile stocks get higher multipliers
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{period * 3}d")
            
            if len(hist) < period:
                return 1.0
            
            # Calculate ATR
            high_low = hist['High'] - hist['Low']
            high_close = np.abs(hist['High'] - hist['Close'].shift())
            low_close = np.abs(hist['Low'] - hist['Close'].shift())
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(period).mean().iloc[-1]
            
            # Calculate ATR as percentage of price
            current_price = hist['Close'][-1]
            atr_pct = atr / current_price
            
            # Convert to multiplier (higher volatility = higher multiplier)
            if atr_pct > 0.05:  # >5% daily range = very volatile
                return 1.5
            elif atr_pct > 0.03:  # >3% daily range = volatile
                return 1.3
            elif atr_pct > 0.02:  # >2% daily range = normal
                return 1.1
            else:  # Low volatility
                return 0.9
                
        except:
            return 1.0

# Global instance
_target_calculator = None

def get_target_calculator() -> DynamicProfitTargetCalculator:
    """Get the global target calculator instance"""
    global _target_calculator
    if _target_calculator is None:
        _target_calculator = DynamicProfitTargetCalculator()
    return _target_calculator
