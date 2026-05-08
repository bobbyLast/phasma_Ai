"""
📜 EVENT STRUCTURE ENGINE

Advanced contract analysis system for identifying "easy trades" in prediction markets
based on contract wording, settlement rules, and structural arbitrage opportunities.

Features:
- Contract Language Analysis (NLP parsing of market rules)
- Settlement Rule Assessment (resolution criteria evaluation)
- Asymmetrical Payoff Detection (one-sided risk/reward)
- Impossible Outcome Identification (structurally biased markets)
- Resolution Lag Arbitrage (real-time vs official data discrepancies)
- High-Confidence Structural Trade Identification (rule-based edges)
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
import math
import statistics
import re
from collections import defaultdict

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
class ContractStructure:
    """Analysis of contract structure and wording."""
    contract_id: str
    contract_title: str
    contract_rules: str

    # Structural analysis
    resolution_criteria: List[str] = field(default_factory=list)
    settlement_source: str = ''
    settlement_lag_days: int = 0

    # Risk/reward asymmetry
    upside_scenarios: int = 0  # number of ways to win YES
    downside_scenarios: int = 0  # number of ways to win NO
    payoff_asymmetry: float = 0.0  # imbalance in win conditions

    # Impossible or unlikely outcomes
    impossible_outcomes: List[str] = field(default_factory=list)
    unlikely_conditions: List[str] = field(default_factory=list)

    # Market efficiency factors
    public_attention_bias: float = 0.0  # how much public focus affects pricing
    institutional_edge: float = 0.0  # advantage from better information access

    # Historical performance
    resolution_accuracy: float = 0.0  # how often rules are applied correctly
    dispute_frequency: float = 0.0  # how often contracts are disputed

    # Edge metrics
    structural_edge: float = 0.0  # edge from contract structure alone
    arbitrage_opportunity: bool = False
    confidence_multiplier: float = 1.0

    last_updated: datetime = field(default_factory=lambda: datetime.now())

    def analyze_payoff_asymmetry(self) -> Tuple[float, str]:
        """Analyze if contract has asymmetrical risk/reward."""

        if self.upside_scenarios == 0 or self.downside_scenarios == 0:
            return 0.0, "Insufficient scenario analysis"

        total_scenarios = self.upside_scenarios + self.downside_scenarios
        asymmetry_ratio = abs(self.upside_scenarios - self.downside_scenarios) / total_scenarios

        if asymmetry_ratio > 0.3:  # >30% imbalance
            favored_side = "YES" if self.upside_scenarios > self.downside_scenarios else "NO"
            return asymmetry_ratio, f"Strong asymmetry favoring {favored_side} ({self.upside_scenarios} vs {self.downside_scenarios} scenarios)"
        elif asymmetry_ratio > 0.1:  # >10% imbalance
            favored_side = "YES" if self.upside_scenarios > self.downside_scenarios else "NO"
            return asymmetry_ratio, f"Moderate asymmetry favoring {favored_side}"

        return asymmetry_ratio, "Balanced risk/reward structure"

    def check_resolution_lag_opportunity(self, current_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for arbitrage from resolution lag."""

        if self.settlement_lag_days < 1:
            return False, "No significant settlement lag"

        # Check if real-time data suggests different outcome than current market
        real_time_outcome = current_data.get('real_time_outcome')
        market_price = current_data.get('market_price', 0.5)

        if real_time_outcome is None:
            return False, "No real-time data available"

        # If real-time data clearly shows outcome but market hasn't adjusted
        if real_time_outcome == 'YES' and market_price < 0.8:
            return True, f"Real-time data shows YES outcome but market still pricing {market_price:.1%}"
        elif real_time_outcome == 'NO' and market_price > 0.2:
            return True, f"Real-time data shows NO outcome but market still pricing {market_price:.1%}"

        return False, "Market properly reflects real-time data"

    def get_easy_structural_trade(self, current_market_data: Dict[str, Any]) -> Tuple[float, str, str]:
        """Get easy trade based on contract structure."""

        # Check payoff asymmetry
        asymmetry, asymmetry_reason = self.analyze_payoff_asymmetry()

        # Check resolution lag
        lag_opportunity, lag_reason = self.check_resolution_lag_opportunity(current_market_data)

        # Check impossible outcomes
        impossible_opportunities = []
        if self.impossible_outcomes:
            impossible_opportunities = [outcome for outcome in self.impossible_outcomes
                                      if current_market_data.get('market_price', 0.5) > 0.1]

        # Determine overall confidence and action
        confidence = 0.0
        rationale = ""
        action = "MONITOR"

        if asymmetry > 0.3 and "Strong asymmetry" in asymmetry_reason:
            confidence = 0.85
            favored_side = "YES" if "YES" in asymmetry_reason else "NO"
            rationale = f"Contract structure strongly favors {favored_side}: {asymmetry_reason}"
            action = f"BUY {favored_side} - STRUCTURAL EDGE"
        elif lag_opportunity:
            confidence = 0.9
            rationale = f"Resolution lag arbitrage: {lag_reason}"
            action = "ARBITRAGE RESOLUTION LAG"
        elif impossible_opportunities:
            confidence = 0.95
            rationale = f"Impossible outcome priced in: {', '.join(impossible_opportunities[:2])}"
            action = "BUY NO - IMPOSSIBLE OUTCOME"
        elif asymmetry > 0.1:
            confidence = 0.7
            rationale = f"Moderate structural edge: {asymmetry_reason}"
            action = f"FADE ASYMMETRY - {asymmetry_reason.split()[-1]}"
        else:
            confidence = 0.5
            rationale = "No significant structural edge detected"
            action = "MONITOR"

        return confidence, rationale, action


