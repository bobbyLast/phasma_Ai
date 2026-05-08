#!/usr/bin/env python3
"""
PHASMA AI - Signal Framework for Stocks/Crypto Trading
Production-ready signal normalization and decision logic
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Normalized trading signal output by AI"""
    symbol: str
    timeframe: str  # '1m', '5m', '15m', '1h', '4h', '1d'
    direction: float  # -1 (strong short) to 1 (strong long), 0 = no edge
    confidence: float  # 0 to 1, strength of the edge
    expected_return: Optional[float] = None  # Expected return over horizon
    volatility: Optional[float] = None  # Predicted volatility
    predicted_win_rate: Optional[float] = None  # Predicted win rate
    predicted_max_drawdown: Optional[float] = None  # Predicted max DD
    timestamp: str = None
    source: str = "AI_MODEL"
    metadata: Optional[Dict] = None  # Additional metadata
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        
        # Validate ranges
        self.direction = max(-1, min(1, self.direction))
        self.confidence = max(0, min(1, self.confidence))

class SignalTier:
    """Signal confidence tiers"""
    NO_EDGE = 0      # c < 0.55
    WEAK = 1         # 0.55 ≤ c < 0.65
    MODERATE = 2     # 0.65 ≤ c < 0.75
    STRONG = 3       # 0.75 ≤ c < 0.85
    HIGH_CONV = 4    # c ≥ 0.85
    
    @classmethod
    def from_confidence(cls, confidence: float) -> int:
        """Convert confidence score to tier"""
        if confidence < 0.55:
            return cls.NO_EDGE
        elif confidence < 0.65:
            return cls.WEAK
        elif confidence < 0.75:
            return cls.MODERATE
        elif confidence < 0.85:
            return cls.STRONG
        else:
            return cls.HIGH_CONV
    
    @classmethod
    def get_tier_name(cls, tier: int) -> str:
        """Get tier name"""
        names = {
            0: "NO_EDGE",
            1: "WEAK",
            2: "MODERATE", 
            3: "STRONG",
            4: "HIGH_CONV"
        }
        return names.get(tier, "UNKNOWN")

class DecisionBand:
    """Decision bands for trading actions"""
    NO_TRADE = "NO_TRADE"      # No position, no order
    WATCH = "WATCH"            # Log signal, no trade
    ENTRY = "ENTRY"            # Small probing position
    CONVICTION = "CONVICTION"  # Standard position size
    HIGH_CONV = "HIGH_CONV"    # Max allowed position
    
    @classmethod
    def determine_band(cls, tier: int, market_conditions: Dict) -> str:
        """Determine decision band based on tier and conditions"""
        # Extract market conditions
        volatility = market_conditions.get('volatility', 0)
        volatility_regime = market_conditions.get('volatility_regime', 'NORMAL')
        liquidity = market_conditions.get('liquidity_score', 1.0)
        spread = market_conditions.get('spread_pct', 0.1)
        trend_aligned = market_conditions.get('trend_aligned', True)
        
        # Band A - No-trade zone
        if tier == SignalTier.NO_EDGE:
            return cls.NO_TRADE
        
        if volatility_regime == 'EXTREME':
            return cls.NO_TRADE
        
        if liquidity < 0.3 or spread > 1.0:
            return cls.NO_TRADE
        
        # Band B - Watch-only zone
        if tier == SignalTier.WEAK:
            return cls.WATCH
        
        if not trend_aligned and tier <= SignalTier.MODERATE:
            return cls.WATCH
        
        # Band C - Entry zone (probing)
        if tier == SignalTier.MODERATE:
            if volatility_regime == 'NORMAL' and trend_aligned:
                return cls.ENTRY
            else:
                return cls.WATCH
        
        # Band D - Conviction zone
        if tier == SignalTier.STRONG:
            if trend_aligned and liquidity > 0.5:
                return cls.CONVICTION
            else:
                return cls.ENTRY
        
        # Band E - High-conviction zone
        if tier == SignalTier.HIGH_CONV:
            if trend_aligned and liquidity > 0.7:
                return cls.HIGH_CONV
            else:
                return cls.CONVICTION
        
        return cls.NO_TRADE

@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_risk_per_trade: float = 0.01  # 1% of equity per trade
    daily_loss_limit: float = 0.05    # 5% daily loss limit
    max_concurrent_exposure: float = 0.20  # 20% max total exposure
    volatility_threshold: float = 0.05  # 5% volatility threshold
    max_positions_per_asset: int = 1
    max_sector_exposure: float = 0.10  # 10% per sector
    
    def __post_init__(self):
        # Validate parameters
        self.max_risk_per_trade = max(0.001, min(0.05, self.max_risk_per_trade))
        self.daily_loss_limit = max(0.01, min(0.20, self.daily_loss_limit))
        self.max_concurrent_exposure = max(0.05, min(0.50, self.max_concurrent_exposure))

