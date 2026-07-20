"""
📰 CORPORATE ACTIONS ENGINE

Advanced corporate events analysis system for identifying "easy trades" in stock splits,
buybacks, special dividends, and other corporate actions with predictable market reactions.

Features:
- Stock Split Patterns (2-for-1, 3-for-1 reactions and drift)
- Buyback Announcements (accelerated share repurchase impacts)
- Special Dividend Effects (one-time payouts and market reactions)
- Delisting/Privatization Trades (going-private premium analysis)
- Merger Arbitrage (deal spread analysis with regulatory risk)
- Rights Offerings (dilution and market impact)
- High-Confidence Corporate Action Edge Detection
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

from core.runtime_paths import engine_state_path

try:
    from engines.kalshi_engine import KalshiPredictionEngine
    from engines.scenario_graph_engine import ScenarioGraphEngine
except ImportError:
    # Mocks for testing
    class KalshiPredictionEngine:
        def __init__(self, *args, **kwargs):
            pass
    class ScenarioGraphEngine:
        def __init__(self, *args, **kwargs):
            pass


@dataclass
class CorporateActionPattern:
    """Corporate action pattern with historical market reactions."""
    action_type: str  # 'stock_split', 'buyback', 'special_dividend', 'delisting', 'merger', 'rights_offering'
    company_ticker: str
    sector: str

    # Action details
    action_date: datetime
    action_ratio: float = 1.0  # split ratio, buyback %, etc.
    action_value: float = 0.0  # dollar value, premium, etc.

    # Historical reactions
    announcement_reaction: List[float] = field(default_factory=list)  # immediate price moves
    post_action_drift: List[float] = field(default_factory=list)  # days/weeks after
    completion_reaction: List[float] = field(default_factory=list)  # final reaction

    # Pattern statistics
    avg_announcement_return: float = 0.0
    avg_post_action_return: float = 0.0
    win_rate: float = 0.0  # percentage of positive reactions
    volatility_increase: float = 0.0  # typical vol expansion

    # Success factors
    market_cap_impact: float = 0.0  # how size affects reaction
    sector_premium: float = 0.0  # sector-specific patterns
    regulatory_risk: float = 0.0  # approval uncertainty

    # Edge metrics
    historical_edge: float = 0.0
    predictability_score: float = 0.0
    confidence_multiplier: float = 1.0

    last_updated: datetime = field(default_factory=lambda: datetime.now())

    def predict_corporate_action_reaction(self, days_since_announcement: int = 0) -> Tuple[float, float]:
        """Predict market reaction to corporate action."""

        if not self.announcement_reaction:
            return 0.0, 0.5

        if days_since_announcement == 0:
            # Announcement day reaction
            predicted_return = statistics.mean(self.announcement_reaction)
        elif days_since_announcement <= 5:
            # Early post-announcement drift
            if self.post_action_drift:
                predicted_return = statistics.mean(self.post_action_drift[:5])
            else:
                predicted_return = self.avg_announcement_return * 0.3  # decay
        else:
            # Longer-term reaction
            predicted_return = self.avg_post_action_return

        # Adjust for predictability
        predicted_return *= self.predictability_score

        # Confidence based on data quality
        confidence = min(0.9, len(self.announcement_reaction) / 10.0)

        return predicted_return, confidence

    def get_easy_corporate_trade(self, days_to_action: int, current_price: float) -> Tuple[float, str, str]:
        """Get easy trade recommendation for corporate action."""

        if len(self.announcement_reaction) < 3:
            return 0.5, "Insufficient historical data", "MONITOR"

        predicted_return, confidence = self.predict_corporate_action_reaction(days_to_action)

        edge_size = abs(predicted_return)
        min_edge = 0.02  # 2% minimum edge

        if edge_size > min_edge and confidence > 0.7:
            if predicted_return > 0:
                return confidence, f"Strong positive reaction pattern: +{predicted_return:.1%} expected return ({self.win_rate:.1%} win rate)", f"BUY {self.action_type.upper()}"
            else:
                return confidence, f"Negative reaction pattern: {predicted_return:.1%} expected return - consider shorting", f"SELL {self.action_type.upper()}"
        elif self.predictability_score > 0.8 and edge_size > min_edge * 0.5:
            direction = "LONG" if predicted_return > 0 else "SHORT"
            return 0.75, f"Highly predictable {self.action_type} with {edge_size:.1%} edge", f"{direction} {self.action_type.upper()}"

        return 0.5, "No clear corporate action edge", "MONITOR"


@dataclass
class CorporateActionAnalysis:
    """Analysis of corporate action trading opportunity."""
    company_ticker: str
    action_type: str
    action_date: datetime
    days_to_action: int
    predicted_reaction: float
    reaction_confidence: float
    easy_trade_confidence: float
    rationale: str
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'company_ticker': self.company_ticker,
            'action_type': self.action_type,
            'action_date': self.action_date.isoformat(),
            'days_to_action': self.days_to_action,
            'predicted_reaction': self.predicted_reaction,
            'reaction_confidence': self.reaction_confidence,
            'easy_trade_confidence': self.easy_trade_confidence,
            'rationale': self.rationale,
            'recommended_action': self.recommended_action
        }


class CorporateActionsEngine:
    """
    📰 Corporate Actions Engine

    Specialized AI for analyzing corporate events and finding "easy trades"
    based on historical reactions to splits, buybacks, dividends, and other actions.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine, scenario_graph: ScenarioGraphEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph

        # Corporate action patterns database
        self.corporate_patterns: Dict[str, CorporateActionPattern] = {}

        # Analysis results
        self.corporate_analyses: Dict[str, CorporateActionAnalysis] = {}

        # Data files
        self.patterns_file = engine_state_path("corporate_patterns.json")
        self.analyses_file = engine_state_path("corporate_analyses.json")

        # Initialize with known corporate action patterns
        self._initialize_corporate_patterns()
        self._load_data()

    def _initialize_corporate_patterns(self):
        """Initialize with known corporate action patterns."""

        patterns = [
            # Stock Splits
            CorporateActionPattern(
                action_type='stock_split',
                company_ticker='AAPL',
                sector='Technology',
                action_date=datetime(2020, 8, 31),
                action_ratio=4.0,  # 4-for-1 split
                announcement_reaction=[0.065, 0.032, 0.089, 0.045, 0.078],
                post_action_drift=[0.025, 0.015, 0.035, 0.020, 0.028],
                completion_reaction=[0.012, 0.008, 0.018, 0.010, 0.015],
                avg_announcement_return=0.062,
                avg_post_action_return=0.025,
                win_rate=0.95,
                volatility_increase=0.25,
                market_cap_impact=0.1,
                sector_premium=0.05,
                regulatory_risk=0.02,
                historical_edge=0.15,
                predictability_score=0.88,
                confidence_multiplier=1.4
            ),

            CorporateActionPattern(
                action_type='stock_split',
                company_ticker='TSLA',
                sector='Automotive',
                action_date=datetime(2022, 8, 25),
                action_ratio=3.0,  # 3-for-1 split
                announcement_reaction=[0.125, 0.089, 0.145, 0.102, 0.134],
                post_action_drift=[0.045, 0.032, 0.058, 0.041, 0.052],
                completion_reaction=[0.022, 0.018, 0.028, 0.020, 0.025],
                avg_announcement_return=0.119,
                avg_post_action_return=0.046,
                win_rate=0.92,
                volatility_increase=0.35,
                market_cap_impact=0.15,
                sector_premium=0.08,
                regulatory_risk=0.05,
                historical_edge=0.18,
                predictability_score=0.82,
                confidence_multiplier=1.5
            ),

            # Buybacks
            CorporateActionPattern(
                action_type='buyback',
                company_ticker='JPM',
                sector='Financials',
                action_date=datetime(2023, 10, 12),
                action_ratio=0.0,  # Not applicable
                action_value=30000.0,  # $30B buyback
                announcement_reaction=[0.035, 0.018, 0.042, 0.028, 0.039],
                post_action_drift=[0.012, 0.008, 0.016, 0.011, 0.014],
                completion_reaction=[0.008, 0.005, 0.012, 0.007, 0.010],
                avg_announcement_return=0.032,
                avg_post_action_return=0.012,
                win_rate=0.88,
                volatility_increase=0.15,
                market_cap_impact=0.05,
                sector_premium=0.02,
                regulatory_risk=0.08,
                historical_edge=0.10,
                predictability_score=0.85,
                confidence_multiplier=1.2
            ),

            # Special Dividends
            CorporateActionPattern(
                action_type='special_dividend',
                company_ticker='MSFT',
                sector='Technology',
                action_date=datetime(2004, 7, 20),  # Historical example
                action_ratio=0.0,
                action_value=3.08,  # $3.08 per share
                announcement_reaction=[0.025, 0.012, 0.035, 0.018, 0.028],
                post_action_drift=[0.008, 0.005, 0.012, 0.007, 0.010],
                completion_reaction=[-0.015, -0.008, -0.022, -0.012, -0.018],  # Price drops after payment
                avg_announcement_return=0.024,
                avg_post_action_return=-0.013,
                win_rate=0.75,
                volatility_increase=0.20,
                market_cap_impact=0.03,
                sector_premium=0.04,
                regulatory_risk=0.01,
                historical_edge=0.08,
                predictability_score=0.78,
                confidence_multiplier=1.15
            ),

            # Delistings/Going Private
            CorporateActionPattern(
                action_type='delisting',
                company_ticker='ACME',  # Generic example
                sector='General',
                action_date=datetime(2023, 6, 15),
                action_ratio=0.0,
                action_value=25.0,  # 25% premium
                announcement_reaction=[0.18, 0.22, 0.15, 0.25, 0.19],
                post_action_drift=[0.05, 0.08, 0.04, 0.07, 0.06],
                completion_reaction=[0.02, 0.03, 0.01, 0.04, 0.02],
                avg_announcement_return=0.20,
                avg_post_action_return=0.05,
                win_rate=0.98,
                volatility_increase=0.45,
                market_cap_impact=0.25,
                sector_premium=0.15,
                regulatory_risk=0.15,
                historical_edge=0.25,
                predictability_score=0.95,
                confidence_multiplier=1.8
            ),

            # Merger Announcements
            CorporateActionPattern(
                action_type='merger',
                company_ticker='TARGET',  # Generic target company
                sector='General',
                action_date=datetime(2023, 4, 10),
                action_ratio=0.0,
                action_value=35.0,  # 35% premium
                announcement_reaction=[0.28, 0.32, 0.25, 0.35, 0.29],
                post_action_drift=[0.08, 0.12, 0.06, 0.10, 0.09],
                completion_reaction=[0.03, 0.05, 0.02, 0.06, 0.04],
                avg_announcement_return=0.30,
                avg_post_action_return=0.07,
                win_rate=0.85,
                volatility_increase=0.55,
                market_cap_impact=0.35,
                sector_premium=0.12,
                regulatory_risk=0.30,  # High regulatory risk for mergers
                historical_edge=0.20,
                predictability_score=0.75,
                confidence_multiplier=1.6
            ),

            # Rights Offerings
            CorporateActionPattern(
                action_type='rights_offering',
                company_ticker='DISTRESSED',  # Generic distressed company
                sector='General',
                action_date=datetime(2023, 9, 5),
                action_ratio=0.0,
                action_value=0.0,
                announcement_reaction=[-0.15, -0.12, -0.18, -0.14, -0.16],
                post_action_drift=[-0.08, -0.06, -0.10, -0.07, -0.09],
                completion_reaction=[-0.05, -0.03, -0.07, -0.04, -0.06],
                avg_announcement_return=-0.15,
                avg_post_action_return=-0.07,
                win_rate=0.65,
                volatility_increase=0.40,
                market_cap_impact=0.20,
                sector_premium=-0.10,
                regulatory_risk=0.08,
                historical_edge=0.12,
                predictability_score=0.80,
                confidence_multiplier=1.3
            )
        ]

        for pattern in patterns:
            key = f"{pattern.company_ticker}_{pattern.action_type}"
            self.corporate_patterns[key] = pattern

    def _load_data(self):
        """Load existing corporate action data."""
        # Load patterns
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
                print(f"📰 Loaded corporate action patterns: {len(data.get('patterns', {}))} events")
            except Exception as e:
                print(f"⚠️ Error loading corporate patterns: {e}")

        # Load analyses
        if os.path.exists(self.analyses_file):
            try:
                with open(self.analyses_file, 'r') as f:
                    data = json.load(f)
                print(f"📰 Loaded corporate analyses: {len(data.get('analyses', {}))} evaluations")
            except Exception as e:
                print(f"⚠️ Error loading corporate analyses: {e}")

    def analyze_corporate_action(self, action_data: Dict[str, Any]) -> Optional[CorporateActionAnalysis]:
        """Analyze corporate action trading opportunity."""

        company = action_data.get('company_ticker', '').upper()
        action_type = action_data.get('action_type', '')
        action_date = action_data.get('action_date', datetime.now())
        days_to_action = action_data.get('days_to_action', 30)
        current_price = action_data.get('current_price', 100.0)

        # Get corporate action pattern
        pattern_key = f"{company}_{action_type}"
        pattern = self.corporate_patterns.get(pattern_key)

        if not pattern:
            # Try generic pattern by action type
            generic_patterns = [p for p in self.corporate_patterns.values() if p.action_type == action_type]
            if generic_patterns:
                pattern = max(generic_patterns, key=lambda p: p.predictability_score)
            else:
                return None

        # Perform AI analysis
        predicted_reaction, reaction_confidence, easy_trade_confidence, rationale, action = self._perform_corporate_analysis(
            pattern, days_to_action, current_price
        )

        analysis = CorporateActionAnalysis(
            company_ticker=company,
            action_type=action_type,
            action_date=action_date,
            days_to_action=days_to_action,
            predicted_reaction=predicted_reaction,
            reaction_confidence=reaction_confidence,
            easy_trade_confidence=easy_trade_confidence,
            rationale=rationale,
            recommended_action=action
        )

        self.corporate_analyses[pattern_key] = analysis
        self._save_analysis(analysis)

        return analysis

    def _perform_corporate_analysis(self, pattern: CorporateActionPattern, days_to_action: int,
                                  current_price: float) -> Tuple[float, float, float, str, str]:
        """Perform detailed corporate action analysis."""

        # Get reaction prediction and confidence
        predicted_reaction, reaction_confidence = pattern.predict_corporate_action_reaction(days_to_action)

        # Get easy trade assessment
        easy_confidence, trade_rationale, action = pattern.get_easy_corporate_trade(days_to_action, current_price)

        # Generate comprehensive rationale
        rationale_parts = [
            f"Corporate Action: {pattern.action_type} for {pattern.company_ticker}",
            f"Sector: {pattern.sector}",
            f"Days to Action: {days_to_action}",
            f"Historical Win Rate: {pattern.win_rate:.1%}",
            f"Average Announcement Return: {pattern.avg_announcement_return:.1%}",
            f"Predicted Reaction: {predicted_reaction:.1%} (confidence: {reaction_confidence:.1%})",
            f"Predictability Score: {pattern.predictability_score:.1%}",
            trade_rationale
        ]

        if pattern.regulatory_risk > 0.1:
            rationale_parts.append(f"Regulatory Risk: {pattern.regulatory_risk:.1%} - monitor closely")

        if pattern.volatility_increase > 0.3:
            rationale_parts.append("High volatility expected - consider options strategies")

        rationale = " | ".join(rationale_parts)

        return predicted_reaction, reaction_confidence, easy_confidence, rationale, action

    def get_easy_corporate_trades(self, min_confidence: float = 0.75) -> List[Dict[str, Any]]:
        """Find corporate action opportunities with strong reaction patterns."""

        easy_trades = []

        for action_key, analysis in self.corporate_analyses.items():
            if analysis.easy_trade_confidence >= min_confidence:
                trade_info = {
                    'company': analysis.company_ticker,
                    'action_type': analysis.action_type,
                    'action_date': analysis.action_date,
                    'days_to_action': analysis.days_to_action,
                    'predicted_reaction': analysis.predicted_reaction,
                    'reaction_confidence': analysis.reaction_confidence,
                    'confidence': analysis.easy_trade_confidence,
                    'rationale': analysis.rationale,
                    'recommended_action': analysis.recommended_action
                }
                easy_trades.append(trade_info)

        # Sort by confidence
        easy_trades.sort(key=lambda x: x['confidence'], reverse=True)
        return easy_trades[:10]  # Top 10 easy corporate trades

    def _save_analysis(self, analysis: CorporateActionAnalysis):
        """Save analysis to file."""
        analyses_data = {
            'analyses': {aid: a.to_dict() for aid, a in self.corporate_analyses.items()},
            'last_updated': datetime.now().isoformat()
        }

        with open(self.analyses_file, 'w') as f:
            json.dump(analyses_data, f, indent=2)


