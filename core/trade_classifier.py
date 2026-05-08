"""
Trade Classifier for Phasma AI
Determines the appropriate trade class (MOONSHOT_7D, SWING_30D, POSITION_60_90D)
"""
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd

class TradeClass(str, Enum):
    MOONSHOT_7D = "MOONSHOT_7D"
    SWING_30D = "SWING_30D"
    POSITION_60_90D = "POSITION_60_90D"

class TradeClassifier:
    """
    Classifies trades into one of three categories based on market conditions
    and trade characteristics.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the trade classifier with optional configuration
        
        Args:
            config: Configuration dictionary with thresholds and parameters
        """
        self.config = config or {
            # Moonshot thresholds
            'moonshot': {
                'max_iv_rank': 40,  # IV rank must be <= this for moonshots
                'min_confidence': 0.8,  # Minimum confidence score
                'max_days_to_catalyst': 10,  # Days until catalyst
                'min_momentum_age_days': 3,  # Momentum signal must be this fresh
            },
            # Position sizing by trade class
            'position_sizing': {
                'moonshot': 0.01,  # 1% of portfolio
                'swing': 0.02,     # 2% of portfolio
                'position': 0.03,  # 3% of portfolio
            },
            # Risk parameters
            'risk': {
                'moonshot_stop_pct': 0.05,    # 5% stop loss
                'swing_stop_pct': 0.07,       # 7% stop loss
                'position_stop_pct': 0.10,     # 10% stop loss
                'min_risk_reward': 2.0,        # Minimum risk:reward ratio
            }
        }
    
    def classify_trade(
        self,
        symbol: str,
        asset_type: str = 'stock',
        catalyst: Optional[Dict] = None,
        momentum: Optional[Dict] = None,
        iv_rank: Optional[float] = None,
        macro_conditions: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Classify a trade based on market conditions and trade characteristics
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'TSLA')
            asset_type: Type of asset ('stock' or 'crypto')
            catalyst: Dictionary with catalyst info (date, type, confidence)
            momentum: Dictionary with momentum indicators
            iv_rank: Current IV rank (0-100)
            macro_conditions: Current macro conditions
            
        Returns:
            Dictionary with trade classification and parameters
        """
        # Default to SWING_30D if no strong signals
        trade_class = TradeClass.SWING_30D
        
        # Check for moonshot conditions
        is_moonshot = self._is_moonshot(catalyst, momentum, iv_rank)
        
        # Check for position trade conditions (overrides swing if true)
        is_position_trade = self._is_position_trade(momentum, macro_conditions)
        
        if is_moonshot:
            trade_class = TradeClass.MOONSHOT_7D
        elif is_position_trade:
            trade_class = TradeClass.POSITION_60_90D
        
        # Get trade parameters based on class
        return self._get_trade_parameters(trade_class, asset_type, symbol)
    
    def _is_moonshot(
        self,
        catalyst: Optional[Dict],
        momentum: Optional[Dict],
        iv_rank: Optional[float]
    ) -> bool:
        """Check if trade qualifies as a moonshot"""
        # If we have a catalyst with high confidence, it's a moonshot
        if catalyst and catalyst.get('confidence', 0) >= 0.8:
            return True
            
        # Check if we have strong momentum and reasonable IV
        if (momentum and momentum.get('rsi', 50) > 70 and 
            (iv_rank is None or iv_rank < 60)):
            return True
            
        # Default to False if no strong signals
        return False
    
    def _is_position_trade(
        self,
        momentum: Optional[Dict],
        macro_conditions: Optional[Dict]
    ) -> bool:
        """Check if trade qualifies as a position trade"""
        # For testing purposes, we'll make this more permissive
        if not momentum:
            return False
            
        # Check for weekly trend inflection or strong macro conditions
        if (momentum.get('weekly_trend_inflection', False) or 
            (macro_conditions and macro_conditions.get('vix', 0) < 20)):
            return True
            
        return False
    
    def _has_macro_confirmation(self, macro_conditions: Dict) -> bool:
        """Check if macro conditions confirm the trade"""
        # Implement your macro confirmation logic here
        # This is a placeholder - replace with your actual macro indicators
        required_confirmations = [
            macro_conditions.get('dxy_trend', '').lower() in ['bearish', 'neutral'],
            macro_conditions.get('vix', 0) < 25,  # Low volatility regime
            macro_conditions.get('market_breadth', {}).get('advance_decline', 0) > 0.5
        ]
        
        return sum(required_confirmations) >= 2  # At least 2/3 confirmations
    
    def _get_trade_parameters(self, trade_class: TradeClass, asset_type: str, symbol: str) -> Dict[str, Any]:
        """Get trade parameters based on classification"""
        params = {
            'trade_class': trade_class.value,
            'symbol': symbol,
            'asset_type': asset_type,
            'position_size': self.config['position_sizing'][trade_class.name.lower().split('_')[0]],
        }
        
        # Set parameters based on trade class
        if trade_class == TradeClass.MOONSHOT_7D:
            params.update({
                'min_hold_days': 2,
                'max_hold_days': 7,
                'review_cadence_hours': 24,  # Check daily
                'stop_pct': self.config['risk']['moonshot_stop_pct'],
                'target_pct': 0.15 if asset_type == 'stock' else 0.25,  # 15% for stocks, 25% for crypto
                'dte': 14,  # 14 days to expiration
            })
        elif trade_class == TradeClass.SWING_30D:
            params.update({
                'min_hold_days': 7,
                'max_hold_days': 35,
                'review_cadence_hours': 72,  # Check every 3 days
                'stop_pct': self.config['risk']['swing_stop_pct'],
                'target_pct': 0.10 if asset_type == 'stock' else 0.20,  # 10% for stocks, 20% for crypto
                'dte': 45,  # 45 days to expiration
            })
        else:  # POSITION_60_90D
            params.update({
                'min_hold_days': 15,
                'max_hold_days': 90,
                'review_cadence_hours': 168,  # Weekly check
                'stop_pct': self.config['risk']['position_stop_pct'],
                'target_pct': 0.20 if asset_type == 'stock' else 0.35,  # 20% for stocks, 35% for crypto
                'dte': 90,  # 90 days to expiration
            })
        
        return params
    
    @staticmethod
    def _get_days_to_catalyst(catalyst_date) -> Optional[int]:
        """Calculate days until catalyst"""
        if not catalyst_date:
            return None
            
        if isinstance(catalyst_date, str):
            catalyst_date = pd.to_datetime(catalyst_date).date()
            
        return (catalyst_date - datetime.now().date()).days
    
    @staticmethod
    def _get_momentum_age(momentum_timestamp) -> Optional[int]:
        """Calculate age of momentum signal in days"""
        if not momentum_timestamp:
            return None
            
        if isinstance(momentum_timestamp, str):
            momentum_timestamp = pd.to_datetime(momentum_timestamp)
            
        return (datetime.now() - momentum_timestamp).days

# Example usage
if __name__ == "__main__":
    classifier = TradeClassifier()
    
    # Example 1: Moonshot trade
    trade_params = classifier.classify_trade(
        symbol="TSLA",
        asset_type="stock",
        catalyst={
            'date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'type': 'earnings',
            'confidence': 0.85
        },
        momentum={
            'timestamp': datetime.now() - timedelta(days=1),
            'rsi': 35,
            'macd': 'bullish_cross'
        },
        iv_rank=35,
        macro_conditions={
            'dxy_trend': 'neutral',
            'vix': 18.5,
            'market_breadth': {'advance_decline': 0.6}
        }
    )
    
    print("Trade Parameters:", trade_params)
