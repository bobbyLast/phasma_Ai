"""
============================================================
ENHANCED EXECUTION CHECKER - US-003 IMPLEMENTATION
============================================================

File: engines/execution_checker_v2.py
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RejectionReason(Enum):
    LOW_ADV = "LOW_ADV"
    HIGH_SPREAD = "HIGH_SPREAD"
    INSUFFICIENT_DEPTH = "INSUFFICIENT_DEPTH"
    DILUTION_RISK = "DILUTION_RISK"
    POSITION_LIMIT = "POSITION_LIMIT"
    SLIPPAGE_RISK = "SLIPPAGE_RISK"
    LEGAL_REVIEW_REQUIRED = "LEGAL_REVIEW_REQUIRED"
    MARKET_HALTED = "MARKET_HALTED"
    VOLATILITY_OVERRIDE = "VOLATILITY_OVERRIDE"

@dataclass
class MarketSnapshot:
    ticker: str
    price: float
    adv_30d_shares: int
    adv_30d_dollars: float
    top_bid: float
    top_ask: float
    top_of_book_spread_pct: float
    depth_top5_shares: int
    depth_top5_dollars: float
    volume_today: int
    is_halted: bool
    limit_up: bool
    limit_down: bool
    vix: float  # Market volatility
    sector_volatility: float
    timestamp: datetime

@dataclass
class OrderPlan:
    total_shares: int
    tranches: List[Dict]
    max_slippage_pct: float
    participation_rate: float
    time_in_force: str
    order_type: str

@dataclass
class StrategyProfile:
    name: str
    min_adv_shares: int
    min_adv_dollars: float
    max_spread_pct: float
    min_depth_multiplier: float
    max_position_pct: float
    max_position_dollars: float
    min_trade_shares: int
    participation_rate_cap: float
    soft_rejections: List[RejectionReason]
    microcap_fallback: bool

class ExecutionChecker:
    def __init__(self, config: Dict, market_data_service, filings_service):
        self.config = config
        self.market = market_data_service
        self.filings = filings_service
        self.paper_mode = config.get('paper_mode', True)
        self.feature_flags = config.get('feature_flags', {})
        
        # Initialize strategy profiles
        self.strategies = self._load_strategy_profiles()
        
        # Dilution penalty
        self.dilution_penalty = config.get('dilution_penalty', 0.5)
        
        # Market regime thresholds
        self.vix_threshold = config.get('vix_threshold', 30)
        self.sector_vol_threshold = config.get('sector_vol_threshold', 50)
    
    def evaluate(self, ticker: str, desired_shares: int, strategy_name: str, 
                 confluence_score: float, evidence_payload: Dict) -> Dict:
        """
        Main evaluation method
        
        Returns:
            {
                "allowed": bool,
                "reason_codes": List[str],
                "recommended_size_shares": int,
                "order_plan": Optional[OrderPlan],
                "diagnostics": Dict
            }
        """
        # Get strategy profile
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            return self._reject("UNKNOWN_STRATEGY", 0, None)
        
        # Get market snapshot
        snapshot = self.market.get_snapshot(ticker)
        
        # Check for market halts
        if snapshot.is_halted or snapshot.limit_up or snapshot.limit_down:
            return self._reject(RejectionReason.MARKET_HALTED.value, 0, None)
        
        # Check for legal review requirements
        if self._requires_legal_review(evidence_payload):
            return self._reject(RejectionReason.LEGAL_REVIEW_REQUIRED.value, 0, None)
        
        # Market regime check
        if self._is_market_too_volatile(snapshot, strategy):
            return self._reject(RejectionReason.VOLATILITY_OVERRIDE.value, 0, None)
        
        # Core checks
        reasons = []
        
        # ADV check
        if snapshot.adv_30d_shares < strategy.min_adv_shares:
            reasons.append(RejectionReason.LOW_ADV.value)
        elif snapshot.adv_30d_dollars < strategy.min_adv_dollars:
            reasons.append(RejectionReason.LOW_ADV.value)
        
        # Spread check
        if snapshot.top_of_book_spread_pct > strategy.max_spread_pct:
            reasons.append(RejectionReason.HIGH_SPREAD.value)
        
        # Depth check
        required_depth = desired_shares * strategy.min_depth_multiplier
        if snapshot.depth_top5_shares < required_depth:
            reasons.append(RejectionReason.INSUFFICIENT_DEPTH.value)
        
        # Dilution check
        dilution_flag = self.filings.has_recent_offering(
            ticker, 
            days=self.config.get('dilution_window', 30)
        )
        if dilution_flag:
            reasons.append(RejectionReason.DILUTION_RISK.value)
        
        # Calculate recommended size
        recommended_size = self._compute_size(
            snapshot, confluence_score, strategy, dilution_flag
        )
        
        # Position limits
        if recommended_size < strategy.min_trade_shares:
            reasons.append(RejectionReason.POSITION_LIMIT.value)
        
        # Slippage risk check
        estimated_slippage = self._estimate_slippage(snapshot, recommended_size, strategy)
        if estimated_slippage > self.config.get('max_slippage_pct', 0.01):
            reasons.append(RejectionReason.SLIPPAGE_RISK.value)
        
        # Determine if allowed (hard rejections block, soft don't)
        hard_rejections = [r for r in reasons if r not in strategy.soft_rejections]
        allowed = len(hard_rejections) == 0
        
        # Build order plan if allowed
        order_plan = None
        if allowed and recommended_size > 0:
            order_plan = self._build_order_plan(recommended_size, snapshot, strategy)
        
        # Log for analytics
        self._log_evaluation(ticker, strategy_name, reasons, recommended_size, allowed)
        
        return {
            "allowed": allowed,
            "reason_codes": reasons,
            "recommended_size_shares": recommended_size,
            "order_plan": order_plan,
            "diagnostics": {
                "ticker": ticker,
                "strategy": strategy_name,
                "adv_shares": snapshot.adv_30d_shares,
                "adv_dollars": snapshot.adv_30d_dollars,
                "spread_pct": snapshot.top_of_book_spread_pct,
                "depth_top5_shares": snapshot.depth_top5_shares,
                "dilution_flag": dilution_flag,
                "confluence_score": confluence_score,
                "estimated_slippage_pct": estimated_slippage,
                "market_regime": {
                    "vix": snapshot.vix,
                    "sector_volatility": snapshot.sector_volatility
                }
            }
        }
    
    def _load_strategy_profiles(self) -> Dict[str, StrategyProfile]:
        """Load strategy profiles from config"""
        profiles = {}
        
        # Penny Moonshot
        profiles['penny_moonshot'] = StrategyProfile(
            name='penny_moonshot',
            min_adv_shares=100000,
            min_adv_dollars=50000,
            max_spread_pct=0.03,
            min_depth_multiplier=2.0,
            max_position_pct=0.02,
            max_position_dollars=5000,
            min_trade_shares=100,
            participation_rate_cap=0.05,
            soft_rejections=[RejectionReason.INSUFFICIENT_DEPTH.value],
            microcap_fallback=True
        )
        
        # Smallcap Compounder
        profiles['smallcap_compounder'] = StrategyProfile(
            name='smallcap_compounder',
            min_adv_shares=500000,
            min_adv_dollars=250000,
            max_spread_pct=0.02,
            min_depth_multiplier=1.5,
            max_position_pct=0.03,
            max_position_dollars=10000,
            min_trade_shares=500,
            participation_rate_cap=0.10,
            soft_rejections=[RejectionReason.DILUTION_RISK.value],
            microcap_fallback=False
        )
        
        return profiles
    
    def _requires_legal_review(self, evidence_payload: Dict) -> bool:
        """Check if evidence requires legal review"""
        # Check for cross-jurisdiction filings
        if evidence_payload.get('cross_border'):
            return True
        
        # Check for ambiguous provenance
        if evidence_payload.get('provenance_confidence', 1.0) < 0.8:
            return True
        
        # Check for related party transactions
        if evidence_payload.get('related_party'):
            return True
        
        return False
    
    def _is_market_too_volatile(self, snapshot: MarketSnapshot, strategy: StrategyProfile) -> bool:
        """Check if market volatility requires tighter controls"""
        # Overall market volatility check
        if snapshot.vix > self.vix_threshold:
            return True
        
        # Sector-specific volatility check
        if snapshot.sector_volatility > self.sector_vol_threshold:
            return True
        
        return False
    
    def _compute_size(self, snapshot: MarketSnapshot, confluence_score: float, 
                      strategy: StrategyProfile, dilution_flag: bool) -> int:
        """Compute recommended position size"""
        # Base size from strategy limits
        base_size_by_pct = int(snapshot.depth_top5_shares * strategy.max_position_pct)
        base_size_by_dollars = int(strategy.max_position_dollars / snapshot.price)
        base_size = min(base_size_by_pct, base_size_by_dollars)
        
        # Liquidity multiplier
        liquidity_mult = min(snapshot.adv_30d_shares / 1_000_000, 1.0)
        
        # Confidence multiplier
        confidence_mult = max(0.3, confluence_score / 0.9)
        
        # Dilution penalty
        dilution_mult = 1.0
        if dilution_flag:
            dilution_mult = self.dilution_penalty
        
        # Microcap fallback
        if strategy.microcap_fallback and snapshot.adv_30d_dollars < 100000:
            liquidity_mult *= 0.5
            confidence_mult *= 0.7
        
        # Calculate final size
        recommended_size = int(base_size * liquidity_mult * confidence_mult * dilution_mult)
        
        # Round to strategy minimum increments
        return max(0, recommended_size - (recommended_size % strategy.min_trade_shares))
    
    def _estimate_slippage(self, snapshot: MarketSnapshot, shares: int, 
                          strategy: StrategyProfile) -> float:
        """Estimate execution slippage"""
        # Base slippage from spread
        base_slippage = snapshot.top_of_book_spread_pct * 0.5
        
        # Impact slippage from size
        participation_rate = shares / snapshot.depth_top5_shares
        impact_slippage = participation_rate * 0.01  # 1% per 100% participation
        
        # Market regime adjustment
        regime_multiplier = 1.0
        if snapshot.vix > 25:
            regime_multiplier = 1.5
        
        total_slippage = (base_slippage + impact_slippage) * regime_multiplier
        
        return total_slippage
    
    def _build_order_plan(self, shares: int, snapshot: MarketSnapshot, 
                         strategy: StrategyProfile) -> OrderPlan:
        """Build execution order plan"""
        # Simple implementation - single tranche
        # Could be enhanced for multi-tranche laddering
        
        participation_rate = min(shares / snapshot.depth_top5_shares, 
                                strategy.participation_rate_cap)
        
        return OrderPlan(
            total_shares=shares,
            tranches=[{
                'shares': shares,
                'type': 'LIMIT',
                'price': snapshot.price * (1 + self._estimate_slippage(snapshot, shares, strategy)),
                'time_in_force': 'DAY',
                'participation_rate': participation_rate
            }],
            max_slippage_pct=self._estimate_slippage(snapshot, shares, strategy),
            participation_rate=participation_rate,
            time_in_force='DAY',
            order_type='LIMIT'
        )
    
    def _reject(self, reason: str, size: int, plan: Optional[OrderPlan]) -> Dict:
        """Helper to create rejection response"""
        return {
            "allowed": False,
            "reason_codes": [reason],
            "recommended_size_shares": size,
            "order_plan": plan,
            "diagnostics": {}
        }
    
    def _log_evaluation(self, ticker: str, strategy: str, reasons: List[str], 
                       size: int, allowed: bool):
        """Log evaluation for analytics"""
        logger.info(f"ExecutionCheck: {ticker} {strategy} allowed={allowed} "
                   f"reasons={reasons} size={size}")
        
        # Store in metrics system
        if hasattr(self, 'metrics'):
            self.metrics.increment('execution_checks.total')
            self.metrics.increment(f'execution_checks.{strategy}')
            
            if allowed:
                self.metrics.increment('execution_checks.allowed')
            else:
                for reason in reasons:
                    self.metrics.increment(f'execution_checks.rejections.{reason}')
    
    def execute_order(self, order_plan: OrderPlan, ticker: str) -> Dict:
        """Execute order (paper or live)"""
        if self.paper_mode:
            return self._simulate_execution(order_plan, ticker)
        else:
            return self._submit_live_order(order_plan, ticker)
    
    def _simulate_execution(self, order_plan: OrderPlan, ticker: str) -> Dict:
        """Simulate order execution for paper trading"""
        fills = []
        
        for tranche in order_plan.tranches:
            # Simulate fill with realistic slippage
            simulated_price = tranche['price']
            simulated_shares = tranche['shares']
            
            fills.append({
                'shares': simulated_shares,
                'price': simulated_price,
                'timestamp': datetime.now(),
                'execution_type': 'SIMULATED'
            })
        
        return {
            'status': 'FILLED',
            'fills': fills,
            'avg_price': sum(f['price'] * f['shares'] for f in fills) / order_plan.total_shares,
            'commission': 0,
            'simulated': True
        }
    
    def _submit_live_order(self, order_plan: OrderPlan, ticker: str) -> Dict:
        """Submit live order to broker"""
        # Integration with broker API
        # Placeholder implementation
        raise NotImplementedError("Live execution not yet implemented")

"""
============================================================
UNIT TESTS
============================================================

