"""
Long-Tier Investment Engine
Handles detection, scoring, and management of long-term investment opportunities
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
import logging

class InvestmentTier(Enum):
    MICRO = "micro"      # $50-$250 positions
    STANDARD = "standard" # $250-$2,500 positions
    HEAVY = "heavy"      # $2,500+ positions

@dataclass
class Opportunity:
    symbol: str
    current_price: float
    target_price: float
    catalyst_score: float  # 0-10 scale
    partner_rank: float    # 0-10 scale
    volume_7d_avg: int
    market_cap: float
    last_updated: datetime = field(default_factory=datetime.utcnow)
    entry_price: Optional[float] = None
    position_size: float = 0.0
    tier: Optional[InvestmentTier] = None
    
    @property
    def upside_potential(self) -> float:
        """Calculate potential return as a multiple"""
        return (self.target_price / self.current_price) - 1
    
    @property
    def risk_score(self) -> float:
        """Calculate risk score (lower is better)"""
        # Higher market cap and volume = lower risk
        market_cap_score = min(1.0, np.log10(self.market_cap) / 10)  # 0-1 scale
        volume_score = min(1.0, np.log10(self.volume_7d_avg) / 6)    # 0-1 scale
        
        # Combine factors (lower is better)
        return (3.0 - (market_cap_score + volume_score + (self.catalyst_score / 10))) / 3.0

class LongTierEngine:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Load bankroll tiers from config
        self.tier_allocations = {
            InvestmentTier.MICRO: config.get('tier_allocations', {}).get('micro', 0.1),    # 10% of bankroll
            InvestmentTier.STANDARD: config.get('tier_allocations', {}).get('standard', 0.3), # 30%
            InvestmentTier.HEAVY: config.get('tier_allocations', {}).get('heavy', 0.6)     # 60%
        }
        
        # Position limits per tier
        self.position_limits = {
            InvestmentTier.MICRO: (50, 250),
            InvestmentTier.STANDARD: (250, 2500),
            InvestmentTier.HEAVY: (2500, float('inf'))
        }
        
        # Track active positions
        self.positions: Dict[str, Opportunity] = {}
    
    def evaluate_opportunity(self, opportunity: Opportunity) -> Tuple[bool, Optional[InvestmentTier]]:
        """
        Evaluate if an opportunity qualifies for long-tier investment
        Returns (is_qualified, suggested_tier)
        """
        # Basic validation
        if opportunity.current_price <= 0 or opportunity.target_price <= 0:
            return False, None
            
        # Calculate key metrics
        upside = opportunity.upside_potential
        risk = opportunity.risk_score
        
        # Qualification criteria
        min_upside = 2.0  # 2x minimum upside potential
        max_risk = 0.7    # 0-1 scale, lower is better
        
        if upside < min_upside or risk > max_risk:
            return False, None
        
        # Determine appropriate tier
        if upside >= 10.0 and opportunity.partner_rank >= 8.0:
            return True, InvestmentTier.HEAVY
        elif upside >= 5.0 and opportunity.partner_rank >= 6.0:
            return True, InvestmentTier.STANDARD
        elif upside >= 2.0 and opportunity.partner_rank >= 4.0:
            return True, InvestmentTier.MICRO
            
        return False, None
    
    def calculate_position_size(self, opportunity: Opportunity, available_capital: float) -> float:
        """Calculate position size based on tier and bankroll"""
        if opportunity.tier is None:
            qualified, tier = self.evaluate_opportunity(opportunity)
            if not qualified:
                return 0.0
            opportunity.tier = tier
        
        # Get allocation percentage for this tier
        allocation_pct = self.tier_allocations.get(opportunity.tier, 0.0)
        
        # Calculate max position size based on bankroll and tier limits
        max_by_bankroll = available_capital * allocation_pct
        min_size, max_size = self.position_limits[opportunity.tier]
        
        # Cap position size by tier limits and available capital
        position_size = min(max_by_bankroll, max_size)
        position_size = max(position_size, min_size)
        
        # Ensure we're not over-allocating to a single position
        max_single_position = available_capital * 0.1  # Max 10% to any single position
        position_size = min(position_size, max_single_position)
        
        return position_size
    
    def generate_alert(self, opportunity: Opportunity) -> dict:
        """Generate alert message for this opportunity"""
        if opportunity.tier is None:
            qualified, tier = self.evaluate_opportunity(opportunity)
            if not qualified:
                return None
            opportunity.tier = tier
        
        # Calculate potential profits for each tier
        shares = opportunity.position_size / opportunity.current_price
        potential_profit = shares * (opportunity.target_price - opportunity.current_price)
        
        return {
            'symbol': opportunity.symbol,
            'current_price': opportunity.current_price,
            'target_price': opportunity.target_price,
            'upside_potential': opportunity.upside_potential * 100,  # as percentage
            'tier': opportunity.tier.value,
            'position_size': opportunity.position_size,
            'potential_profit': potential_profit,
            'catalyst_score': opportunity.catalyst_score,
            'partner_rank': opportunity.partner_rank,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def monitor_positions(self) -> List[dict]:
        """Monitor all active positions and generate updates"""
        updates = []
        for symbol, position in self.positions.items():
            # Check for exit signals (simplified)
            current_price = self._get_current_price(symbol)
            if current_price is None:
                continue
                
            # Calculate current return
            if position.entry_price is None:
                position.entry_price = current_price
                
            current_return = (current_price / position.entry_price) - 1
            
            # Generate update
            update = {
                'symbol': symbol,
                'current_price': current_price,
                'entry_price': position.entry_price,
                'current_return': current_return * 100,  # as percentage
                'status': self._get_position_status(position, current_price),
                'last_updated': datetime.utcnow().isoformat()
            }
            updates.append(update)
            
            # Update position
            position.current_price = current_price
            
        return updates
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price (placeholder - implement actual market data feed)"""
        # TODO: Implement actual market data lookup
        return None
    
    def _get_position_status(self, position: Opportunity, current_price: float) -> str:
        """Determine position status"""
        if position.entry_price is None:
            return "PENDING_ENTRY"
            
        current_return = (current_price / position.entry_price) - 1
        
        if current_return <= -0.2:  # 20% drawdown
            return "REVIEW_REQUIRED"
        elif current_return >= position.upside_potential * 0.8:  # 80% of target
            return "CONSIDER_TAKING_PROFITS"
        else:
            return "HOLD"