class PositionSizer:
    """Position sizing based on risk and tier"""
    
    def __init__(self, risk_params: RiskParameters):
        self.risk_params = risk_params
    
    def calculate_position_size(self, 
                              signal: TradingSignal,
                              account_equity: float,
                              current_exposure: float,
                              stop_distance_pct: float) -> Dict[str, float]:
        """Calculate position size based on signal and risk parameters"""
        
        # Get signal tier
        tier = SignalTier.from_confidence(signal.confidence)
        
        # Calculate base position size using risk formula
        # Q = (E * r) / SL
        if stop_distance_pct <= 0:
            logger.warning(f"Invalid stop distance for {signal.symbol}: {stop_distance_pct}")
            return {"size_notional": 0, "size_shares": 0, "risk_amount": 0}
        
        base_size_notional = (account_equity * self.risk_params.max_risk_per_trade) / stop_distance_pct
        
        # Apply tier multipliers
        tier_multipliers = {
            SignalTier.NO_EDGE: 0,
            SignalTier.WEAK: 0,
            SignalTier.MODERATE: 0.5,
            SignalTier.STRONG: 1.0,
            SignalTier.HIGH_CONV: 1.5
        }
        
        multiplier = tier_multipliers.get(tier, 0)
        adjusted_size = base_size_notional * multiplier
        
        # Apply global exposure limits
        max_additional = account_equity * self.risk_params.max_concurrent_exposure - current_exposure
        adjusted_size = min(adjusted_size, max_additional)
        
        # Ensure non-negative
        adjusted_size = max(0, adjusted_size)
        
        # Calculate share/contract quantity
        price = signal.expected_return or 100  # Use current price if available
        size_shares = int(adjusted_size / price) if price > 0 else 0
        
        # Calculate actual risk
        risk_amount = size_shares * price * stop_distance_pct
        
        return {
            "size_notional": adjusted_size,
            "size_shares": size_shares,
            "risk_amount": risk_amount,
            "risk_pct": risk_amount / account_equity if account_equity > 0 else 0,
            "tier": tier,
            "multiplier": multiplier
        }

@dataclass
class TradeDecision:
    """Final trade decision"""
    action: str  # NO_TRADE, WATCH, ENTRY, CONVICTION, HIGH_CONV
    direction: int  # -1, 0, 1
    symbol: str
    size_notional: float
    size_shares: int
    tier: int
    band: str
    confidence: float
    risk_amount: float
    risk_pct: float
    reasoning: List[str]
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "action": self.action,
            "direction": self.direction,
            "symbol": self.symbol,
            "size_notional": self.size_notional,
            "size_shares": self.size_shares,
            "tier": self.tier,
            "band": self.band,
            "confidence": self.confidence,
            "risk_amount": self.risk_amount,
            "risk_pct": self.risk_pct,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp
        }

class SignalProcessor:
    """Main signal processing and decision engine"""
    
    def __init__(self, risk_params: Optional[RiskParameters] = None):
        self.risk_params = risk_params or RiskParameters()
        self.position_sizer = PositionSizer(self.risk_params)
        
        # Track daily PnL for loss limit
        self.daily_pnl = 0
        self.last_reset_date = datetime.now().date()
        
    def process_signal(self, 
                      signal: TradingSignal,
                      market_conditions: Dict,
                      account_state: Dict) -> TradeDecision:
        """Process signal and return trade decision"""
        
        # Reset daily PnL if new day
        if datetime.now().date() != self.last_reset_date:
            self.daily_pnl = 0
            self.last_reset_date = datetime.now().date()
        
        # Check daily loss limit
        daily_loss_pct = abs(self.daily_pnl) / account_state.get('equity', 1)
        if daily_loss_pct > self.risk_params.daily_loss_limit:
            return self._create_decision(
                signal=signal,
                action="NO_TRADE",
                size=0,
                reasoning=[f"Daily loss limit exceeded: {daily_loss_pct:.2%}"]
            )
        
        # Check for edge
        if signal.direction == 0 or signal.confidence < 0.55:
            return self._create_decision(
                signal=signal,
                action="NO_TRADE",
                size=0,
                reasoning=["No edge detected or confidence too low"]
            )
        
        # Determine tier
        tier = SignalTier.from_confidence(signal.confidence)
        
        # Determine decision band
        band = DecisionBand.determine_band(tier, market_conditions)
        
        # If no-trade or watch, return early
        if band in ["NO_TRADE", "WATCH"]:
            return self._create_decision(
                signal=signal,
                action=band,
                size=0,
                reasoning=[f"Signal tier {tier} placed in {band} band"]
            )
        
        # Calculate position size
        account_equity = account_state.get('equity', 0)
        current_exposure = account_state.get('current_exposure', 0)
        stop_distance = market_conditions.get('stop_distance_pct', 0.02)  # 2% default
        
        sizing = self.position_sizer.calculate_position_size(
            signal=signal,
            account_equity=account_equity,
            current_exposure=current_exposure,
            stop_distance_pct=stop_distance
        )
        
        # Build reasoning
        reasoning = [
            f"Signal tier: {SignalTier.get_tier_name(tier)} (confidence: {signal.confidence:.2f})",
            f"Decision band: {band}",
            f"Direction: {signal.direction:+.0f}",
            f"Position size: ${sizing['size_notional']:,.2f}",
            f"Risk amount: ${sizing['risk_amount']:,.2f} ({sizing['risk_pct']:.2%})"
        ]
        
        # Add market condition reasoning
        if market_conditions.get('volatility_regime') == 'HIGH':
            reasoning.append("High volatility - reduced size")
        if not market_conditions.get('trend_aligned', True):
            reasoning.append("Trend not aligned - caution")
        
        return self._create_decision(
            signal=signal,
            action=band,
            size=sizing['size_notional'],
            size_shares=sizing['size_shares'],
            tier=tier,
            band=band,
            risk_amount=sizing['risk_amount'],
            risk_pct=sizing['risk_pct'],
            reasoning=reasoning
        )
    
    def _create_decision(self, 
                        signal: TradingSignal,
                        action: str,
                        size: float,
                        size_shares: int = 0,
                        tier: int = 0,
                        band: str = "NO_TRADE",
                        risk_amount: float = 0,
                        risk_pct: float = 0,
                        reasoning: List[str] = None) -> TradeDecision:
        """Create trade decision object"""
        return TradeDecision(
            action=action,
            direction=int(signal.direction),
            symbol=signal.symbol,
            size_notional=size,
            size_shares=size_shares,
            tier=tier,
            band=band,
            confidence=signal.confidence,
            risk_amount=risk_amount,
            risk_pct=risk_pct,
            reasoning=reasoning or [],
            timestamp=datetime.now().isoformat()
        )
    
    def update_daily_pnl(self, pnl: float):
        """Update daily PnL for risk management"""
        self.daily_pnl += pnl
        logger.info(f"Daily PnL updated: ${self.daily_pnl:,.2f}")