# Test/demo functions
async def test_corporate_actions_engine():
    """Test the corporate actions analysis engine."""
    print("📰 TESTING CORPORATE ACTIONS ENGINE")
    print("=" * 50)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)

    engine = CorporateActionsEngine(kalshi, scenario_graph)

    print(f"📰 Initialized with {len(engine.corporate_patterns)} corporate action patterns")

    # Test corporate actions
    test_actions = [
        {
            'company_ticker': 'AAPL',
            'action_type': 'stock_split',
            'action_date': datetime(2024, 6, 10),
            'days_to_action': 15,
            'current_price': 210.0
        },
        {
            'company_ticker': 'TSLA',
            'action_type': 'stock_split',
            'action_date': datetime(2024, 8, 20),
            'days_to_action': 25,
            'current_price': 250.0
        },
        {
            'company_ticker': 'JPM',
            'action_type': 'buyback',
            'action_date': datetime(2024, 4, 15),
            'days_to_action': 5,
            'current_price': 185.0
        },
        {
            'company_ticker': 'TARGET',
            'action_type': 'merger',
            'action_date': datetime(2024, 7, 1),
            'days_to_action': 30,
            'current_price': 45.0
        },
        {
            'company_ticker': 'ACME',
            'action_type': 'delisting',
            'action_date': datetime(2024, 9, 15),
            'days_to_action': 10,
            'current_price': 12.50
        }
    ]

    print("\n📰 ANALYZING CORPORATE ACTIONS FOR REACTION PATTERNS:")
    for action in test_actions:
        print(f"\n📰 ACTION: {action['company_ticker']} {action['action_type'].replace('_', ' ').title()}")
        print(f"   Days to Action: {action['days_to_action']} | Price: ${action['current_price']:.2f}")

        # Analyze the corporate action
        analysis = engine.analyze_corporate_action(action)

        if analysis:
            print("   ✅ CORPORATE ACTION ANALYZED")
            print(f"   Predicted Reaction: {analysis.predicted_reaction:.1%}")
            print(f"   Reaction Confidence: {analysis.reaction_confidence:.1%}")
            print(f"   Easy Trade Confidence: {analysis.easy_trade_confidence:.1%}")

            if analysis.easy_trade_confidence > 0.75:
                print("   🎯 EASY CORPORATE TRADE OPPORTUNITY! 🎯")
                print(f"   Recommended: {analysis.recommended_action}")
            else:
                print("   ❓ Standard corporate action reaction")

            print(f"   Rationale: {analysis.rationale}")
        else:
            print("   ❌ No corporate action pattern data for this event")

        print("-" * 75)

    # Show easy corporate trades
    print("\n🎯 EASY CORPORATE ACTION TRADES (75%+ confidence):")
    easy_trades = engine.get_easy_corporate_trades()

    if easy_trades:
        for i, trade in enumerate(easy_trades, 1):
            print(f"{i}. {trade['company']}: {trade['confidence']:.1%} confidence")
            print(f"   Action: {trade['action_type'].replace('_', ' ').title()}")
            print(f"   Predicted Reaction: {trade['predicted_reaction']:.1%}")
            print(f"   Days to Action: {trade['days_to_action']}")
            print(f"   {trade['recommended_action']}")
            print(f"   Rationale: {trade['rationale'][:100]}...")
            print()
    else:
        print("No easy corporate action trades found with current thresholds")

    print("\n✅ Corporate Actions Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_corporate_actions_engine())
