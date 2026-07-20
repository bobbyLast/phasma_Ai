"""
Adaptive Position Sizer - Smart Money Management

Implements dynamic position sizing based on:
- Current portfolio capital and tier
- Risk per trade limits
- Opportunity confidence scoring
- Volatility-adjusted sizing
- Portfolio heat management
- Compounding optimization

Features:
- Capital-based position scaling
- Risk-adjusted sizing algorithms
- Portfolio heat management
- Moon shot special sizing
- Kelly criterion integration
"""

import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class SizingMethod(Enum):
    FIXED_PERCENTAGE = "fixed_percentage"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    KELLY_CRITERION = "kelly_criterion"
    CONFIDENCE_BASED = "confidence_based"
    MOON_SHOT = "moon_shot"

@dataclass
class PositionSize:
    """Position size recommendation"""
    shares: int
    position_value: float
    risk_amount: float
    risk_percent: float
    method: str
    confidence: float
    max_loss: float
    recommended: bool
    
    def to_dict(self) -> Dict:
        return {
            'shares': self.shares,
            'position_value': self.position_value,
            'risk_amount': self.risk_amount,
            'risk_percent': self.risk_percent,
            'method': self.method,
            'confidence': self.confidence,
            'max_loss': self.max_loss,
            'recommended': self.recommended
        }