# Example usage and testing
def main():
    """Example of signal processing framework"""
    print("🤖 PHASMA AI - Signal Framework Demo")
    print("=" * 60)
    
    # Initialize processor
    risk_params = RiskParameters(
        max_risk_per_trade=0.01,  # 1% per trade
        daily_loss_limit=0.05,    # 5% daily limit
        max_concurrent_exposure=0.20  # 20% max exposure
    )
    
    processor = SignalProcessor(risk_params)
    
    # Example signals
    signals = [
        TradingSignal(
            symbol="BTCUSDT",
            timeframe="1h",
            direction=1,
            confidence=0.92,  # High conviction
            expected_return=0.015,
            volatility=0.04
        ),
        TradingSignal(
            symbol="AAPL",
            timeframe="15m",
            direction=-1,
            confidence=0.68,  # Moderate
            expected_return=-0.008,
            volatility=0.025
        ),
        TradingSignal(
            symbol="TSLA",
            timeframe="5m",
            direction=1,
            confidence=0.45,  # No edge
            expected_return=0.002,
            volatility=0.06
        )
    ]
    
    # Market conditions for each signal
    market_conditions = [
        {
            'volatility': 0.04,
            'volatility_regime': 'NORMAL',
            'liquidity_score': 0.9,
            'spread_pct': 0.05,
            'trend_aligned': True,
            'stop_distance_pct': 0.025
        },
        {
            'volatility': 0.025,
            'volatility_regime': 'NORMAL',
            'liquidity_score': 0.8,
            'spread_pct': 0.02,
            'trend_aligned': False,
            'stop_distance_pct': 0.02
        },
        {
            'volatility': 0.06,
            'volatility_regime': 'HIGH',
            'liquidity_score': 0.6,
            'spread_pct': 0.1,
            'trend_aligned': True,
            'stop_distance_pct': 0.03
        }
    ]
    
    # Account state
    account_state = {
        'equity': 100000,  # $100k
        'current_exposure': 5000  # $5k already exposed
    }
    
    # Process each signal
    for i, (signal, conditions) in enumerate(zip(signals, market_conditions)):
        print(f"\n📊 Signal {i+1}: {signal.symbol}")
        print("-" * 40)
        print(f"Direction: {signal.direction:+.0f}")
        print(f"Confidence: {signal.confidence:.2f}")
        print(f"Expected Return: {signal.expected_return:+.2%}")
        
        # Process signal
        decision = processor.process_signal(signal, conditions, account_state)
        
        print(f"\nDecision: {decision.action}")
        print(f"Tier: {SignalTier.get_tier_name(decision.tier)}")
        print(f"Band: {decision.band}")
        
        if decision.size_shares > 0:
            print(f"Size: {decision.size_shares} shares (${decision.size_notional:,.2f})")
            print(f"Risk: ${decision.risk_amount:,.2f} ({decision.risk_pct:.2%})")
        
        print("\nReasoning:")
        for reason in decision.reasoning:
            print(f"  • {reason}")

if __name__ == "__main__":
    main()