File: tests/test_execution_checker_v2.py
"""

import pytest
from unittest.mock import Mock, patch
from engines.execution_checker_v2 import (
    ExecutionChecker, MarketSnapshot, StrategyProfile, RejectionReason
)
from datetime import datetime

class TestExecutionCheckerV2:
    def setup_method(self):
        self.config = {
            'paper_mode': True,
            'dilution_penalty': 0.5,
            'vix_threshold': 30,
            'sector_vol_threshold': 50,
            'max_slippage_pct': 0.01
        }
        
        self.market_service = Mock()
        self.filings_service = Mock()
        self.checker = ExecutionChecker(self.config, self.market_service, self.filings_service)
    
    def test_low_adv_rejection(self):
        """Test rejection when ADV is below threshold"""
        # Create snapshot with low ADV
        snapshot = MarketSnapshot(
            ticker='PENNY',
            price=1.0,
            adv_30d_shares=50000,  # Below 100K threshold
            adv_30d_dollars=50000,  # At threshold
            top_bid=0.99,
            top_ask=1.01,
            top_of_book_spread_pct=0.02,
            depth_top5_shares=100000,
            depth_top5_dollars=100000,
            volume_today=50000,
            is_halted=False,
            limit_up=False,
            limit_down=False,
            vix=20,
            sector_volatility=25,
            timestamp=datetime.now()
        )
        
        self.market_service.get_snapshot.return_value = snapshot
        self.filings_service.has_recent_offering.return_value = False
        
        result = self.checker.evaluate(
            'PENNY', 1000, 'penny_moonshot', 0.8, {}
        )
        
        assert not result['allowed']
        assert RejectionReason.LOW_ADV.value in result['reason_codes']
        assert result['recommended_size_shares'] == 0
    
    def test_spread_rejection(self):
        """Test rejection when spread is too wide"""
        snapshot = MarketSnapshot(
            ticker='WIDE',
            price=10.0,
            adv_30d_shares=500000,
            adv_30d_dollars=5000000,
            top_bid=9.5,
            top_ask=10.8,  # 13% spread
            top_of_book_spread_pct=0.13,
            depth_top5_shares=100000,
            depth_top5_dollars=1000000,
            volume_today=100000,
            is_halted=False,
            limit_up=False,
            limit_down=False,
            vix=20,
            sector_volatility=25,
            timestamp=datetime.now()
        )
        
        self.market_service.get_snapshot.return_value = snapshot
        self.filings_service.has_recent_offering.return_value = False
        
        result = self.checker.evaluate(
            'WIDE', 1000, 'penny_moonshot', 0.8, {}
        )
        
        assert not result['allowed']
        assert RejectionReason.HIGH_SPREAD.value in result['reason_codes']
    
    def test_depth_partial_execution(self):
        """Test reduced size when depth insufficient"""
        snapshot = MarketSnapshot(
            ticker='THIN',
            price=5.0,
            adv_30d_shares=200000,
            adv_30d_dollars=1000000,
            top_bid=4.98,
            top_ask=5.02,
            top_of_book_spread_pct=0.008,
            depth_top5_shares=5000,  # Low depth
            depth_top5_dollars=25000,
            volume_today=50000,
            is_halted=False,
            limit_up=False,
            limit_down=False,
            vix=20,
            sector_volatility=25,
            timestamp=datetime.now()
        )
        
        self.market_service.get_snapshot.return_value = snapshot
        self.filings_service.has_recent_offering.return_value = False
        
        result = self.checker.evaluate(
            'THIN', 10000, 'penny_moonshot', 0.8, {}
        )
        
        # Should be allowed but with reduced size
        assert result['allowed']
        assert result['recommended_size_shares'] < 10000
        assert RejectionReason.INSUFFICIENT_DEPTH.value in result['reason_codes']
    
    def test_dilution_penalty(self):
        """Test size reduction with recent dilution"""
        snapshot = MarketSnapshot(
            ticker='DILUTE',
            price=10.0,
            adv_30d_shares=1000000,
            adv_30d_dollars=10000000,
            top_bid=9.98,
            top_ask=10.02,
            top_of_book_spread_pct=0.004,
            depth_top5_shares=500000,
            depth_top5_dollars=5000000,
            volume_today=200000,
            is_halted=False,
            limit_up=False,
            limit_down=False,
            vix=20,
            sector_volatility=25,
            timestamp=datetime.now()
        )
        
        self.market_service.get_snapshot.return_value = snapshot
        self.filings_service.has_recent_offering.return_value = True
        
        result = self.checker.evaluate(
            'DILUTE', 5000, 'smallcap_compounder', 0.8, {}
        )
        
        # Should have dilution flag and reduced size
        assert RejectionReason.DILUTION_RISK.value in result['reason_codes']
        assert result['diagnostics']['dilution_flag'] == True
        
        # Size should be penalized
        normal_size = self.checker._compute_size(snapshot, 0.8, 
                                                self.checker.strategies['smallcap_compounder'], 
                                                False)
        dilution_size = result['recommended_size_shares']
        assert dilution_size < normal_size
    
    def test_market_halt_rejection(self):
        """Test rejection when market is halted"""
        snapshot = MarketSnapshot(
            ticker='HALTED',
            price=10.0,
            adv_30d_shares=1000000,
            adv_30d_dollars=10000000,
            top_bid=10.0,
            top_ask=10.0,
            top_of_book_spread_pct=0.0,
            depth_top5_shares=500000,
            depth_top5_dollars=5000000,
            volume_today=0,
            is_halted=True,  # Halted
            limit_up=False,
            limit_down=False,
            vix=20,
            sector_volatility=25,
            timestamp=datetime.now()
        )
        
        self.market_service.get_snapshot.return_value = snapshot
        
        result = self.checker.evaluate(
            'HALTED', 1000, 'penny_moonshot', 0.8, {}
        )
        
        assert not result['allowed']
        assert RejectionReason.MARKET_HALTED.value in result['reason_codes']
    
    def test_volatility_override(self):
        """Test rejection when VIX is too high"""
        snapshot = MarketSnapshot(
            ticker='VOLATILE',
            price=10.0,
            adv_30d_shares=1000000,
            adv_30d_dollars=10000000,
            top_bid=9.98,
            top_ask=10.02,
            top_of_book_spread_pct=0.004,
            depth_top5_shares=500000,
            depth_top5_dollars=5000000,
            volume_today=200000,
            is_halted=False,
            limit_up=False,
            limit_down=False,
            vix=35,  # Above threshold
            sector_volatility=25,
            timestamp=datetime.now()
        )
        
        self.market_service.get_snapshot.return_value = snapshot
        self.filings_service.has_recent_offering.return_value = False
        
        result = self.checker.evaluate(
            'VOLATILE', 1000, 'penny_moonshot', 0.8, {}
        )
        
        assert not result['allowed']
        assert RejectionReason.VOLATILITY_OVERRIDE.value in result['reason_codes']
    
    def test_legal_review_required(self):
        """Test rejection when legal review is needed"""
        snapshot = MarketSnapshot(
            ticker='LEGAL',
            price=10.0,
            adv_30d_shares=1000000,
            adv_30d_dollars=10000000,
            top_bid=9.98,
            top_ask=10.02,
            top_of_book_spread_pct=0.004,
            depth_top5_shares=500000,
            depth_top5_dollars=5000000,
            volume_today=200000,
            is_halted=False,
            limit_up=False,
            limit_down=False,
            vix=20,
            sector_volatility=25,
            timestamp=datetime.now()
        )
        
        self.market_service.get_snapshot.return_value = snapshot
        
        # Evidence with cross-border filing
        evidence = {'cross_border': True}
        
        result = self.checker.evaluate(
            'LEGAL', 1000, 'penny_moonshot', 0.8, evidence
        )
        
        assert not result['allowed']
        assert RejectionReason.LEGAL_REVIEW_REQUIRED.value in result['reason_codes']
    
    def test_successful_execution_plan(self):
        """Test successful execution with order plan"""
        snapshot = MarketSnapshot(
            ticker='GOOD',
            price=10.0,
            adv_30d_shares=1000000,
            adv_30d_dollars=10000000,
            top_bid=9.98,
            top_ask=10.02,
            top_of_book_spread_pct=0.004,
            depth_top5_shares=500000,
            depth_top5_dollars=5000000,
            volume_today=200000,
            is_halted=False,
            limit_up=False,
            limit_down=False,
            vix=20,
            sector_volatility=25,
            timestamp=datetime.now()
        )
        
        self.market_service.get_snapshot.return_value = snapshot
        self.filings_service.has_recent_offering.return_value = False
        
        result = self.checker.evaluate(
            'GOOD', 5000, 'smallcap_compounder', 0.8, {}
        )
        
        assert result['allowed']
        assert result['recommended_size_shares'] > 0
        assert result['order_plan'] is not None
        assert result['order_plan'].total_shares == result['recommended_size_shares']
        assert result['order_plan'].max_slippage_pct <= 0.01
    
    def test_paper_trading_simulation(self):
        """Test paper trading mode simulation"""
        snapshot = MarketSnapshot(
            ticker='PAPER',
            price=10.0,
            adv_30d_shares=1000000,
            adv_30d_dollars=10000000,
            top_bid=9.98,
            top_ask=10.02,
            top_of_book_spread_pct=0.004,
            depth_top5_shares=500000,
            depth_top5_dollars=5000000,
            volume_today=200000,
            is_halted=False,
            limit_up=False,
            limit_down=False,
            vix=20,
            sector_volatility=25,
            timestamp=datetime.now()
        )
        
        self.market_service.get_snapshot.return_value = snapshot
        self.filings_service.has_recent_offering.return_value = False
        
        result = self.checker.evaluate(
            'PAPER', 1000, 'penny_moonshot', 0.8, {}
        )
        
        # Execute in paper mode
        execution_result = self.checker.execute_order(result['order_plan'], 'PAPER')
        
        assert execution_result['simulated'] == True
        assert execution_result['status'] == 'FILLED'
        assert len(execution_result['fills']) > 0
        assert execution_result['commission'] == 0

"""
============================================================
INTEGRATION TESTS
============================================================

File: tests/test_execution_integration_v2.py
"""

def test_end_to_end_paper_flow():
    """Test full flow from signal to simulated execution"""
    # This would integrate with the actual confluence service
    # and execution checker
    pass

def test_market_regime_adjustments():
    """Test that high volatility triggers tighter controls"""
    pass

def test_historical_replay():
    """Test against historical market data"""
    pass

""" 
============================================================
MONITORING CONFIGURATION
============================================================

Add to metrics collection:
- execution_checks.total
- execution_checks.{strategy}
- execution_checks.allowed
- execution_checks.rejections.{reason}
- execution.recommended_size_distribution
- execution.slippage_estimated_vs_actual
- execution.participation_rate

Alerts:
- execution_checks.rejection_rate > 20% for 1 hour
- execution.slippage_actual > estimated by 2x for 3 trades
- execution.dilution_flags spike > 3x baseline
============================================================
"""
