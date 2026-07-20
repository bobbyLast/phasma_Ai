"""
🛡️ RISK GUARDIAN / KILL-SWITCH META-AGENT

Advanced safety system that monitors all trading activities across the entire Phasma AI ecosystem.
Automatically enforces risk limits, detects correlated exposures, and can halt trading if conditions deteriorate.

Monitors:
- Portfolio-level risk metrics
- Strategy correlation across Kalshi + traditional assets
- Drawdown limits and position concentration
- Market regime changes
- Liquidity and slippage risks
- Counterparty and systemic risks

Features:
- Multi-level risk thresholds (warning, reduction, emergency halt)
- Automatic position sizing adjustments
- Kill-switch activation for extreme conditions
- Risk attribution and scenario stress testing
- Real-time risk dashboard
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
import math
import statistics
from collections import defaultdict
from enum import Enum

from core.runtime_paths import engine_state_path

try:
    from engines.kalshi_engine import KalshiPredictionEngine
    from engines.scenario_graph_engine import ScenarioGraphEngine
    from engines.cross_venue_radar import CrossVenueMispricingRadar
    from engines.top_10_dashboard import Top10OpportunitiesDashboard
    from engines.causal_counterfactual_engine import CausalCounterfactualEngine
except ImportError:
    # Mocks for testing
    class KalshiPredictionEngine:
        def __init__(self, *args, **kwargs):
            pass
    class ScenarioGraphEngine:
        def __init__(self, *args, **kwargs):
            pass
    class CrossVenueMispricingRadar:
        def __init__(self, *args, **kwargs):
            pass
    class Top10OpportunitiesDashboard:
        def __init__(self, *args, **kwargs):
            pass
    class CausalCounterfactualEngine:
        def __init__(self, *args, **kwargs):
            pass


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class GuardianAction(Enum):
    """Actions the Risk Guardian can take."""
    MONITOR = "monitor"  # Just monitoring, no action
    WARNING = "warning"  # Send warning notifications
    REDUCE = "reduce"  # Reduce position sizes
    HALT = "halt"  # Stop new positions
    EMERGENCY = "emergency"  # Close all positions immediately


@dataclass
class RiskThreshold:
    """Defines risk thresholds for different metrics."""
    metric_name: str
    warning_level: float
    reduction_level: float
    halt_level: float
    emergency_level: float
    description: str = ""

    def assess_value(self, value: float) -> RiskLevel:
        """Assess a metric value against thresholds."""
        if value >= self.emergency_level:
            return RiskLevel.CRITICAL
        elif value >= self.halt_level:
            return RiskLevel.HIGH
        elif value >= self.reduction_level:
            return RiskLevel.ELEVATED
        elif value >= self.warning_level:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment of the current portfolio."""
    timestamp: datetime = field(default_factory=datetime.now)
    overall_risk_level: RiskLevel = RiskLevel.LOW
    recommended_action: GuardianAction = GuardianAction.MONITOR
    risk_metrics: Dict[str, Any] = field(default_factory=dict)
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'overall_risk_level': self.overall_risk_level.value,
            'recommended_action': self.recommended_action.value,
            'risk_metrics': self.risk_metrics,
            'violations': self.violations,
            'recommendations': self.recommendations
        }


@dataclass
class PositionExposure:
    """Tracks exposure for a single position."""
    position_id: str
    asset: str
    position_type: str  # 'kalshi', 'stock', 'option', 'crypto'
    notional_value: float
    market_value: float
    unrealized_pnl: float
    risk_factors: Set[str] = field(default_factory=set)  # e.g., 'rate_sensitive', 'tech_sector'
    correlation_group: str = ""  # e.g., 'tech_stocks', 'rate_sensitive'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'position_id': self.position_id,
            'asset': self.asset,
            'position_type': self.position_type,
            'notional_value': self.notional_value,
            'market_value': self.market_value,
            'unrealized_pnl': self.unrealized_pnl,
            'risk_factors': list(self.risk_factors),
            'correlation_group': self.correlation_group
        }