@dataclass
class EventStructureAnalysis:
    """Analysis of contract structure opportunity."""
    contract_id: str
    contract_title: str
    payoff_asymmetry: float
    resolution_lag_opportunity: bool
    impossible_outcomes_count: int
    structural_edge: float
    easy_trade_confidence: float
    rationale: str
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'contract_id': self.contract_id,
            'contract_title': self.contract_title,
            'payoff_asymmetry': self.payoff_asymmetry,
            'resolution_lag_opportunity': self.resolution_lag_opportunity,
            'impossible_outcomes_count': self.impossible_outcomes_count,
            'structural_edge': self.structural_edge,
            'easy_trade_confidence': self.easy_trade_confidence,
            'rationale': self.rationale,
            'recommended_action': self.recommended_action
        }


class EventStructureEngine:
    """
    📜 Event Structure Engine

    Specialized AI for analyzing prediction market contracts and finding "easy trades"
    based on contract wording, settlement rules, and structural arbitrage.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine, scenario_graph: ScenarioGraphEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph

        # Contract structure database
        self.contract_structures: Dict[str, ContractStructure] = {}

        # Analysis results
        self.structure_analyses: Dict[str, EventStructureAnalysis] = {}

        # Data files
        self.structures_file = "contract_structures.json"
        self.analyses_file = "structure_analyses.json"

        # Initialize with known contract structures
        self._initialize_contract_structures()
        self._load_data()

    def _initialize_contract_structures(self):
        """Initialize with known contract structure patterns."""

        structures = [
            ContractStructure(
                contract_id='PRESIDENTIAL_ELECTION',
                contract_title='Will [Candidate] win the 2024 Presidential Election?',
                contract_rules='Winner determined by official Electoral College vote as certified by Congress',
                resolution_criteria=['Electoral College certification', 'Congressional acceptance', 'No successful legal challenges'],
                settlement_source='Congress',
                settlement_lag_days=30,
                upside_scenarios=1,  # Only one way to win: get majority of electoral votes
                downside_scenarios=1,  # Only one way to lose: don't get majority
                payoff_asymmetry=0.0,
                impossible_outcomes=['Write-in candidate wins without major party nomination'],
                unlikely_conditions=['Electoral College tie requiring House decision'],
                public_attention_bias=0.8,
                institutional_edge=0.2,
                resolution_accuracy=0.98,
                dispute_frequency=0.02,
                structural_edge=0.05,
                arbitrage_opportunity=False,
                confidence_multiplier=1.1
            ),

            ContractStructure(
                contract_id='FED_RATE_DECISION',
                contract_title='Will Fed raise rates by 25bps in [Month]?',
                contract_rules='Based on FOMC statement following scheduled meeting',
                resolution_criteria=['FOMC announcement', '25bps increase specified', 'No conditions or qualifiers'],
                settlement_source='Federal Reserve',
                settlement_lag_days=0,
                upside_scenarios=1,
                downside_scenarios=3,  # No change, 50bps hike, pause
                payoff_asymmetry=0.5,  # More ways to resolve NO
                impossible_outcomes=[],
                unlikely_conditions=['Emergency meeting between scheduled dates'],
                public_attention_bias=0.9,
                institutional_edge=0.3,
                resolution_accuracy=0.99,
                dispute_frequency=0.01,
                structural_edge=0.08,
                arbitrage_opportunity=False,
                confidence_multiplier=1.2
            ),

            ContractStructure(
                contract_id='CELEBRITY_EVENT',
                contract_title='Will [Celebrity] win [Award] at [Event]?',
                contract_rules='Winner as announced at official ceremony',
                resolution_criteria=['Live announcement', 'Official presenter declaration', 'No subsequent revocation'],
                settlement_source='Event organizers',
                settlement_lag_days=0,
                upside_scenarios=1,
                downside_scenarios=10,  # Many other nominees can win
                payoff_asymmetry=0.82,  # Much more likely to lose than win
                impossible_outcomes=['Winner disqualified after announcement'],
                unlikely_conditions=['Tie vote requiring runoff'],
                public_attention_bias=0.95,
                institutional_edge=0.1,
                resolution_accuracy=0.97,
                dispute_frequency=0.03,
                structural_edge=0.12,
                arbitrage_opportunity=False,
                confidence_multiplier=1.25
            ),

            ContractStructure(
                contract_id='WEATHER_RECORD',
                contract_title='Will [Location] set new [Weather] record in [Period]?',
                contract_rules='Based on official weather service measurements',
                resolution_criteria=['Official measurement', 'Surpasses existing record', 'Within specified time period'],
                settlement_source='National Weather Service',
                settlement_lag_days=1,
                upside_scenarios=1,
                downside_scenarios=364,  # Any other day in year
                payoff_asymmetry=0.996,  # Extremely unlikely to happen
                impossible_outcomes=['Measurement error favors record'],
                unlikely_conditions=['Perfect storm of weather conditions'],
                public_attention_bias=0.6,
                institutional_edge=0.4,
                resolution_accuracy=0.95,
                dispute_frequency=0.05,
                structural_edge=0.15,
                arbitrage_opportunity=True,
                confidence_multiplier=1.4
            ),

            ContractStructure(
                contract_id='CORPORATE_EARNINGS',
                contract_title='Will [Company] beat EPS consensus by [Amount]?',
                contract_rules='Based on company\'s official earnings release',
                resolution_criteria=['Official press release', 'EPS exceeds consensus by specified amount', 'No restatements within 48 hours'],
                settlement_source='Company',
                settlement_lag_days=0,
                upside_scenarios=2,  # Beat by amount, or beat by more
                downside_scenarios=2,  # Miss, or restate down
                payoff_asymmetry=0.0,
                impossible_outcomes=['Company goes private before earnings'],
                unlikely_conditions=['Exact consensus hit'],
                public_attention_bias=0.85,
                institutional_edge=0.25,
                resolution_accuracy=0.92,
                dispute_frequency=0.08,
                structural_edge=0.06,
                arbitrage_opportunity=False,
                confidence_multiplier=1.15
            ),

            ContractStructure(
                contract_id='SPORTS_CHAMPIONSHIP',
                contract_title='Will [Team] win [Championship]?',
                contract_rules='Winner of final game as determined by league',
                resolution_criteria=['Official final score', 'No forfeited games', 'League approval of result'],
                settlement_source='Sports League',
                settlement_lag_days=0,
                upside_scenarios=1,
                downside_scenarios=15,  # 15 other teams in tournament
                payoff_asymmetry=0.88,  # Very unlikely for underdog
                impossible_outcomes=['Championship canceled'],
                unlikely_conditions=['All games decided by 1 point'],
                public_attention_bias=0.9,
                institutional_edge=0.15,
                resolution_accuracy=0.98,
                dispute_frequency=0.02,
                structural_edge=0.10,
                arbitrage_opportunity=False,
                confidence_multiplier=1.3
            )
        ]

        for structure in structures:
            self.contract_structures[structure.contract_id] = structure

    def _load_data(self):
        """Load existing contract structure data."""
        # Load structures
        if os.path.exists(self.structures_file):
            try:
                with open(self.structures_file, 'r') as f:
                    data = json.load(f)
                print(f"📜 Loaded contract structures: {len(data.get('structures', {}))} analyzed contracts")
            except Exception as e:
                print(f"⚠️ Error loading contract structures: {e}")

        # Load analyses
        if os.path.exists(self.analyses_file):
            try:
                with open(self.analyses_file, 'r') as f:
                    data = json.load(f)
                print(f"📜 Loaded structure analyses: {len(data.get('analyses', {}))} contract evaluations")
            except Exception as e:
                print(f"⚠️ Error loading structure analyses: {e}")

    def analyze_contract_structure(self, contract_data: Dict[str, Any]) -> Optional[EventStructureAnalysis]:
        """Analyze contract structure for trading opportunities."""

        contract_id = contract_data.get('contract_id', '')
        contract_title = contract_data.get('contract_title', '')
        current_market_data = contract_data.get('market_data', {})

        # Get contract structure
        structure = self.contract_structures.get(contract_id)
        if not structure:
            return None

        # Perform AI analysis
        payoff_asymmetry, resolution_lag, impossible_count, structural_edge, easy_trade_confidence, rationale, action = self._perform_structure_analysis(
            structure, current_market_data
        )

        analysis = EventStructureAnalysis(
            contract_id=contract_id,
            contract_title=contract_title,
            payoff_asymmetry=payoff_asymmetry,
            resolution_lag_opportunity=resolution_lag,
            impossible_outcomes_count=impossible_count,
            structural_edge=structural_edge,
            easy_trade_confidence=easy_trade_confidence,
            rationale=rationale,
            recommended_action=action
        )

        self.structure_analyses[contract_id] = analysis
        self._save_analysis(analysis)

        return analysis

    def _perform_structure_analysis(self, structure: ContractStructure, market_data: Dict[str, Any]) -> Tuple[float, bool, int, float, float, str, str]:
        """Perform detailed contract structure analysis."""

        # Get asymmetry analysis
        asymmetry, asymmetry_reason = structure.analyze_payoff_asymmetry()

        # Check resolution lag
        lag_opportunity, lag_reason = structure.check_resolution_lag_opportunity(market_data)

        # Count impossible outcomes priced in
        impossible_count = len(structure.impossible_outcomes)

        # Calculate overall structural edge
        structural_edge = asymmetry * 0.4 + (0.2 if lag_opportunity else 0) + (impossible_count * 0.05)

        # Get easy trade assessment
        easy_confidence, trade_rationale, action = structure.get_easy_structural_trade(market_data)

        # Generate comprehensive rationale
        rationale_parts = [
            f"Contract: {structure.contract_title}",
            f"Settlement: {structure.settlement_source} ({structure.settlement_lag_days} day lag)",
            f"Payoff Asymmetry: {asymmetry:.1%} - {asymmetry_reason}",
            f"Resolution Lag Opportunity: {'YES' if lag_opportunity else 'NO'} - {lag_reason}",
            f"Impossible Outcomes: {impossible_count} identified",
            f"Structural Edge: {structural_edge:.1%}",
            trade_rationale
        ]

        if structure.dispute_frequency > 0.05:
            rationale_parts.append(f"High dispute risk: {structure.dispute_frequency:.1%} of contracts disputed")

        if structure.public_attention_bias > 0.8:
            rationale_parts.append("High public attention may cause overreactions")

        rationale = " | ".join(rationale_parts)

        return asymmetry, lag_opportunity, impossible_count, structural_edge, easy_confidence, rationale, action

    def get_easy_structural_trades(self, min_confidence: float = 0.75) -> List[Dict[str, Any]]:
        """Find contracts with structural arbitrage opportunities."""

        easy_trades = []

        for contract_id, analysis in self.structure_analyses.items():
            if analysis.easy_trade_confidence >= min_confidence:
                trade_info = {
                    'contract_id': contract_id,
                    'contract_title': analysis.contract_title,
                    'payoff_asymmetry': analysis.payoff_asymmetry,
                    'resolution_lag_opportunity': analysis.resolution_lag_opportunity,
                    'impossible_outcomes': analysis.impossible_outcomes_count,
                    'structural_edge': analysis.structural_edge,
                    'confidence': analysis.easy_trade_confidence,
                    'rationale': analysis.rationale,
                    'recommended_action': analysis.recommended_action
                }
                easy_trades.append(trade_info)

        # Sort by confidence
        easy_trades.sort(key=lambda x: x['confidence'], reverse=True)
        return easy_trades[:10]  # Top 10 easy structural trades

    def _save_analysis(self, analysis: EventStructureAnalysis):
        """Save analysis to file."""
        analyses_data = {
            'analyses': {aid: a.to_dict() for aid, a in self.structure_analyses.items()},
            'last_updated': datetime.now().isoformat()
        }

        with open(self.analyses_file, 'w') as f:
            json.dump(analyses_data, f, indent=2)


# Test/demo functions
async def test_event_structure_engine():
    """Test the event structure analysis engine."""
    print("📜 TESTING EVENT STRUCTURE ENGINE")
    print("=" * 50)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)

    engine = EventStructureEngine(kalshi, scenario_graph)

    print(f"📜 Initialized with {len(engine.contract_structures)} contract structure analyses")

    # Test contract structures
    test_contracts = [
        {
            'contract_id': 'PRESIDENTIAL_ELECTION',
            'contract_title': 'Will Candidate A win 2024 Presidential Election?',
            'market_data': {'market_price': 0.4}
        },
        {
            'contract_id': 'FED_RATE_DECISION',
            'contract_title': 'Will Fed raise rates by 25bps in December?',
            'market_data': {'market_price': 0.6}
        },
        {
            'contract_id': 'CELEBRITY_EVENT',
            'contract_title': 'Will Actor X win Best Actor Oscar?',
            'market_data': {'market_price': 0.15}
        },
        {
            'contract_id': 'WEATHER_RECORD',
            'contract_title': 'Will Chicago set new heat record in July?',
            'market_data': {'market_price': 0.05, 'real_time_outcome': 'NO'}
        },
        {
            'contract_id': 'SPORTS_CHAMPIONSHIP',
            'contract_title': 'Will Underdog Team win NBA Championship?',
            'market_data': {'market_price': 0.12}
        }
    ]

    print("\n📜 ANALYZING CONTRACTS FOR STRUCTURAL EDGES:")
    for contract in test_contracts:
        print(f"\n📜 CONTRACT: {contract['contract_id']}")
        print(f"   Title: {contract['contract_title']}")

        # Analyze the contract structure
        analysis = engine.analyze_contract_structure(contract)

        if analysis:
            print("   ✅ CONTRACT STRUCTURE ANALYZED")
            print(f"   Payoff Asymmetry: {analysis.payoff_asymmetry:.1%}")
            print(f"   Resolution Lag Opportunity: {analysis.resolution_lag_opportunity}")
            print(f"   Impossible Outcomes: {analysis.impossible_outcomes_count}")
            print(f"   Structural Edge: {analysis.structural_edge:.1%}")
            print(f"   Easy Trade Confidence: {analysis.easy_trade_confidence:.1%}")

            if analysis.easy_trade_confidence > 0.75:
                print("   🎯 EASY STRUCTURAL TRADE OPPORTUNITY! 🎯")
                print(f"   Recommended: {analysis.recommended_action}")
            else:
                print("   ❓ Standard contract structure")

            print(f"   Rationale: {analysis.rationale}")
        else:
            print("   ❌ No structure analysis for this contract")

        print("-" * 75)

    # Show easy structural trades
    print("\n🎯 EASY STRUCTURAL TRADES (75%+ confidence):")
    easy_trades = engine.get_easy_structural_trades()

    if easy_trades:
        for i, trade in enumerate(easy_trades, 1):
            print(f"{i}. {trade['contract_id']}: {trade['confidence']:.1%} confidence")
            print(f"   Asymmetry: {trade['payoff_asymmetry']:.1%} | Edge: {trade['structural_edge']:.1%}")
            print(f"   {trade['recommended_action']}")
            print(f"   Rationale: {trade['rationale'][:100]}...")
            print()
    else:
        print("No easy structural trades found with current thresholds")

    print("\n✅ Event Structure Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_event_structure_engine())
