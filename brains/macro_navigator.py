"""
Macro Navigator - Mind 1 of the Three-Mind Trading Framework

Decides where the wind is blowing and which seas to fish in.
Provides regime-aware context for all trading decisions.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class RegimeState:
    """Current market regime classification"""
    name: str
    risk_on_off: str  # RISK_ON, RISK_OFF, NEUTRAL
    volatility_regime: str  # LOW, NORMAL, HIGH, EXTREME
    trend_bias: str  # BULLISH, BEARISH, SIDEWAYS
    preferred_strategies: List[str]
    position_size_multiplier: float
    confidence: float


class MacroNavigator:
    """Mind 1: Analyzes macro context and market regimes"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.regime_history = []
        self.current_regime = None
        
        # Macro indicators to track
        self.macro_weights = {
            'vix': 0.25,  # Fear index
            'dxy': 0.15,  # Dollar strength
            'rates': 0.20,  # Interest rate expectations
            'inflation': 0.15,  # Inflation data
            'growth': 0.15,  # Growth indicators
            'liquidity': 0.10  # Fed balance sheet, credit spreads
        }
        
    def analyze_regime(self, market_data: Dict) -> RegimeState:
        """Analyze current market regime"""
        
        # Calculate regime score
        regime_score = self._calculate_regime_score(market_data)
        
        # Determine risk on/off
        risk_on_off = self._determine_risk_sentiment(regime_score)
        
        # Classify volatility regime
        vol_regime = self._classify_volatility(market_data.get('vix', 20))
        
        # Determine trend bias
        trend_bias = self._determine_trend_bias(market_data)
        
        # Select preferred strategies for this regime
        preferred_strategies = self._select_strategies(
            risk_on_off, vol_regime, trend_bias
        )
        
        # Position size adjustment based on regime hostility
        size_multiplier = self._calculate_size_multiplier(
            risk_on_off, vol_regime, regime_score
        )
        
        self.current_regime = RegimeState(
            name=self._generate_regime_name(regime_score),
            risk_on_off=risk_on_off,
            volatility_regime=vol_regime,
            trend_bias=trend_bias,
            preferred_strategies=preferred_strategies,
            position_size_multiplier=size_multiplier,
            confidence=abs(regime_score)
        )
        
        return self.current_regime
    
    def _calculate_regime_score(self, data: Dict) -> float:
        """Calculate composite regime score (-1 to 1, where positive = bullish)"""
        score = 0.0
        
        # VIX component (inverted - low VIX is bullish)
        vix = data.get('vix', 20)
        vix_signal = np.clip((30 - vix) / 20, -1, 1)
        score += vix_signal * self.macro_weights['vix']
        
        # Dollar component (inverted for risk assets)
        dxy = data.get('dxy', 100)
        dxy_signal = np.clip((100 - dxy) / 20, -1, 1)
        score += dxy_signal * self.macro_weights['dxy']
        
        # Rates component
        rates = data.get('rate_expectations', 0.5)
        rates_signal = np.clip((0.5 - rates), -1, 1)
        score += rates_signal * self.macro_weights['rates']
        
        # Growth component
        growth = data.get('growth_momentum', 0.5)
        growth_signal = np.clip((growth - 0.5) * 2, -1, 1)
        score += growth_signal * self.macro_weights['growth']
        
        return np.clip(score, -1, 1)
    
    def _determine_risk_sentiment(self, regime_score: float) -> str:
        """Determine if risk is on or off"""
        if regime_score > 0.3:
            return "RISK_ON"
        elif regime_score < -0.3:
            return "RISK_OFF"
        else:
            return "NEUTRAL"
    
    def _classify_volatility(self, vix: float) -> str:
        """Classify volatility regime"""
        if vix < 15:
            return "LOW"
        elif vix < 25:
            return "NORMAL"
        elif vix < 35:
            return "HIGH"
        else:
            return "EXTREME"
    
    def _determine_trend_bias(self, data: Dict) -> str:
        """Determine market trend bias"""
        # Use SPY 200-day MA as primary trend indicator
        spy = data.get('spy_price', 400)
        spy_ma200 = data.get('spy_ma200', 400)
        
        if spy > spy_ma200 * 1.05:
            return "BULLISH"
        elif spy < spy_ma200 * 0.95:
            return "BEARISH"
        else:
            return "SIDEWAYS"
    
    def _select_strategies(self, risk: str, vol: str, trend: str) -> List[str]:
        """Select preferred strategies for current regime"""
        strategies = []
        
        if risk == "RISK_ON" and vol in ["LOW", "NORMAL"]:
            strategies.extend(["momentum_swing", "growth_breakout", "sector_rotation"])
        
        if risk == "RISK_OFF" or vol == "HIGH":
            strategies.extend(["mean_reversion", "defensive_stocks", "volatility_selling"])
        
        if trend == "BULLISH":
            strategies.extend(["trend_following", "buy_dips"])
        elif trend == "BEARISH":
            strategies.extend(["short_selling", "cash_preservation"])
        
        # Always include these as fallback
        strategies.extend(["thematic_investment", "value_investing"])
        
        return list(set(strategies))
    
    def _calculate_size_multiplier(self, risk: str, vol: str, score: float) -> float:
        """Calculate position size multiplier based on regime"""
        base = 1.0
        
        # Reduce size in risk-off or high vol environments
        if risk == "RISK_OFF":
            base *= 0.5
        elif vol == "HIGH":
            base *= 0.7
        elif vol == "EXTREME":
            base *= 0.3
        
        # Adjust for regime strength
        base *= (0.5 + abs(score) * 0.5)
        
        return np.clip(base, 0.1, 1.5)
    
    def _generate_regime_name(self, score: float) -> str:
        """Generate human-readable regime name"""
        if score > 0.5:
            return "Bull Market Expansion"
        elif score > 0:
            return "Mild Risk-On"
        elif score > -0.5:
            return "Cautious / Neutral"
        else:
            return "Bear Market / Risk-Off"
    
    def should_trade(self, strategy: str) -> Tuple[bool, str]:
        """Check if given strategy is suitable for current regime"""
        if not self.current_regime:
            return False, "No regime data"
        
        if strategy not in self.current_regime.preferred_strategies:
            return False, f"Strategy not preferred in {self.current_regime.name}"
        
        if self.current_regime.position_size_multiplier < 0.3:
            return False, "Regime too hostile for new positions"
        
        return True, "Strategy aligned with regime"
    
    def get_position_size_limit(self, base_size: float) -> float:
        """Get adjusted position size based on regime"""
        if not self.current_regime:
            return base_size
        
        return base_size * self.current_regime.position_size_multiplier
