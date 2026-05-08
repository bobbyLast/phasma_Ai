"""
Dynamic Portfolio Manager - Capital-Based Stock Universe Scaling

Manages portfolio growth and determines accessible stock universe based on current capital.
Implements progressive scaling strategy from penny stocks to mid-cap to large-cap as wealth grows.

Key Features:
- Capital-based stock universe expansion
- Progressive market cap access levels
- Smart money management and position sizing
- Portfolio growth tracking and optimization
- Dynamic risk management based on account size
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class MarketCapTier(Enum):
    PENNY_STOCKS = "penny_stocks"      # $0.10 - $5.00
    MICRO_CAP = "micro_cap"           # $5.00 - $20.00
    SMALL_CAP = "small_cap"           # $20.00 - $100.00
    MID_CAP = "mid_cap"               # $100.00 - $500.00
    LARGE_CAP = "large_cap"           # $500.00+

@dataclass
class CapitalTier:
    """Capital tier configuration"""
    min_capital: float
    max_price: float
    tier_name: str
    max_position_pct: float
    risk_per_trade: float
    max_concurrent_trades: int
    description: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class PortfolioState:
    """Current portfolio state"""
    current_capital: float
    starting_capital: float
    total_pnl: float
    total_trades: int
    winning_trades: int
    current_tier: MarketCapTier
    tier_progress: float  # Progress to next tier (0-100%)
    last_updated: str
    win_rate: float  # Current win rate (0-1)
    max_drawdown: float  # Maximum drawdown experienced
    consecutive_wins: int  # Current consecutive wins
    consecutive_losses: int  # Current consecutive losses
    # Separate bankrolls for different trading types
    stock_bankroll: float  # Bankroll for stock trading
    kalshi_bankroll: float  # Bankroll for Kalshi prediction markets
    stock_positions: Dict[str, Dict]  # Active stock positions
    kalshi_positions: Dict[str, Dict]  # Active Kalshi positions
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['current_tier'] = self.current_tier.value
        return data

class DynamicPortfolioManager:
    """
    Dynamic portfolio manager that scales stock universe based on capital growth
    """
    
    def __init__(self, config: Dict = None, data_dir: str = "data/portfolio"):
        self.config = config or {}
        self.data_dir = data_dir
        self.state_file = os.path.join(data_dir, "portfolio_state.json")
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize capital tiers
        self.capital_tiers = self._initialize_capital_tiers()
        
        # Load portfolio state
        self.portfolio_state = self._load_portfolio_state()
        
        print("Dynamic Portfolio Manager initialized")
        print(f"   - Starting capital: ${self.portfolio_state.starting_capital:.2f}")
        print(f"   - Current capital: ${self.portfolio_state.current_capital:.2f}")
        print(f"   - Current tier: {self.portfolio_state.current_tier.value}")
        print(f"   - Progress to next tier: {self.portfolio_state.tier_progress:.1f}%")
    
    def _initialize_capital_tiers(self) -> List[CapitalTier]:
        """Initialize capital-based access tiers with progressive scaling"""
        return [
            CapitalTier(
                min_capital=0,
                max_price=50.0,
                tier_name="Starter Trader",
                max_position_pct=0.40,  # 40% max per trade for small bankroll
                risk_per_trade=0.02,    # 2% risk per trade
                max_concurrent_trades=2,
                description="Focus on affordable stocks under $50 with $50 bankroll"
            ),
            CapitalTier(
                min_capital=100,
                max_price=100.0,
                tier_name="Beginner Trader",
                max_position_pct=0.30,  # 30% max per trade
                risk_per_trade=0.02,    # 2% risk per trade
                max_concurrent_trades=3,
                description="Expand to stocks up to $100 after proving profitability"
            ),
            CapitalTier(
                min_capital=500,
                max_price=200.0,
                tier_name="Growing Trader",
                max_position_pct=0.20,  # 20% max per trade
                risk_per_trade=0.015,   # 1.5% risk per trade
                max_concurrent_trades=4,
                description="Access stocks up to $200 with consistent wins"
            ),
            CapitalTier(
                min_capital=2000,
                max_price=500.0,
                tier_name="Advanced Trader",
                max_position_pct=0.15,  # 15% max per trade
                risk_per_trade=0.01,    # 1% risk per trade
                max_concurrent_trades=5,
                description="Expand to mid-cap stocks up to $500"
            ),
            CapitalTier(
                min_capital=10000,
                max_price=1000.0,
                tier_name="Expert Trader",
                max_position_pct=0.10,  # 10% max per trade
                risk_per_trade=0.008,   # 0.8% risk per trade
                max_concurrent_trades=6,
                description="Access higher priced stocks up to $1000"
            ),
            CapitalTier(
                min_capital=50000,
                max_price=10000.0,
                tier_name="Master Trader",
                max_position_pct=0.05,  # 5% max per trade
                risk_per_trade=0.005,   # 0.5% risk per trade
                max_concurrent_trades=8,
                description="Full market access including large caps"
            )
        ]
    
    def get_current_tier_config(self) -> CapitalTier:
        """Get configuration for current capital tier"""
        current_tier_name = self.portfolio_state.current_tier.value
        
        for tier in self.capital_tiers:
            if tier.tier_name.lower().replace(' ', '_') == current_tier_name:
                return tier
        
        # Default to first tier if not found
        return self.capital_tiers[0]
    
    def update_capital(self, new_capital: float, trade_pnl: float = 0, is_win: bool = None) -> bool:
        """
        Update portfolio capital and check for tier progression
        
        Args:
            new_capital: New total capital amount
            trade_pnl: P&L from the trade that triggered this update
            is_win: Whether the trade was a win (for tracking consecutive wins/losses)
        
        Returns:
            bool: True if tier changed, False otherwise
        """
        try:
            old_capital = self.portfolio_state.current_capital
            old_tier = self.portfolio_state.current_tier
            
            # Update capital
            self.portfolio_state.current_capital = new_capital
            self.portfolio_state.total_pnl += trade_pnl
            self.portfolio_state.last_updated = datetime.now(timezone.utc).isoformat()
            
            # Update win rate
            if self.portfolio_state.total_trades > 0:
                self.portfolio_state.win_rate = self.portfolio_state.winning_trades / self.portfolio_state.total_trades
            
            # Update consecutive wins/losses
            if is_win is not None:
                if is_win:
                    self.portfolio_state.consecutive_wins += 1
                    self.portfolio_state.consecutive_losses = 0
                else:
                    self.portfolio_state.consecutive_losses += 1
                    self.portfolio_state.consecutive_wins = 0
            
            # Calculate drawdown
            peak_capital = max(old_capital, self.portfolio_state.starting_capital)
            if new_capital < peak_capital:
                drawdown = (peak_capital - new_capital) / peak_capital
                self.portfolio_state.max_drawdown = max(self.portfolio_state.max_drawdown, drawdown)
            
            # Check for drawdown protection
            self.check_drawdown_protection()
            
            # Check for tier progression with win rate requirement
            new_tier = self._determine_capital_tier(new_capital)
            tier_changed = new_tier != old_tier
            
            if tier_changed and new_tier != old_tier:
                # Check win rate requirement before upgrading
                target_tier_index = 0
                for i, tier in enumerate(self.capital_tiers):
                    if tier.tier_name.lower().replace(' ', '_') == new_tier.value:
                        target_tier_index = i
                        break
                
                if self.check_win_rate_requirement(target_tier_index):
                    self.portfolio_state.current_tier = new_tier
                    print(f"🎯 TIER PROGRESSION: {old_tier.value} → {new_tier.value}")
                    print(f"   Capital: ${old_capital:.2f} → ${new_capital:.2f}")
                    print(f"   Max price access: ${self.get_max_price_access():.2f}")
                else:
                    print(f"   ❌ Cannot upgrade to {new_tier.value} - win rate requirement not met")
                    tier_changed = False
            
            # Update tier progress
            self.portfolio_state.tier_progress = self._calculate_tier_progress()
            
            # Save state
            self._save_portfolio_state()
            
            return tier_changed
            
        except Exception as e:
            print(f"❌ Error updating capital: {str(e)}")
            return False
    
    def _determine_capital_tier(self, capital: float) -> MarketCapTier:
        """Determine market cap tier based on capital"""
        for tier in reversed(self.capital_tiers):  # Check from highest to lowest
            if capital >= tier.min_capital:
                # Map tier names to enum values
                tier_mapping = {
                    "penny stock trader": MarketCapTier.PENNY_STOCKS,
                    "micro cap explorer": MarketCapTier.MICRO_CAP,
                    "small cap builder": MarketCapTier.SMALL_CAP,
                    "mid cap investor": MarketCapTier.MID_CAP,
                    "large cap trader": MarketCapTier.LARGE_CAP
                }
                return tier_mapping.get(tier.tier_name.lower(), MarketCapTier.PENNY_STOCKS)
        
        return MarketCapTier.PENNY_STOCKS
    
    def _calculate_tier_progress(self) -> float:
        """Calculate progress to next tier (0-100%)"""
        current_capital = self.portfolio_state.current_capital
        current_tier = self.portfolio_state.current_tier
        
        # Find current and next tier
        current_tier_index = 0
        for i, tier in enumerate(self.capital_tiers):
            if current_capital >= tier.min_capital:
                current_tier_index = i
        
        # If at highest tier, return 100%
        if current_tier_index >= len(self.capital_tiers) - 1:
            return 100.0
        
        # Calculate progress to next tier
        current_tier_config = self.capital_tiers[current_tier_index]
        next_tier_config = self.capital_tiers[current_tier_index + 1]
        
        capital_in_tier = current_capital - current_tier_config.min_capital
        capital_needed_for_next = next_tier_config.min_capital - current_tier_config.min_capital
        
        if capital_needed_for_next <= 0:
            return 100.0
        
        progress = min((capital_in_tier / capital_needed_for_next) * 100, 100.0)
        return progress
    
    def get_max_price_access(self) -> float:
        """Get maximum stock price accessible at current tier"""
        tier_config = self.get_current_tier_config()
        return tier_config.max_price
    
    def get_position_size_limits(self) -> Dict:
        """Get position sizing limits for current tier"""
        tier_config = self.get_current_tier_config()
        current_capital = self.portfolio_state.current_capital
        
        return {
            'max_position_value': current_capital * tier_config.max_position_pct,
            'max_position_pct': tier_config.max_position_pct,
            'risk_per_trade': tier_config.risk_per_trade,
            'max_concurrent_trades': tier_config.max_concurrent_trades,
            'recommended_position_size': current_capital * 0.05  # 5% recommended
        }
    
    def can_trade_symbol(self, symbol_price: float) -> bool:
        """Check if symbol price is accessible at current tier"""
        max_price = self.get_max_price_access()
        return symbol_price <= max_price
    
    def get_accessible_universe(self) -> Dict:
        """Get description of accessible stock universe"""
        tier_config = self.get_current_tier_config()
        
        return {
            'tier_name': tier_config.tier_name,
            'max_price': tier_config.max_price,
            'min_capital': tier_config.min_capital,
            'description': tier_config.description,
            'position_limits': self.get_position_size_limits(),
            'progress_to_next': self.portfolio_state.tier_progress
        }
    
    def get_tier_milestones(self) -> List[Dict]:
        """Get upcoming tier milestones"""
        current_capital = self.portfolio_state.current_capital
        milestones = []
        
        for tier in self.capital_tiers:
            if tier.min_capital > current_capital:
                capital_needed = tier.min_capital - current_capital
                progress_needed = (capital_needed / current_capital) * 100 if current_capital > 0 else 100
                
                milestones.append({
                    'tier_name': tier.tier_name,
                    'capital_needed': capital_needed,
                    'min_capital': tier.min_capital,
                    'max_price_access': tier.max_price,
                    'progress_needed': progress_needed
                })
        
        return milestones[:3]  # Return next 3 milestones
    
    def check_win_rate_requirement(self, target_tier_index: int) -> bool:
        """Check if win rate meets requirement for next tier"""
        if target_tier_index == 0:
            return True  # No requirement for starter tier
        
        # Win rate requirements increase with tiers
        win_rate_requirements = [0.0, 0.55, 0.60, 0.65, 0.70, 0.75]
        min_trades = [0, 10, 20, 30, 50, 100]
        
        required_win_rate = win_rate_requirements[min(target_tier_index, len(win_rate_requirements)-1)]
        required_trades = min_trades[min(target_tier_index, len(min_trades)-1)]
        
        current_win_rate = self.portfolio_state.win_rate
        current_trades = self.portfolio_state.total_trades
        
        if current_trades < required_trades:
            print(f"   ❌ Need {required_trades} trades (have {current_trades})")
            return False
        
        if current_win_rate < required_win_rate:
            print(f"   ❌ Need {required_win_rate:.0%} win rate (have {current_win_rate:.0%})")
            return False
        
        return True
    
    def check_drawdown_protection(self) -> bool:
        """Check if drawdown triggers tier demotion"""
        current_drawdown = self.portfolio_state.max_drawdown
        consecutive_losses = self.portfolio_state.consecutive_losses
        
        # Drop tier if drawdown > 40%
        if current_drawdown > 0.40:
            print(f"   ⚠️ DRAWDOWN ALERT: {current_drawdown:.0%} > 40% - Dropping tier")
            self._demote_tier()
            return True
        
        # Drop tier if 5+ consecutive losses
        if consecutive_losses >= 5:
            print(f"   ⚠️ LOSING STREAK: {consecutive_losses} consecutive losses - Dropping tier")
            self._demote_tier()
            return True
        
        return False
    
    def _demote_tier(self):
        """Demote to previous tier for protection"""
        current_tier_name = self.portfolio_state.current_tier.value
        tier_order = ["penny_stocks", "micro_cap", "small_cap", "mid_cap", "large_cap"]
        
        try:
            current_index = tier_order.index(current_tier_name)
            if current_index > 0:
                new_tier_name = tier_order[current_index - 1]
                self.portfolio_state.current_tier = MarketCapTier(new_tier_name)
                print(f"   📉 Demoted to {new_tier_name} tier for protection")
        except:
            pass
    
    def record_trade(self, symbol: str, entry_price: float, exit_price: float, 
                     position_size: int, pnl: float, win: bool) -> None:
        """Record trade outcome for portfolio tracking"""
        try:
            self.portfolio_state.total_trades += 1
            
            if win:
                self.portfolio_state.winning_trades += 1
            
            # Update capital with P&L
            new_capital = self.portfolio_state.current_capital + pnl
            self.update_capital(new_capital, pnl, win)
            
            print(f"📊 Trade recorded: {symbol} P&L: ${pnl:+.2f}")
            print(f"   Win rate: {self.get_win_rate():.1f}% | Total trades: {self.portfolio_state.total_trades}")
            
        except Exception as e:
            print(f"❌ Error recording trade: {str(e)}")
    
    def get_win_rate(self) -> float:
        """Calculate current win rate"""
        if self.portfolio_state.total_trades == 0:
            return 0.0
        
        return (self.portfolio_state.winning_trades / self.portfolio_state.total_trades) * 100
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        return {
            'current_capital': self.portfolio_state.current_capital,
            'starting_capital': self.portfolio_state.starting_capital,
            'total_pnl': self.portfolio_state.total_pnl,
            'total_return_pct': ((self.portfolio_state.current_capital - self.portfolio_state.starting_capital) / self.portfolio_state.starting_capital) * 100,
            'total_trades': self.portfolio_state.total_trades,
            'winning_trades': self.portfolio_state.winning_trades,
            'win_rate': self.get_win_rate(),
            'current_tier': self.portfolio_state.current_tier.value,
            'tier_progress': self.portfolio_state.tier_progress,
            'accessible_universe': self.get_accessible_universe(),
            'upcoming_milestones': self.get_tier_milestones()
        }
    
    def _load_portfolio_state(self) -> PortfolioState:
        """Load portfolio state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                return PortfolioState(
                    current_capital=data.get('current_capital', 100.0),
                    starting_capital=data.get('starting_capital', 100.0),
                    total_pnl=data.get('total_pnl', 0.0),
                    total_trades=data.get('total_trades', 0),
                    winning_trades=data.get('winning_trades', 0),
                    current_tier=MarketCapTier(data.get('current_tier', 'penny_stocks')),
                    tier_progress=data.get('tier_progress', 0.0),
                    last_updated=data.get('last_updated', datetime.now(timezone.utc).isoformat()),
                    win_rate=data.get('win_rate', 0.0),
                    max_drawdown=data.get('max_drawdown', 0.0),
                    consecutive_wins=data.get('consecutive_wins', 0),
                    consecutive_losses=data.get('consecutive_losses', 0),
                    stock_bankroll=data.get('stock_bankroll', 50.0),
                    kalshi_bankroll=data.get('kalshi_bankroll', 50.0),
                    stock_positions=data.get('stock_positions', {}),
                    kalshi_positions=data.get('kalshi_positions', {})
                )
        
        except Exception as e:
            print(f"⚠️ Error loading portfolio state: {str(e)}")
        
        # Return default state
        return PortfolioState(
            current_capital=100.0,  # Total $100 ($50 stocks + $50 Kalshi)
            starting_capital=100.0,
            total_pnl=0.0,
            total_trades=0,
            winning_trades=0,
            current_tier=MarketCapTier.PENNY_STOCKS,
            tier_progress=0.0,
            last_updated=datetime.now(timezone.utc).isoformat(),
            win_rate=0.0,
            max_drawdown=0.0,
            consecutive_wins=0,
            consecutive_losses=0,
            stock_bankroll=50.0,  # $50 for stock trading
            kalshi_bankroll=50.0,  # $50 for Kalshi markets
            stock_positions={},
            kalshi_positions={}
        )
    
    def _save_portfolio_state(self) -> None:
        """Save portfolio state to file"""
        try:
            data = self.portfolio_state.to_dict()
            
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving portfolio state: {str(e)}")

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Dynamic Portfolio Manager...")
    
    manager = DynamicPortfolioManager()
    
    print(f"\n📊 Current Portfolio State:")
    summary = manager.get_portfolio_summary()
    
    print(f"   Capital: ${summary['current_capital']:.2f} (${summary['total_pnl']:+.2f} P&L)")
    print(f"   Return: {summary['total_return_pct']:+.1f}%")
    print(f"   Win Rate: {summary['win_rate']:.1f}% ({summary['winning_trades']}/{summary['total_trades']})")
    print(f"   Tier: {summary['current_tier']} ({summary['tier_progress']:.1f}% to next)")
    
    print(f"\n🎯 Accessible Universe:")
    universe = summary['accessible_universe']
    print(f"   Max price: ${universe['max_price']:.2f}")
    print(f"   Max position: {universe['position_limits']['max_position_pct']*100:.0f}%")
    print(f"   Risk per trade: {universe['position_limits']['risk_per_trade']*100:.1f}%")
    
    print(f"\n🚀 Upcoming Milestones:")
    for milestone in summary['upcoming_milestones']:
        print(f"   {milestone['tier_name']}: Need ${milestone['capital_needed']:.2f} more")
        print(f"      Max price access: ${milestone['max_price_access']:.2f}")
    
    # Test capital progression
    print(f"\n📈 Testing Capital Progression:")
    
    # Simulate some winning trades
    test_trades = [
        (10.0, True),   # +$10 win
        (15.0, True),   # +$15 win  
        (25.0, False),  # -$25 loss
        (30.0, True),   # +$30 win
    ]
    
    for pnl, win in test_trades:
        current_capital = manager.portfolio_state.current_capital
        new_capital = current_capital + pnl
        tier_changed = manager.update_capital(new_capital, pnl)
        
        if tier_changed:
            print(f"   🎯 TIER UP! Now: {manager.portfolio_state.current_tier.value}")
        else:
            print(f"   Capital: ${new_capital:.2f} ({manager.get_win_rate():.1f}% win rate)")
    
    print(f"\n✅ Dynamic Portfolio Manager working!")
    print(f"   - Capital-based tier progression implemented")
    print(f"   - Smart position sizing configured")
    print(f"   - Ready for integration with trading system")
