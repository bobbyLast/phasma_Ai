"""
📊 REAL-TIME TOP 10 OPPORTUNITIES DASHBOARD BRAIN

Advanced meta-brain that maintains a live leaderboard of the universe's best trading opportunities.
Continuously evaluates and ranks all potential setups across:

- Kalshi prediction markets
- Cross-market arbitrage opportunities
- Traditional asset signals
- Scenario-based opportunities
- Multi-venue mispricings

Creates a "heatmap of the entire market universe" for instant opportunity identification.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
import math
from collections import defaultdict

from core.runtime_paths import engine_state_path

try:
    from engines.kalshi_engine import KalshiPredictionEngine
    from engines.scenario_graph_engine import ScenarioGraphEngine
    from engines.cross_venue_radar import CrossVenueMispricingRadar
except ImportError:
    # Mocks for testing
    class KalshiPredictionEngine:
        pass
    class ScenarioGraphEngine:
        def __init__(self, *args, **kwargs):
            pass
    class CrossVenueMispricingRadar:
        def __init__(self, *args, **kwargs):
            pass


@dataclass
class OpportunityScore:
    """Scoring components for ranking opportunities."""
    edge_size: float = 0.0  # Size of the edge (probability, arbitrage, etc.)
    confidence: float = 0.0  # Statistical confidence
    liquidity: float = 0.0   # Trading liquidity
    time_decay: float = 0.0  # Urgency factor
    diversification: float = 0.0  # Portfolio diversification benefit
    market_regime: float = 0.0  # Current market conditions alignment
    total_score: float = 0.0

    def calculate_total(self) -> float:
        """Calculate weighted total score."""
        # Weighted scoring formula
        weights = {
            'edge_size': 0.4,
            'confidence': 0.25,
            'liquidity': 0.15,
            'time_decay': 0.1,
            'diversification': 0.05,
            'market_regime': 0.05
        }

        self.total_score = (
            self.edge_size * weights['edge_size'] +
            self.confidence * weights['confidence'] +
            self.liquidity * weights['liquidity'] +
            self.time_decay * weights['time_decay'] +
            self.diversification * weights['diversification'] +
            self.market_regime * weights['market_regime']
        )

        return self.total_score


@dataclass
class UniverseOpportunity:
    """Represents any trading opportunity in the universe."""
    id: str
    opportunity_type: str  # 'kalshi_market', 'cross_market_arbitrage', 'scenario_tree', 'mispricing', 'traditional_signal'
    title: str
    description: str
    primary_asset: str
    secondary_assets: List[str] = field(default_factory=list)
    score: OpportunityScore = field(default_factory=OpportunityScore)
    expected_return: float = 0.0
    risk_level: str = 'medium'  # 'low', 'medium', 'high'
    time_horizon: str = 'medium'  # 'short', 'medium', 'long'
    confidence_level: float = 0.0
    recommended_position_size: float = 0.0
    rationale: str = ""
    action_required: str = ""
    tags: Set[str] = field(default_factory=set)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.opportunity_type,
            'title': self.title,
            'description': self.description,
            'primary_asset': self.primary_asset,
            'secondary_assets': self.secondary_assets,
            'score': {
                'edge_size': self.score.edge_size,
                'confidence': self.score.confidence,
                'liquidity': self.score.liquidity,
                'time_decay': self.score.time_decay,
                'diversification': self.score.diversification,
                'market_regime': self.score.market_regime,
                'total_score': self.score.total_score
            },
            'expected_return': self.expected_return,
            'risk_level': self.risk_level,
            'time_horizon': self.time_horizon,
            'confidence_level': self.confidence_level,
            'recommended_position_size': self.recommended_position_size,
            'rationale': self.rationale,
            'action_required': self.action_required,
            'tags': list(self.tags),
            'last_updated': self.last_updated.isoformat(),
            'metadata': self.metadata
        }


class Top10OpportunitiesDashboard:
    """DEMO DATA dashboard — sample opportunities, not live production signals."""
    """
    📊 Real-Time Top 10 Opportunities Dashboard Brain

    The "market universe heatmap" - continuously evaluates and ranks every potential
    trading opportunity across all engines and venues.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine,
                 scenario_graph: ScenarioGraphEngine,
                 mispricing_radar: CrossVenueMispricingRadar):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph
        self.mispricing_radar = mispricing_radar

        self.opportunities: Dict[str, UniverseOpportunity] = {}
        self.top_10_cache: List[UniverseOpportunity] = []
        self.last_refresh: datetime = datetime.min
        self.refresh_interval = timedelta(minutes=5)  # Refresh every 5 minutes
        self.dashboard_file = engine_state_path("top_10_dashboard.json")

        # Initialize with sample data
        self._initialize_sample_opportunities()
        self._load_dashboard()

    def _initialize_sample_opportunities(self):
        """Initialize with diverse sample opportunities for testing."""
        opportunities = [
            # Kalshi markets
            UniverseOpportunity(
                id="kalshi_fed_cut",
                opportunity_type="kalshi_market",
                title="Fed Rate Cut 0.25% in March 2025",
                description="Federal Reserve expected to cut rates by 0.25% in March",
                primary_asset="FED_RATE_CUT",
                score=OpportunityScore(edge_size=0.65, confidence=0.8, liquidity=0.7, time_decay=0.9),
                expected_return=0.15,
                risk_level="medium",
                time_horizon="medium",
                rationale="Strong probability edge in liquid market with upcoming FOMC meeting",
                action_required="Buy YES position on Kalshi",
                tags={"macro", "central_bank", "high_probability"}
            ),

            UniverseOpportunity(
                id="kalshi_btc_200k",
                opportunity_type="kalshi_market",
                title="Bitcoin Hits $200K by End of 2025",
                description="Prediction market for Bitcoin reaching $200K target",
                primary_asset="BTC-USD",
                score=OpportunityScore(edge_size=0.25, confidence=0.7, liquidity=0.8, time_decay=0.6),
                expected_return=0.08,
                risk_level="high",
                time_horizon="long",
                rationale="BTC price prediction with significant upside potential",
                action_required="Buy YES on Kalshi BTC200K market",
                tags={"crypto", "price_target", "long_term"}
            ),

            # Cross-market arbitrage
            UniverseOpportunity(
                id="arbitrage_btc_kalshi_options",
                opportunity_type="cross_market_arbitrage",
                title="BTC Price Target: Kalshi vs Options Mispricing",
                description="Kalshi shows 25% probability, options imply 40% - buy Kalshi sell options",
                primary_asset="BTC-USD",
                secondary_assets=["BTC options"],
                score=OpportunityScore(edge_size=0.15, confidence=0.75, liquidity=0.6, time_decay=0.8),
                expected_return=0.12,
                risk_level="medium",
                time_horizon="medium",
                rationale="Multi-venue probability disagreement creates arbitrage opportunity",
                action_required="Buy Kalshi YES, sell equivalent options position",
                tags={"arbitrage", "multi_venue", "quantitative"}
            ),

            # Scenario-based opportunities
            UniverseOpportunity(
                id="scenario_soft_landing",
                opportunity_type="scenario_tree",
                title="Soft Landing Scenario: Fed Cuts + Growth Continues",
                description="Complete scenario: Fed rate cut + low inflation + SPY/QQQ up + BTC risk-on",
                primary_asset="SPY",
                secondary_assets=["QQQ", "BTC-USD"],
                score=OpportunityScore(edge_size=0.55, confidence=0.6, liquidity=0.9, time_decay=0.7),
                expected_return=0.18,
                risk_level="medium",
                time_horizon="medium",
                rationale="Coordinated scenario with multiple reinforcing signals",
                action_required="Buy SPY calls, QQQ calls, BTC positions",
                tags={"scenario", "macro", "multi_asset"}
            ),

            # Traditional signals
            UniverseOpportunity(
                id="ceo_apple_tim_cook",
                opportunity_type="traditional_signal",
                title="Tim Cook Apple CEO Reappointment Cross-Market",
                description="High probability Tim Cook remains Apple CEO - stock impact opportunity",
                primary_asset="AAPL",
                score=OpportunityScore(edge_size=0.75, confidence=0.8, liquidity=0.9, time_decay=0.5),
                expected_return=0.25,
                risk_level="low",
                time_horizon="long",
                rationale="CEO track record analysis shows positive Apple stock impact",
                action_required="Buy AAPL calls with 6-12 month expiry",
                tags={"ceo", "apple", "fundamental"}
            ),

            # AI breakthrough opportunity
            UniverseOpportunity(
                id="ai_breakthrough_2025",
                opportunity_type="kalshi_market",
                title="Major AI Breakthrough in 2025",
                description="Prediction market for significant AI advancement this year",
                primary_asset="NVDA",
                secondary_assets=["MSFT", "GOOGL", "META"],
                score=OpportunityScore(edge_size=0.45, confidence=0.5, liquidity=0.7, time_decay=0.9),
                expected_return=0.22,
                risk_level="high",
                time_horizon="medium",
                rationale="AI sector catalyst with broad market implications",
                action_required="Buy NVDA calls, consider AI sector ETF",
                tags={"ai", "breakthrough", "sector_catalyst"}
            ),

            # Oil crisis scenario
            UniverseOpportunity(
                id="oil_crisis_scenario",
                opportunity_type="scenario_tree",
                title="Oil Crisis Scenario: $150+ Oil in 2025",
                description="Geopolitical oil disruption scenario with energy stock impacts",
                primary_asset="XOM",
                secondary_assets=["CVX", "BTC-USD"],
                score=OpportunityScore(edge_size=0.35, confidence=0.6, liquidity=0.8, time_decay=0.4),
                expected_return=0.16,
                risk_level="high",
                time_horizon="medium",
                rationale="Oil supply disruption scenario with risk-off crypto implications",
                action_required="Buy XOM/CVX calls, consider BTC puts as hedge",
                tags={"commodity", "geopolitical", "energy"}
            ),

            # FDA approval opportunity
            UniverseOpportunity(
                id="fda_ai_drug_approval",
                opportunity_type="cross_market_arbitrage",
                title="FDA AI Drug Approval - Biotech Impact",
                description="FDA approves AI-assisted drug treatment with biotech stock implications",
                primary_asset="Biotech ETF",
                secondary_assets=["NVDA", "MSFT"],
                score=OpportunityScore(edge_size=0.9, confidence=0.8, liquidity=0.5, time_decay=0.6),
                expected_return=0.35,
                risk_level="high",
                time_horizon="medium",
                rationale="High-impact FDA approval with AI/healthcare crossover potential",
                action_required="Buy biotech ETF, consider AI healthcare positions",
                tags={"fda", "biotech", "ai_healthcare"}
            ),

            # Inflation scenario
            UniverseOpportunity(
                id="inflation_shock_scenario",
                opportunity_type="scenario_tree",
                title="Inflation Shock: CPI Exceeds 3% in 2025",
                description="Inflationary scenario with broad market implications",
                primary_asset="SPY",
                secondary_assets=["BTC-USD", "GLD"],
                score=OpportunityScore(edge_size=0.4, confidence=0.55, liquidity=0.9, time_decay=0.3),
                expected_return=0.14,
                risk_level="medium",
                time_horizon="short",
                rationale="Inflation scenario analysis shows defensive positioning needed",
                action_required="Buy TIPS/gold, reduce growth exposure",
                tags={"inflation", "defensive", "macro"}
            ),

            # Election scenario
            UniverseOpportunity(
                id="election_dem_win_2024",
                opportunity_type="kalshi_market",
                title="Democrat Wins 2024 US Election",
                description="Election outcome prediction with market implications",
                primary_asset="SPY",
                secondary_assets=["NVDA", "XOM"],
                score=OpportunityScore(edge_size=0.52, confidence=0.6, liquidity=0.9, time_decay=0.95),
                expected_return=0.20,
                risk_level="medium",
                time_horizon="short",
                rationale="Election outcome drives sector rotation and market sentiment",
                action_required="Position for Democratic policy preferences",
                tags={"election", "political", "sector_rotation"}
            )
        ]

        for opp in opportunities:
            opp.score.calculate_total()
            self.opportunities[opp.id] = opp

    def _load_dashboard(self):
        """Load existing dashboard data."""
        if os.path.exists(self.dashboard_file):
            try:
                with open(self.dashboard_file, 'r') as f:
                    data = json.load(f)
                print(f"📊 Loaded dashboard: {len(data.get('opportunities', {}))} opportunities")
            except Exception as e:
                print(f"⚠️ Error loading dashboard: {e}")

    def _save_dashboard(self):
        """Save current dashboard state."""
        data = {
            'opportunities': {
                opp_id: opp.to_dict()
                for opp_id, opp in self.opportunities.items()
            },
            'top_10_cache': [opp.to_dict() for opp in self.top_10_cache],
            'last_refresh': self.last_refresh.isoformat(),
            'timestamp': datetime.now().isoformat()
        }

        with open(self.dashboard_file, 'w') as f:
            json.dump(data, f, indent=2)

    def refresh_opportunities(self, force: bool = False) -> bool:
        """Refresh all opportunities from engines. Returns True if refreshed."""
        now = datetime.now()
        if not force and now - self.last_refresh < self.refresh_interval:
            return False  # Not time to refresh yet

        print("🔄 Refreshing Top 10 Opportunities Dashboard...")

        # In production, this would gather data from all engines
        # For now, we work with our initialized data

        # Update scores based on current market conditions
        self._update_opportunity_scores()

        # Recalculate top 10
        self._recalculate_top_10()

        self.last_refresh = now
        self._save_dashboard()
        return True

    def _update_opportunity_scores(self):
        """Update opportunity scores based on current conditions (DEMO DATA — not production signals)."""
        import os
        demo_mode = os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")
        for opp in self.opportunities.values():
            age_hours = (datetime.now() - opp.last_updated).total_seconds() / 3600
            # Deterministic time-decay adjustment (no random noise in production)
            decay_adj = max(-0.05, min(0.05, -age_hours / 480.0))
            if demo_mode:
                import random
                decay_adj += random.uniform(-0.05, 0.05)
            opp.score.edge_size = min(1.0, max(0.0, opp.score.edge_size + decay_adj))

            # Time decay for older opportunities
            age_hours = (datetime.now() - opp.last_updated).total_seconds() / 3600
            opp.score.time_decay = max(0.1, 1.0 - (age_hours / 24))  # Decay over 24 hours

            opp.score.calculate_total()
            opp.last_updated = datetime.now()

    def _recalculate_top_10(self):
        """Recalculate the top 10 opportunities."""
        all_opps = list(self.opportunities.values())
        all_opps.sort(key=lambda x: x.score.total_score, reverse=True)
        self.top_10_cache = all_opps[:10]

    def get_top_10_dashboard(self) -> Dict[str, Any]:
        """Get the current top 10 opportunities dashboard."""
        self.refresh_opportunities()

        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'last_refresh': self.last_refresh.isoformat(),
            'total_opportunities': len(self.opportunities),
            'top_10': []
        }

        for i, opp in enumerate(self.top_10_cache, 1):
            opp_data = opp.to_dict()
            opp_data['rank'] = i
            dashboard['top_10'].append(opp_data)

        return dashboard

    def get_opportunity_by_id(self, opp_id: str) -> Optional[UniverseOpportunity]:
        """Get detailed information about a specific opportunity."""
        return self.opportunities.get(opp_id)

    def get_opportunities_by_type(self, opp_type: str) -> List[UniverseOpportunity]:
        """Get all opportunities of a specific type."""
        return [opp for opp in self.opportunities.values() if opp.opportunity_type == opp_type]

    def get_opportunities_by_asset(self, asset: str) -> List[UniverseOpportunity]:
        """Get all opportunities involving a specific asset."""
        return [opp for opp in self.opportunities.values()
                if opp.primary_asset == asset or asset in opp.secondary_assets]

    def get_opportunities_by_tag(self, tag: str) -> List[UniverseOpportunity]:
        """Get all opportunities with a specific tag."""
        return [opp for opp in self.opportunities.values() if tag in opp.tags]

    def get_portfolio_allocation_suggestion(self, capital: float = 10000) -> Dict[str, Any]:
        """Suggest portfolio allocation across top opportunities."""
        top_opps = self.top_10_cache[:5]  # Use top 5 for allocation

        if not top_opps:
            return {'error': 'No opportunities available'}

        # Simple equal-weight allocation
        allocation_per_opp = capital / len(top_opps)

        portfolio = {
            'total_capital': capital,
            'allocation_strategy': 'equal_weight_top_5',
            'allocations': []
        }

        for opp in top_opps:
            # Scale position size by opportunity score
            position_multiplier = opp.score.total_score / 0.5  # Normalize around 0.5
            position_size = min(allocation_per_opp * position_multiplier, capital * 0.3)  # Max 30% per position

            allocation = {
                'opportunity_id': opp.id,
                'title': opp.title,
                'type': opp.opportunity_type,
                'allocated_capital': position_size,
                'expected_return': position_size * opp.expected_return,
                'risk_level': opp.risk_level,
                'action_required': opp.action_required,
                'score': opp.score.total_score
            }

            portfolio['allocations'].append(allocation)

        return portfolio

    def get_market_heatmap(self) -> Dict[str, Any]:
        """Get a heatmap view of opportunities by category and asset."""
        heatmap = {
            'by_type': defaultdict(int),
            'by_asset': defaultdict(int),
            'by_risk_level': defaultdict(int),
            'by_time_horizon': defaultdict(int),
            'by_tag': defaultdict(int)
        }

        for opp in self.opportunities.values():
            heatmap['by_type'][opp.opportunity_type] += 1
            heatmap['by_asset'][opp.primary_asset] += 1
            heatmap['by_risk_level'][opp.risk_level] += 1
            heatmap['by_time_horizon'][opp.time_horizon] += 1

            for tag in opp.tags:
                heatmap['by_tag'][tag] += 1

        return dict(heatmap)