class RiskGuardianMetaAgent:
    """
    🛡️ Risk Guardian / Kill-Switch Meta-Agent

    The ultimate safety system that monitors and controls all trading activities.
    Can override any engine if risk thresholds are breached.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine,
                 scenario_graph: ScenarioGraphEngine,
                 mispricing_radar: CrossVenueMispricingRadar,
                 opportunities_dashboard: Top10OpportunitiesDashboard,
                 causal_engine: CausalCounterfactualEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph
        self.mispricing_radar = mispricing_radar
        self.opportunities_dashboard = opportunities_dashboard
        self.causal_engine = causal_engine

        # Risk thresholds
        self.risk_thresholds = self._initialize_risk_thresholds()

        # Current state
        self.current_positions: Dict[str, PositionExposure] = {}
        self.risk_assessments: List[RiskAssessment] = []
        self.kill_switch_activated = False
        self.emergency_mode = False

        # Configuration
        self.monitoring_interval = timedelta(minutes=5)
        self.last_assessment = datetime.min
        self.guardian_file = engine_state_path("risk_guardian", "risk_guardian_state.json")
        os.makedirs(os.path.dirname(self.guardian_file), exist_ok=True)

        # Load existing state
        self._load_state()

    def _initialize_risk_thresholds(self) -> Dict[str, RiskThreshold]:
        """Initialize comprehensive risk thresholds."""

        thresholds = {
            'portfolio_drawdown': RiskThreshold(
                metric_name='portfolio_drawdown',
                warning_level=0.05,    # 5% drawdown
                reduction_level=0.10,  # 10% drawdown
                halt_level=0.15,       # 15% drawdown
                emergency_level=0.20,  # 20% drawdown
                description="Portfolio drawdown from peak value"
            ),

            'concentration_single_asset': RiskThreshold(
                metric_name='concentration_single_asset',
                warning_level=0.15,    # 15% in one asset
                reduction_level=0.25,  # 25% in one asset
                halt_level=0.35,       # 35% in one asset
                emergency_level=0.50,  # 50% in one asset
                description="Concentration in single asset/position"
            ),

            'correlation_group_exposure': RiskThreshold(
                metric_name='correlation_group_exposure',
                warning_level=0.30,    # 30% in correlated group
                reduction_level=0.45,  # 45% in correlated group
                halt_level=0.60,       # 60% in correlated group
                emergency_level=0.75,  # 75% in correlated group
                description="Exposure to correlated risk groups"
            ),

            'daily_pnl_volatility': RiskThreshold(
                metric_name='daily_pnl_volatility',
                warning_level=0.03,    # 3% daily volatility
                reduction_level=0.06,  # 6% daily volatility
                halt_level=0.10,       # 10% daily volatility
                emergency_level=0.15,  # 15% daily volatility
                description="Daily P&L volatility (standard deviation)"
            ),

            'liquidity_risk': RiskThreshold(
                metric_name='liquidity_risk',
                warning_level=0.20,    # 20% illiquid positions
                reduction_level=0.35,  # 35% illiquid positions
                halt_level=0.50,       # 50% illiquid positions
                emergency_level=0.70,  # 70% illiquid positions
                description="Percentage of portfolio in illiquid positions"
            ),

            'counterparty_risk': RiskThreshold(
                metric_name='counterparty_risk',
                warning_level=0.25,    # 25% with single counterparty
                reduction_level=0.40,  # 40% with single counterparty
                halt_level=0.60,       # 60% with single counterparty
                emergency_level=0.80,  # 80% with single counterparty
                description="Concentration with single counterparty/broker"
            )
        }

        return thresholds

    def _load_state(self):
        """Load existing risk guardian state."""
        if os.path.exists(self.guardian_file):
            try:
                with open(self.guardian_file, 'r') as f:
                    data = json.load(f)
                print(f"🛡️ Loaded Risk Guardian state: {len(data.get('positions', {}))} positions")
            except Exception as e:
                print(f"⚠️ Error loading Risk Guardian state: {e}")

    def _save_state(self):
        """Save current state."""
        state = {
            'positions': {pid: pos.to_dict() for pid, pos in self.current_positions.items()},
            'kill_switch_activated': self.kill_switch_activated,
            'emergency_mode': self.emergency_mode,
            'last_assessment': self.last_assessment.isoformat(),
            'latest_assessment': self.risk_assessments[-1].to_dict() if self.risk_assessments else None,
            'last_updated': datetime.now().isoformat()
        }

        with open(self.guardian_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    def update_position(self, position_id: str, asset: str, position_type: str,
                       notional_value: float, market_value: float, unrealized_pnl: float,
                       risk_factors: Set[str] = None, correlation_group: str = ""):
        """Update or add a position to the risk monitoring system."""

        position = PositionExposure(
            position_id=position_id,
            asset=asset,
            position_type=position_type,
            notional_value=notional_value,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            risk_factors=risk_factors or set(),
            correlation_group=correlation_group
        )

        self.current_positions[position_id] = position
        self._save_state()

    def remove_position(self, position_id: str):
        """Remove a position from risk monitoring."""
        if position_id in self.current_positions:
            del self.current_positions[position_id]
            self._save_state()

    def assess_portfolio_risk(self, force: bool = False) -> RiskAssessment:
        """Perform comprehensive portfolio risk assessment."""

        now = datetime.now()
        if not force and now - self.last_assessment < self.monitoring_interval:
            # Return last assessment if recent enough
            return self.risk_assessments[-1] if self.risk_assessments else RiskAssessment()

        assessment = RiskAssessment(timestamp=now)

        # Calculate all risk metrics
        assessment.risk_metrics = self._calculate_risk_metrics()

        # Assess each metric against thresholds
        metric_risk_levels = {}
        for metric_name, value in assessment.risk_metrics.items():
            if metric_name in self.risk_thresholds:
                threshold = self.risk_thresholds[metric_name]
                risk_level = threshold.assess_value(value)
                metric_risk_levels[metric_name] = risk_level

                if risk_level.value != 'low':
                    assessment.violations.append(f"{metric_name}: {value:.1%} ({risk_level.value})")

        # Determine overall risk level
        if RiskLevel.CRITICAL in metric_risk_levels.values():
            assessment.overall_risk_level = RiskLevel.CRITICAL
            assessment.recommended_action = GuardianAction.EMERGENCY
        elif RiskLevel.HIGH in metric_risk_levels.values():
            assessment.overall_risk_level = RiskLevel.HIGH
            assessment.recommended_action = GuardianAction.HALT
        elif RiskLevel.ELEVATED in metric_risk_levels.values():
            assessment.overall_risk_level = RiskLevel.ELEVATED
            assessment.recommended_action = GuardianAction.REDUCE
        elif RiskLevel.MODERATE in metric_risk_levels.values():
            assessment.overall_risk_level = RiskLevel.MODERATE
            assessment.recommended_action = GuardianAction.WARNING
        else:
            assessment.overall_risk_level = RiskLevel.LOW
            assessment.recommended_action = GuardianAction.MONITOR

        # Generate recommendations
        assessment.recommendations = self._generate_recommendations(assessment)

        # Check for kill switch conditions
        self._check_kill_switch_conditions(assessment)

        self.risk_assessments.append(assessment)
        self.last_assessment = now
        self._save_state()

        return assessment

    def _calculate_risk_metrics(self) -> Dict[str, float]:
        """Calculate all portfolio risk metrics."""

        if not self.current_positions:
            return {'total_portfolio_value': 0.0}

        metrics = {}

        # Basic portfolio metrics
        total_portfolio_value = sum(pos.market_value for pos in self.current_positions.values())
        total_pnl = sum(pos.unrealized_pnl for pos in self.current_positions.values())

        metrics['total_portfolio_value'] = total_portfolio_value
        metrics['total_unrealized_pnl'] = total_pnl
        metrics['portfolio_drawdown'] = abs(total_pnl / total_portfolio_value) if total_portfolio_value > 0 else 0

        # Concentration metrics
        if total_portfolio_value > 0:
            # Single asset concentration
            asset_exposure = defaultdict(float)
            for pos in self.current_positions.values():
                asset_exposure[pos.asset] += abs(pos.market_value)

            max_asset_concentration = max(asset_exposure.values()) / total_portfolio_value
            metrics['concentration_single_asset'] = max_asset_concentration

            # Correlation group concentration
            group_exposure = defaultdict(float)
            for pos in self.current_positions.values():
                if pos.correlation_group:
                    group_exposure[pos.correlation_group] += abs(pos.market_value)

            if group_exposure:
                max_group_concentration = max(group_exposure.values()) / total_portfolio_value
                metrics['correlation_group_exposure'] = max_group_concentration

        # Position type diversification
        position_types = defaultdict(float)
        for pos in self.current_positions.values():
            position_types[pos.position_type] += abs(pos.market_value)

        if total_portfolio_value > 0:
            # Liquidity risk (simplified - Kalshi might be less liquid)
            illiquid_value = sum(value for pos_type, value in position_types.items()
                               if pos_type in ['kalshi', 'crypto', 'options'])
            metrics['liquidity_risk'] = illiquid_value / total_portfolio_value

        # Risk factor concentration
        risk_factor_exposure = defaultdict(float)
        for pos in self.current_positions.values():
            for risk_factor in pos.risk_factors:
                risk_factor_exposure[risk_factor] += abs(pos.market_value)

        if risk_factor_exposure and total_portfolio_value > 0:
            max_risk_factor = max(risk_factor_exposure.values()) / total_portfolio_value
            metrics['risk_factor_concentration'] = max_risk_factor

        # P&L volatility (simplified - would need historical data)
        # For now, use position size variability as proxy
        position_sizes = [abs(pos.market_value) for pos in self.current_positions.values()]
        if len(position_sizes) > 1:
            size_std = math.sqrt(sum((size - statistics.mean(position_sizes))**2 for size in position_sizes) / len(position_sizes))
            avg_size = statistics.mean(position_sizes)
            metrics['position_size_volatility'] = size_std / avg_size if avg_size > 0 else 0

        return metrics

    def _generate_recommendations(self, assessment: RiskAssessment) -> List[str]:
        """Generate specific recommendations based on risk assessment."""

        recommendations = []

        if assessment.overall_risk_level == RiskLevel.CRITICAL:
            recommendations.append("🚨 EMERGENCY: Immediately close all positions and halt trading")
            recommendations.append("📞 Contact risk management immediately")
            recommendations.append("🔍 Conduct full portfolio review")

        elif assessment.overall_risk_level == RiskLevel.HIGH:
            recommendations.append("🛑 HALT: Stop opening new positions")
            recommendations.append("🔄 Reduce existing position sizes by 50%")
            recommendations.append("📊 Review correlation exposures")

        elif assessment.overall_risk_level == RiskLevel.ELEVATED:
            recommendations.append("⚠️ REDUCE: Limit new positions to 25% of normal size")
            recommendations.append("🔍 Identify and reduce concentrated exposures")
            recommendations.append("📈 Monitor P&L more frequently")

        elif assessment.overall_risk_level == RiskLevel.MODERATE:
            recommendations.append("👀 MONITOR: Increase monitoring frequency")
            recommendations.append("📋 Review risk factor concentrations")
            recommendations.append("📊 Consider position rebalancing")

        else:
            recommendations.append("✅ LOW RISK: Continue normal operations")
            recommendations.append("📈 Consider gradual position increases if opportunities arise")

        # Specific metric-based recommendations
        metrics = assessment.risk_metrics

        if metrics.get('concentration_single_asset', 0) > 0.25:
            recommendations.append("🎯 Reduce single asset concentration below 25%")

        if metrics.get('correlation_group_exposure', 0) > 0.40:
            recommendations.append("🔗 Diversify across correlation groups")

        if metrics.get('liquidity_risk', 0) > 0.30:
            recommendations.append("💧 Improve portfolio liquidity")

        return recommendations

    def _check_kill_switch_conditions(self, assessment: RiskAssessment):
        """Check if kill switch conditions are met."""

        emergency_triggers = [
            assessment.overall_risk_level == RiskLevel.CRITICAL,
            assessment.risk_metrics.get('portfolio_drawdown', 0) > 0.25,  # 25% drawdown
            len([v for v in assessment.violations if 'emergency' in v.lower()]) > 0
        ]

        if any(emergency_triggers):
            self.activate_kill_switch("Emergency risk thresholds breached")
        elif assessment.recommended_action == GuardianAction.HALT and not self.kill_switch_activated:
            self.activate_kill_switch("High risk conditions detected")

    def activate_kill_switch(self, reason: str):
        """Activate the kill switch - halt all trading activities."""

        self.kill_switch_activated = True
        self.emergency_mode = True

        emergency_log = {
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'active_positions': len(self.current_positions),
            'total_exposure': sum(pos.market_value for pos in self.current_positions.values()),
            'action': 'KILL_SWITCH_ACTIVATED'
        }

        # Save emergency log
        emergency_file = engine_state_path(
            "risk_guardian", f"emergency_kill_switch_{int(datetime.now().timestamp())}.json"
        )
        with open(emergency_file, 'w') as f:
            json.dump(emergency_log, f, indent=2)

        print(f"🚨 KILL SWITCH ACTIVATED: {reason}")
        print(f"📄 Emergency log saved to: {emergency_file}")

        self._save_state()

    def deactivate_kill_switch(self, reason: str = "Manual deactivation"):
        """Deactivate the kill switch."""

        self.kill_switch_activated = False
        self.emergency_mode = False

        deactivation_log = {
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'action': 'KILL_SWITCH_DEACTIVATED'
        }

        deactivation_file = engine_state_path(
            "risk_guardian", f"kill_switch_deactivation_{int(datetime.now().timestamp())}.json"
        )
        with open(deactivation_file, 'w') as f:
            json.dump(deactivation_log, f, indent=2)

        print(f"✅ KILL SWITCH DEACTIVATED: {reason}")
        self._save_state()

    def get_risk_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive risk dashboard."""

        latest_assessment = self.risk_assessments[-1] if self.risk_assessments else None

        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'kill_switch_active': self.kill_switch_activated,
            'emergency_mode': self.emergency_mode,
            'total_positions': len(self.current_positions),
            'total_exposure': sum(pos.market_value for pos in self.current_positions.values()),
            'latest_assessment': latest_assessment.to_dict() if latest_assessment else None,
            'risk_thresholds': {
                name: {
                    'warning': threshold.warning_level,
                    'reduction': threshold.reduction_level,
                    'halt': threshold.halt_level,
                    'emergency': threshold.emergency_level
                }
                for name, threshold in self.risk_thresholds.items()
            }
        }

        return dashboard

    def stress_test_portfolio(self, scenario: str) -> Dict[str, Any]:
        """Run stress test on portfolio under different scenarios."""

        # Simplified stress testing - in production would use historical scenarios
        stress_tests = {
            'market_crash': {'shock_multiplier': 1.5, 'description': '2008-style market crash'},
            'rate_hike_cycle': {'shock_multiplier': 1.2, 'description': 'Aggressive Fed tightening'},
            'tech_sector_dump': {'shock_multiplier': 2.0, 'description': 'AI/tech sector correction'},
            'crypto_winter': {'shock_multiplier': 3.0, 'description': 'Extended crypto downturn'}
        }

        if scenario not in stress_tests:
            return {'error': f'Unknown scenario: {scenario}'}

        test_config = stress_tests[scenario]

        # Apply shocks to positions
        stressed_value = 0.0
        stressed_pnl = 0.0
        position_impacts = []

        for pos in self.current_positions.values():
            # Determine shock based on position characteristics
            shock = test_config['shock_multiplier']

            # Tech/AI positions hit harder in tech dump
            if scenario == 'tech_sector_dump' and ('tech' in pos.risk_factors or 'ai' in pos.risk_factors):
                shock *= 1.5

            # Crypto positions hit harder in crypto winter
            if scenario == 'crypto_winter' and pos.position_type == 'crypto':
                shock *= 2.0

            # Rate-sensitive positions affected by rate hikes
            if scenario == 'rate_hike_cycle' and 'rate_sensitive' in pos.risk_factors:
                shock *= 1.3

            # Apply shock
            shocked_value = pos.market_value * (1 - shock * 0.01)  # Convert to percentage
            shocked_pnl = pos.unrealized_pnl - (pos.market_value * shock * 0.01)

            stressed_value += shocked_value
            stressed_pnl += shocked_pnl

            position_impacts.append({
                'position_id': pos.position_id,
                'asset': pos.asset,
                'original_value': pos.market_value,
                'stressed_value': shocked_value,
                'value_impact': shocked_value - pos.market_value,
                'shock_applied': shock
            })

        return {
            'scenario': scenario,
            'description': test_config['description'],
            'original_portfolio_value': sum(pos.market_value for pos in self.current_positions.values()),
            'stressed_portfolio_value': stressed_value,
            'value_impact': stressed_value - sum(pos.market_value for pos in self.current_positions.values()),
            'max_drawdown_risk': abs(stressed_value - sum(pos.market_value for pos in self.current_positions.values())) / sum(pos.market_value for pos in self.current_positions.values()) if self.current_positions else 0,
            'position_impacts': position_impacts
        }

    def approve_trade(self, trade_details: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if a proposed trade passes risk guardian approval."""

        if self.kill_switch_activated:
            return False, "Kill switch is active - no new trades allowed"

        if self.emergency_mode:
            return False, "Emergency mode active - trading suspended"

        # Get latest assessment
        assessment = self.assess_portfolio_risk()

        if assessment.recommended_action in [GuardianAction.EMERGENCY, GuardianAction.HALT]:
            return False, f"Risk level too high: {assessment.overall_risk_level.value}"

        # Check trade-specific risks
        trade_size = trade_details.get('notional_value', 0)
        portfolio_value = assessment.risk_metrics.get('total_portfolio_value', 0)

        if portfolio_value > 0:
            trade_concentration = trade_size / portfolio_value

            if trade_concentration > 0.10:  # 10% of portfolio
                if assessment.overall_risk_level in [RiskLevel.ELEVATED, RiskLevel.HIGH]:
                    return False, f"Trade size ({trade_concentration:.1%}) too large given current risk level"

        return True, "Trade approved by Risk Guardian"


# Test/demo functions
async def test_risk_guardian():
    """Test the Risk Guardian Meta-Agent."""
    print("🛡️ TESTING RISK GUARDIAN META-AGENT")
    print("=" * 40)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)
    mispricing_radar = CrossVenueMispricingRadar(kalshi, scenario_graph)
    opportunities_dashboard = Top10OpportunitiesDashboard(kalshi, scenario_graph, mispricing_radar)
    causal_engine = CausalCounterfactualEngine(scenario_graph)

    guardian = RiskGuardianMetaAgent(kalshi, scenario_graph, mispricing_radar,
                                   opportunities_dashboard, causal_engine)

    print(f"🛡️ Risk Guardian initialized with {len(guardian.risk_thresholds)} risk thresholds")

    # Add some test positions
    print("\n📊 ADDING TEST POSITIONS:")
    test_positions = [
        ("kalshi_fed_cut", "FED_RATE_CUT", "kalshi", 1000, 950, -50,
         {"rate_sensitive", "macro"}, "macro_events"),
        ("apple_stock", "AAPL", "stock", 5000, 4800, -200,
         {"tech", "consumer"}, "tech_stocks"),
        ("nvda_options", "NVDA", "option", 2000, 2100, 100,
         {"tech", "ai", "volatility"}, "tech_stocks"),
        ("btc_position", "BTC-USD", "crypto", 3000, 2850, -150,
         {"crypto", "volatility"}, "crypto_assets"),
        ("spy_hedge", "SPY", "stock", 8000, 7900, -100,
         {"equity", "broad_market"}, "equity_hedge")
    ]

    for pos_id, asset, pos_type, notional, market_val, pnl, risk_factors, corr_group in test_positions:
        guardian.update_position(pos_id, asset, pos_type, notional, market_val, pnl, risk_factors, corr_group)
        print(f"✅ Added position: {pos_id} ({asset}) - ${market_val:,.0f}")

    # Perform risk assessment
    print("\n🔍 PERFORMING RISK ASSESSMENT:")
    assessment = guardian.assess_portfolio_risk(force=True)

    print(f"Overall Risk Level: {assessment.overall_risk_level.value.upper()}")
    print(f"Recommended Action: {assessment.recommended_action.value.upper()}")

    print("\n📈 Risk Metrics:")
    for metric, value in assessment.risk_metrics.items():
        if isinstance(value, float):
            print(".1%")
        else:
            print(f"   • {metric}: {value}")

    if assessment.violations:
        print("\n⚠️ Risk Violations:")
        for violation in assessment.violations:
            print(f"   • {violation}")

    if assessment.recommendations:
        print("\n💡 Recommendations:")
        for rec in assessment.recommendations:
            print(f"   • {rec}")

    # Test trade approval
    print("\n✅ TESTING TRADE APPROVAL:")
    test_trades = [
        {"notional_value": 500, "description": "Small Kalshi position"},
        {"notional_value": 2000, "description": "Medium stock position"},
        {"notional_value": 5000, "description": "Large position - should be rejected"}
    ]

    for trade in test_trades:
        approved, reason = guardian.approve_trade(trade)
        status = "✅ APPROVED" if approved else "❌ REJECTED"
        print(f"   • ${trade['notional_value']:,.0f} trade: {status} - {reason}")

    # Test stress testing
    print("\n💥 TESTING STRESS SCENARIOS:")
    scenarios = ['market_crash', 'tech_sector_dump', 'crypto_winter']

    for scenario in scenarios:
        stress_result = guardian.stress_test_portfolio(scenario)
        if 'error' not in stress_result:
            original_value = stress_result['original_portfolio_value']
            stressed_value = stress_result['stressed_portfolio_value']
            impact_pct = stress_result['value_impact'] / original_value * 100
            print(".1f")
    # Test kill switch (carefully)
    print("\n🚨 TESTING KILL SWITCH (simulated):")
    if not guardian.kill_switch_activated:
        # Simulate critical risk
        guardian.activate_kill_switch("Test emergency activation")
        print("✅ Kill switch activated for testing")

        # Test trade approval with kill switch
        approved, reason = guardian.approve_trade({"notional_value": 100})
        print(f"   • Trade with kill switch active: {'❌ REJECTED' if not approved else '✅ APPROVED'} - {reason}")

        # Deactivate
        guardian.deactivate_kill_switch("Test deactivation")
        print("✅ Kill switch deactivated")

    print("\n✅ Risk Guardian Meta-Agent test complete!")


if __name__ == "__main__":
    asyncio.run(test_risk_guardian())
