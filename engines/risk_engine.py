"""
Phasma Risk Management Engine
Greeks-aware position sizing and dynamic risk controls
"""

import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

class PhasmaRiskEngine:
    """Advanced risk management with Greeks-aware position sizing"""

    def __init__(self, config):
        self.config = config
        self.bankroll = getattr(config, 'bankroll', 2000) or (config.get('bankroll') if hasattr(config, 'get') else 2000)
        self.max_risk_per_trade = getattr(config, 'risk_per_trade', 0.01) or (config.get('risk_per_trade') if hasattr(config, 'get') else 0.01)  # 1% default
        self.max_total_risk = getattr(config, 'max_total_risk', 0.05) or (config.get('max_total_risk') if hasattr(config, 'get') else 0.05)  # 5% total portfolio risk

        # Greeks exposure limits
        self.greeks_limits = {
            'max_delta_exposure': 0.1,  # 10% of bankroll
            'max_vega_exposure': 0.05,  # 5% of bankroll
            'max_theta_exposure': 0.03,  # 3% of bankroll
            'max_gamma_exposure': 0.02   # 2% of bankroll
        }

        # Current portfolio state
        self.current_positions = []
        self.total_delta_exposure = 0.0
        self.total_vega_exposure = 0.0
        self.total_theta_exposure = 0.0

        self.logger = logging.getLogger("PhasmaRiskEngine")

    def calculate_greeks_aware_position_size(self, signal: Dict, option_data: Optional[Dict] = None) -> float:
        """Calculate position size based on Greeks exposure and risk management"""

        # Base position size calculation
        base_size = self.calculate_base_position_size(signal)

        # Greeks-aware adjustments
        if option_data and 'greeks' in option_data:
            greeks = option_data['greeks']

            # Delta adjustment (directional exposure)
            delta = greeks.get('delta', 0.5)
            delta_adjustment = 1.0 - abs(delta - 0.5) * 0.8  # Reduce size for extreme deltas
            if abs(delta) > 0.8:
                delta_adjustment *= 0.7  # Further reduce for very high delta
            
            # Theta decay adjustment (NEW - AI Feedback Task 3)
            theta_adjustment = self.calculate_theta_adjustment(option_data)
            
            # Combine all adjustments
            base_size *= delta_adjustment * theta_adjustment

            # Vega adjustment (volatility exposure) - ENHANCED
            vega_adjustment = self.calculate_vega_adjustment(option_data, greeks)

            # Theta adjustment (time decay)
            dte = signal.get('dte', signal.get('days_to_expiry', 14))
            theta_adjustment = max(0.5, min(1.5, 21 / dte))  # Favor longer DTE
            if dte < 7:
                theta_adjustment *= 0.8  # Reduce size for very short DTE

            # Apply Greeks adjustments
            adjusted_size = base_size * delta_adjustment * vega_adjustment * theta_adjustment

            vega = greeks.get('vega', 0.0)
            self.logger.info(f"Greeks adjustments: Δ={delta:.2f}({delta_adjustment:.2f}x), "
                           f"ν={vega:.3f}({vega_adjustment:.2f}x), θ-dte={dte}({theta_adjustment:.2f}x)")

        else:
            # No Greeks data, use conservative sizing
            adjusted_size = base_size * 0.7
            self.logger.warning("No Greeks data available, using conservative sizing")

        # Portfolio risk check
        total_exposure = sum(pos['position_size'] for pos in self.current_positions)
        max_exposure = self.bankroll * self.max_total_risk

        if total_exposure + adjusted_size > max_exposure:
            # Scale down to fit within limits
            available_risk = max_exposure - total_exposure
            if available_risk > 0:
                adjusted_size = min(adjusted_size, available_risk)
            else:
                adjusted_size = 0
                self.logger.warning("Portfolio at max risk capacity, rejecting new position")

        return max(adjusted_size, 0)

    def calculate_base_position_size(self, signal: Dict) -> float:
        """Calculate base position size before Greeks adjustments"""
        confidence = signal.get('confidence', 0.5)
        is_moonshot = signal.get('is_moonshot', False)

        # Base risk amount
        base_risk = self.bankroll * self.max_risk_per_trade

        # Confidence multiplier (realistic scaling)
        if confidence > 0.8:
            confidence_multiplier = 1.2  # 20% increase for high confidence
        elif confidence > 0.6:
            confidence_multiplier = 1.0  # No change for good confidence
        elif confidence > 0.4:
            confidence_multiplier = 0.8  # 20% reduction for moderate confidence
        else:
            confidence_multiplier = 0.6  # 40% reduction for low confidence

        # Moonshot adjustment (reduced from doubling)
        if is_moonshot:
            confidence_multiplier *= 1.3  # 30% increase for moonshots (vs previous doubling)

        # Company validation bonus
        fact_check = signal.get('fact_check', {})
        validation_score = fact_check.get('validation_score', 0.5)
        validation_multiplier = 1.0 + (validation_score - 0.5) * 0.4  # Up to 20% bonus for high validation

        position_size = base_risk * confidence_multiplier * validation_multiplier

        # Cap at maximum allowed
        max_position = self.bankroll * (self.max_risk_per_trade * 3)  # Max 3x normal risk
        position_size = min(position_size, max_position)

        return position_size

    def check_portfolio_greeks_limits(self, proposed_greeks: Dict) -> bool:
        """Check if adding position would exceed Greeks exposure limits"""
        if not proposed_greeks:
            return True  # No Greeks data, allow trade

        proposed_delta = proposed_greeks.get('delta', 0)
        proposed_vega = proposed_greeks.get('vega', 0)
        proposed_theta = proposed_greeks.get('theta', 0)

        # Calculate new total exposures
        new_delta = self.total_delta_exposure + proposed_delta
        new_vega = self.total_vega_exposure + abs(proposed_vega)
        new_theta = self.total_theta_exposure + abs(proposed_theta)

        # Check limits
        delta_limit = self.greeks_limits['max_delta_exposure'] * self.bankroll
        vega_limit = self.greeks_limits['max_vega_exposure'] * self.bankroll
        theta_limit = self.greeks_limits['max_theta_exposure'] * self.bankroll

        within_limits = (
            abs(new_delta) <= delta_limit and
            new_vega <= vega_limit and
            new_theta <= theta_limit
        )

        if not within_limits:
            self.logger.warning(f"Greeks limits exceeded: Δ={new_delta:.2f}/{delta_limit:.2f}, "
                              f"ν={new_vega:.2f}/{vega_limit:.2f}, θ={new_theta:.2f}/{theta_limit:.2f}")

        return within_limits

    def update_portfolio_exposure(self, signal: Dict, option_data: Optional[Dict] = None) -> None:
        """Update portfolio exposure tracking"""
        if option_data and 'greeks' in option_data:
            greeks = option_data['greeks']

            # Update totals
            self.total_delta_exposure += greeks.get('delta', 0)
            self.total_vega_exposure += abs(greeks.get('vega', 0))
            self.total_theta_exposure += abs(greeks.get('theta', 0))

        # Add to current positions
        self.current_positions.append({
            'symbol': signal.get('symbol', ''),
            'position_size': signal.get('position_size', 0),
            'timestamp': datetime.now(),
            'signal': signal
        })

        # Keep only recent positions (last 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        self.current_positions = [
            pos for pos in self.current_positions
            if pos['timestamp'] > cutoff_date
        ]

    def get_dynamic_risk_limits(self) -> Dict[str, float]:
        """Get dynamic risk limits based on current market conditions"""
        # This would integrate with market regime detection
        # For now, return static limits
        return {
            'max_risk_per_trade': self.max_risk_per_trade,
            'max_total_risk': self.max_total_risk,
            'delta_limit': self.greeks_limits['max_delta_exposure'] * self.bankroll,
            'vega_limit': self.greeks_limits['max_vega_exposure'] * self.bankroll,
            'theta_limit': self.greeks_limits['max_theta_exposure'] * self.bankroll
        }

    def calculate_var(self, confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk for current portfolio"""
        if not self.current_positions:
            return 0.0

        # Simplified VaR calculation based on position sizes
        total_exposure = sum(pos['position_size'] for pos in self.current_positions)

        # Assume 20% volatility for options portfolio
        portfolio_volatility = 0.20

        # Calculate VaR using normal distribution
        z_score = 1.645 if confidence_level == 0.95 else 2.326  # 95% or 99%
        var = total_exposure * portfolio_volatility * z_score

        return var

    def should_reduce_exposure(self) -> bool:
        """Check if portfolio should reduce exposure"""
        current_var = self.calculate_var()
        max_var = self.bankroll * 0.1  # Max 10% VaR

        if current_var > max_var:
            return True

        # Check consecutive losses
        recent_positions = [pos for pos in self.current_positions[-10:]]  # Last 10 trades
        if len(recent_positions) >= 5:
            # Check if last 5 trades were losses (simplified)
            losses = sum(1 for pos in recent_positions if pos.get('pnl', 0) < 0)
            if losses >= 4:  # 4 out of 5 losses
                return True

        return False

    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        total_exposure = sum(pos['position_size'] for pos in self.current_positions)

        return {
            'total_positions': len(self.current_positions),
            'total_exposure': total_exposure,
            'bankroll': self.bankroll,
            'exposure_ratio': total_exposure / self.bankroll if self.bankroll > 0 else 0,
            'delta_exposure': self.total_delta_exposure,
            'vega_exposure': self.total_vega_exposure,
            'theta_exposure': self.total_theta_exposure,
            'var_95': self.calculate_var(0.95),
            'var_99': self.calculate_var(0.99),
            'should_reduce_exposure': self.should_reduce_exposure(),
            'remaining_risk_capacity': (self.bankroll * self.max_total_risk) - total_exposure
        }
    
    def calculate_theta_adjustment(self, option_data: Dict) -> float:
        """
        Calculate position size adjustment based on theta decay
        AI Feedback Task 3: Account for time decay in position sizing
        
        Args:
            option_data: Dictionary containing option Greeks and DTE
            
        Returns:
            Adjustment factor (0.5 to 1.5)
        """
        # Get theta (daily decay) and days to expiration
        theta = abs(option_data.get('greeks', {}).get('theta', 0.0))
        dte = option_data.get('dte', option_data.get('days_to_expiry', 30))
        
        # Base adjustment for days to expiration
        # Prefer trades with 21+ days (3+ weeks)
        dte_adjustment = max(0.5, min(1.5, dte / 21))
        
        # Additional adjustment for high theta decay
        # If theta > $0.10/day, reduce size
        if theta > 0.10:  # Significant daily decay
            theta_adjustment = 0.8
        elif theta > 0.05:  # Moderate decay
            theta_adjustment = 0.9
        else:  # Low decay
            theta_adjustment = 1.0
        
        # Combine adjustments
        total_adjustment = dte_adjustment * theta_adjustment
        
        # Ensure within reasonable bounds
        return max(0.5, min(1.5, total_adjustment))
    
    def calculate_vega_adjustment(self, option_data: Dict, greeks: Dict) -> float:
        """
        Calculate position size adjustment based on vega exposure
        AI Feedback Task 8: Account for IV risk in position sizing
        
        Args:
            option_data: Dictionary containing option details
            greeks: Dictionary containing Greeks values
            
        Returns:
            Adjustment factor (0.5 to 1.0)
        """
        vega = greeks.get('vega', 0.0)
        iv = option_data.get('implied_volatility', option_data.get('iv', 0.30))
        iv_rank = option_data.get('iv_rank', 50)  # 0-100 percentile
        
        # Base vega adjustment
        # High vega = high sensitivity to IV changes = reduce size
        if vega > 0.15:  # Very high vega
            vega_adjustment = 0.7
        elif vega > 0.10:  # High vega
            vega_adjustment = 0.85
        else:  # Normal vega
            vega_adjustment = 1.0
        
        # IV rank adjustment
        # High IV rank = elevated IV = potential crush risk
        if iv_rank > 75:  # Very high IV environment
            iv_adjustment = 0.8
        elif iv_rank > 50:  # Above average IV
            iv_adjustment = 0.9
        else:  # Normal or low IV
            iv_adjustment = 1.0
        
        # Combined adjustment
        total_adjustment = vega_adjustment * iv_adjustment
        
        # Ensure within bounds
        return max(0.5, min(1.0, total_adjustment))