# Test/demo functions
async def test_top_10_dashboard():
    """Test the Top 10 Opportunities Dashboard."""
    print("📊 TESTING TOP 10 OPPORTUNITIES DASHBOARD")
    print("=" * 50)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)
    mispricing_radar = CrossVenueMispricingRadar(kalshi, scenario_graph)

    dashboard = Top10OpportunitiesDashboard(kalshi, scenario_graph, mispricing_radar)

    print(f"🎯 Initialized with {len(dashboard.opportunities)} total opportunities")

    # Force refresh to test
    dashboard.refresh_opportunities(force=True)

    # Test top 10 dashboard
    print("\n🥇 TOP 10 OPPORTUNITIES DASHBOARD:")
    top_10 = dashboard.get_top_10_dashboard()

    for opp in top_10['top_10']:
        print(f"#{opp['rank']}: {opp['title']}")
        print(f"   Type: {opp['type']} | Asset: {opp['primary_asset']}")
        print(f"   Score: {opp['score']['total_score']:.3f} | Expected Return: {opp['expected_return']:.1%}")
        print(f"   Risk: {opp['risk_level']} | Time: {opp['time_horizon']}")
        print(f"   → {opp['action_required']}")
        print()

    # Test filtering
    print("🎯 FILTERING EXAMPLES:")
    print(f"Kalshi markets: {len(dashboard.get_opportunities_by_type('kalshi_market'))}")
    print(f"Arbitrage opportunities: {len(dashboard.get_opportunities_by_type('cross_market_arbitrage'))}")
    print(f"AI-tagged opportunities: {len(dashboard.get_opportunities_by_tag('ai'))}")
    print(f"BTC-related opportunities: {len(dashboard.get_opportunities_by_asset('BTC-USD'))}")

    # Test portfolio allocation
    print("\n💰 PORTFOLIO ALLOCATION SUGGESTION ($10,000):")
    portfolio = dashboard.get_portfolio_allocation_suggestion(10000)

    for alloc in portfolio['allocations']:
        print(f"   • {alloc['title'][:40]}...: ${alloc['allocated_capital']:.0f} ({alloc['risk_level']} risk)")

    # Test market heatmap
    print("\n🌡️ MARKET HEATMAP:")
    heatmap = dashboard.get_market_heatmap()
    print(f"   By Type: {dict(heatmap['by_type'])}")
    print(f"   By Risk: {dict(heatmap['by_risk_level'])}")
    print(f"   Top Tags: {dict(sorted(heatmap['by_tag'].items(), key=lambda x: x[1], reverse=True)[:5])}")

    print("\n✅ Top 10 Opportunities Dashboard test complete!")


if __name__ == "__main__":
    asyncio.run(test_top_10_dashboard())