class AdaptivePositionSizer:
    """
    Adaptive position sizer that adjusts based on portfolio growth and opportunity characteristics
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Sizing parameters
        self.default_risk_per_trade = float(self.config.get('position_sizing', {}).get('risk_per_trade', 0.02))
        self.max_portfolio_heat = float(self.config.get('position_sizing', {}).get('max_portfolio_heat', 0.06))
        self.min_position_size = float(self.config.get('position_sizing', {}).get('min_position_size', 50.0))
        self.max_position_size = float(self.config.get('position_sizing', {}).get('max_position_size', 1000.0))
        
        # Volatility adjustment
        self.volatility_lookback = int(self.config.get('position_sizing', {}).get('volatility_lookback', 20))
        self.volatility_multiplier = float(self.config.get('position_sizing', {}).get('volatility_multiplier', 1.0))
        
        # Confidence scaling
        self.confidence_threshold = float(self.config.get('position_sizing', {}).get('confidence_threshold', 0.6))
        self.moon_shot_multiplier = float(self.config.get('position_sizing', {}).get('moon_shot_multiplier', 1.5))
        
        print("💰 Adaptive Position Sizer initialized")
        print(f"   - Default risk per trade: {self.default_risk_per_trade*100:.1f}%")
        print(f"   - Max portfolio heat: {self.max_portfolio_heat*100:.1f}%")
        print(f"   - Position range: ${self.min_position_size:.0f} - ${self.max_position_size:.0f}")
        print(f"   - Moon shot multiplier: {self.moon_shot_multiplier}x")
    
    def calculate_position_size(self, 
                               symbol: str,
                               current_price: float,
                               portfolio_capital: float,
                               tier_config: Dict,
                               opportunity_data: Dict = None,
                               existing_positions: Dict = None) -> PositionSize:
        """
        Calculate optimal position size based on multiple factors
        
        Args:
            symbol: Stock symbol
            current_price: Current stock price
            portfolio_capital: Current portfolio capital
            tier_config: Current tier configuration
            opportunity_data: Opportunity analysis data (confidence, volatility, etc.)
            existing_positions: Existing positions for heat management
        
        Returns:
            PositionSize recommendation
        """
        try:
            if current_price is None or float(current_price) <= 0:
                return PositionSize(
                    shares=0,
                    position_value=0.0,
                    risk_amount=0.0,
                    risk_percent=0.0,
                    method="skipped_no_price",
                    confidence=0.0,
                    max_loss=0.0,
                    recommended=False,
                )

            # Extract opportunity data
            confidence = opportunity_data.get('confidence', 0.5) if opportunity_data else 0.5
            volatility = opportunity_data.get('volatility', 0.3) if opportunity_data else 0.3
            is_moon_shot = opportunity_data.get('is_moon_shot', False) if opportunity_data else False
            moon_shot_score = opportunity_data.get('moon_shot_score', 0) if opportunity_data else 0
            
            # Calculate portfolio heat (total risk exposure)
            current_heat = self._calculate_portfolio_heat(existing_positions, portfolio_capital)
            
            # Determine sizing method
            sizing_method = self._select_sizing_method(confidence, is_moon_shot, volatility)
            
            # Calculate base position size
            base_position_value = self._calculate_base_position(
                portfolio_capital, tier_config, sizing_method, confidence, volatility
            )
            
            # Apply moon shot multiplier
            if is_moon_shot and moon_shot_score >= 70:
                base_position_value *= self.moon_shot_multiplier
                sizing_method = "moon_shot_enhanced"
            
            # Apply portfolio heat reduction
            if current_heat > 0.8 * self.max_portfolio_heat:
                heat_reduction = 1.0 - (current_heat - 0.8 * self.max_portfolio_heat) / (0.2 * self.max_portfolio_heat)
                base_position_value *= max(heat_reduction, 0.5)
            
            # Apply position size limits
            position_value = max(self.min_position_size, min(base_position_value, self.max_position_size))
            
            # Calculate shares
            shares = int(position_value / current_price)
            actual_position_value = shares * current_price
            
            # Calculate risk amount
            risk_amount = actual_position_value * self.default_risk_per_trade
            risk_percent = (risk_amount / portfolio_capital) * 100
            
            # Calculate maximum loss (stop-loss)
            stop_loss_pct = 0.15 if not is_moon_shot else 0.20  # Higher stop loss for moon shots
            max_loss = actual_position_value * stop_loss_pct
            
            # Determine if recommended
            recommended = (
                confidence >= self.confidence_threshold and
                current_heat < self.max_portfolio_heat and
                actual_position_value >= self.min_position_size
            )
            
            return PositionSize(
                shares=shares,
                position_value=actual_position_value,
                risk_amount=risk_amount,
                risk_percent=risk_percent,
                method=sizing_method,
                confidence=confidence,
                max_loss=max_loss,
                recommended=recommended
            )
            
        except Exception as e:
            print(f"❌ Error calculating position size for {symbol}: {str(e)}")
            # Return conservative default
            return PositionSize(
                shares=1,
                position_value=current_price,
                risk_amount=current_price * 0.02,
                risk_percent=2.0,
                method="conservative_default",
                confidence=0.3,
                max_loss=current_price * 0.15,
                recommended=False
            )
    
    def _select_sizing_method(self, confidence: float, is_moon_shot: bool, 
                            volatility: float) -> str:
        """Select optimal sizing method based on opportunity characteristics"""
        
        if is_moon_shot and confidence >= 0.7:
            return SizingMethod.MOON_SHOT.value
        elif confidence >= 0.8:
            return SizingMethod.CONFIDENCE_BASED.value
        elif volatility > 0.5:
            return SizingMethod.VOLATILITY_ADJUSTED.value
        elif confidence >= 0.6:
            return SizingMethod.KELLY_CRITERION.value
        else:
            return SizingMethod.FIXED_PERCENTAGE.value
    
    def _calculate_base_position(self, portfolio_capital: float, tier_config: Dict,
                               sizing_method: str, confidence: float, 
                               volatility: float) -> float:
        """Calculate base position value using selected method"""
        
        if sizing_method == SizingMethod.FIXED_PERCENTAGE.value:
            return portfolio_capital * tier_config.get('max_position_pct', 0.10)
        
        elif sizing_method == SizingMethod.VOLATILITY_ADJUSTED.value:
            # Reduce size for high volatility
            volatility_factor = max(0.5, 1.0 - (volatility - 0.3) * self.volatility_multiplier)
            base_size = portfolio_capital * tier_config.get('max_position_pct', 0.10)
            return base_size * volatility_factor
        
        elif sizing_method == SizingMethod.KELLY_CRITERION.value:
            # Simplified Kelly: f* = (bp - q) / b
            # where b = odds, p = win probability, q = loss probability
            win_prob = confidence
            avg_win = 2.0  # Assume 2:1 reward:risk
            loss_prob = 1 - win_prob
            
            kelly_fraction = (avg_win * win_prob - loss_prob) / avg_win
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
            
            return portfolio_capital * kelly_fraction
        
        elif sizing_method == SizingMethod.CONFIDENCE_BASED.value:
            # Scale position size by confidence
            confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5x to 1.0x based on confidence
            base_size = portfolio_capital * tier_config.get('max_position_pct', 0.10)
            return base_size * confidence_multiplier
        
        elif sizing_method == SizingMethod.MOON_SHOT.value:
            # Aggressive sizing for moon shots
            return portfolio_capital * 0.15  # 15% max for moon shots
        
        else:
            return portfolio_capital * 0.05  # Conservative 5% default
    
    def _calculate_portfolio_heat(self, existing_positions: Dict, 
                                portfolio_capital: float) -> float:
        """Calculate current portfolio heat (total risk exposure)"""
        
        if not existing_positions or portfolio_capital <= 0:
            return 0.0
        
        total_risk = 0.0
        
        for symbol, position in existing_positions.items():
            position_value = position.get('value', 0)
            position_risk = position.get('risk_amount', position_value * 0.02)
            total_risk += position_risk
        
        return total_risk / portfolio_capital
    
    def get_position_recommendation(self, position_size: PositionSize, 
                                  symbol: str, current_price: float) -> Dict:
        """Get detailed position recommendation"""
        
        recommendation = {
            'action': 'BUY' if position_size.recommended else 'HOLD',
            'symbol': symbol,
            'shares': position_size.shares,
            'position_value': position_size.position_value,
            'entry_price': current_price,
            'risk_amount': position_size.risk_amount,
            'risk_percent': position_size.risk_percent,
            'max_loss': position_size.max_loss,
            'method': position_size.method,
            'confidence': position_size.confidence,
            'stop_loss_price': current_price * 0.85,  # 15% stop loss
            'target_price': current_price * 2.0,      # 2x target
            'risk_reward_ratio': 2.0
        }
        
        # Add moon shot specific targets
        if 'moon_shot' in position_size.method:
            recommendation['target_price'] = current_price * 3.0  # 3x target for moon shots
            recommendation['risk_reward_ratio'] = 3.0
            recommendation['stop_loss_price'] = current_price * 0.80  # 20% stop loss
        
        return recommendation
    
    def calculate_compounding_returns(self, initial_capital: float, 
                                    win_rate: float, avg_win_pct: float,
                                    avg_loss_pct: float, num_trades: int) -> Dict:
        """Calculate compounding returns over time"""
        
        capital = initial_capital
        capital_history = [initial_capital]
        trade_results = []
        
        for trade in range(num_trades):
            # Determine if win or loss
            is_win = trade < (num_trades * win_rate)
            
            if is_win:
                return_pct = avg_win_pct / 100
            else:
                return_pct = -avg_loss_pct / 100
            
            # Calculate position size (2% risk per trade)
            risk_amount = capital * 0.02
            position_value = risk_amount / 0.15  # Assuming 15% stop loss
            
            # Calculate P&L
            pnl = position_value * return_pct
            capital += pnl
            
            capital_history.append(capital)
            trade_results.append({
                'trade': trade + 1,
                'capital': capital,
                'pnl': pnl,
                'return_pct': return_pct * 100,
                'is_win': is_win
            })
        
        total_return = ((capital - initial_capital) / initial_capital) * 100
        
        return {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_return_pct': total_return,
            'total_trades': num_trades,
            'win_rate': win_rate,
            'avg_win_pct': avg_win_pct,
            'avg_loss_pct': avg_loss_pct,
            'capital_history': capital_history,
            'trade_results': trade_results
        }

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Adaptive Position Sizer...")
    
    sizer = AdaptivePositionSizer()
    
    # Test different scenarios
    test_scenarios = [
        {
            'name': 'Small Capital - Penny Stock',
            'capital': 100,
            'price': 2.50,
            'confidence': 0.7,
            'volatility': 0.4,
            'tier_config': {'max_position_pct': 0.20, 'risk_per_trade': 0.02}
        },
        {
            'name': 'Medium Capital - Normal Stock',
            'capital': 2000,
            'price': 25.00,
            'confidence': 0.8,
            'volatility': 0.3,
            'tier_config': {'max_position_pct': 0.10, 'risk_per_trade': 0.015}
        },
        {
            'name': 'Moon Shot Opportunity',
            'capital': 500,
            'price': 3.20,
            'confidence': 0.8,
            'volatility': 0.6,
            'is_moon_shot': True,
            'moon_shot_score': 75,
            'tier_config': {'max_position_pct': 0.15, 'risk_per_trade': 0.02}
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📊 {scenario['name']}:")
        
        opportunity_data = {
            'confidence': scenario['confidence'],
            'volatility': scenario['volatility'],
            'is_moon_shot': scenario.get('is_moon_shot', False),
            'moon_shot_score': scenario.get('moon_shot_score', 0)
        }
        
        position_size = sizer.calculate_position_size(
            symbol='TEST',
            current_price=scenario['price'],
            portfolio_capital=scenario['capital'],
            tier_config=scenario['tier_config'],
            opportunity_data=opportunity_data
        )
        
        recommendation = sizer.get_position_recommendation(
            position_size, 'TEST', scenario['price']
        )
        
        print(f"   Shares: {position_size.shares} | Value: ${position_size.position_value:.2f}")
        print(f"   Risk: ${position_size.risk_amount:.2f} ({position_size.risk_percent:.1f}%)")
        print(f"   Method: {position_size.method} | Recommended: {position_size.recommended}")
        print(f"   Stop Loss: ${recommendation['stop_loss_price']:.2f}")
        print(f"   Target: ${recommendation['target_price']:.2f}")
    
    # Test compounding
    print(f"\n📈 Testing Compounding Returns:")
    compounding = sizer.calculate_compounding_returns(
        initial_capital=50,
        win_rate=0.6,
        avg_win_pct=30,
        avg_loss_pct=15,
        num_trades=20
    )
    
    print(f"   Initial: ${compounding['initial_capital']:.2f}")
    print(f"   Final: ${compounding['final_capital']:.2f}")
    print(f"   Total Return: {compounding['total_return_pct']:+.1f}%")
    
    print(f"\n✅ Adaptive Position Sizer working!")
    print(f"   - Dynamic position sizing implemented")
    print(f"   - Risk management integrated")
    print(f"   - Moon shot sizing configured")
