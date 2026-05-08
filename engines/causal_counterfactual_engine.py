"""
🔬 CAUSAL / COUNTERFACTUAL ENGINE

Advanced "What If" analysis system that models causal relationships between market events
and their downstream effects. Answers questions like:

- "If Fed cuts rates by 0.5% instead of 0.25%, what happens to SPY/BTC/NVDA?"
- "If Kalshi BTC 200K probability goes from 25% to 50%, how does that affect my portfolio?"
- "What would have happened if the election went the other way?"

Features:
- Causal Graph Modeling (Structural Causal Model)
- Counterfactual Simulation Engine
- Impact Propagation Analysis
- Scenario Stress Testing
- Portfolio Counterfactual Analysis
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
import math
import copy
from collections import defaultdict

try:
    from engines.scenario_graph_engine import ScenarioGraphEngine, GraphNode, GraphEdge
    from engines.kalshi_engine import KalshiPredictionEngine
except ImportError:
    # Mocks for testing
    class ScenarioGraphEngine:
        def __init__(self, *args, **kwargs):
            self.nodes = {}
            self.edges = []
    class GraphNode:
        pass
    class GraphEdge:
        pass
    class KalshiPredictionEngine:
        pass


@dataclass
class CausalRelationship:
    """Represents a causal relationship between variables."""
    cause_variable: str
    effect_variable: str
    relationship_type: str  # 'direct', 'indirect', 'moderated', 'mediated'
    strength: float  # Effect size (-1.0 to 1.0)
    confidence: float = 0.5
    time_lag: int = 0  # Days between cause and effect
    conditions: Dict[str, Any] = field(default_factory=dict)  # Moderating conditions
    evidence: List[str] = field(default_factory=list)  # Supporting data/observations

    def to_dict(self) -> Dict[str, Any]:
        return {
            'cause': self.cause_variable,
            'effect': self.effect_variable,
            'type': self.relationship_type,
            'strength': self.strength,
            'confidence': self.confidence,
            'time_lag': self.time_lag,
            'conditions': self.conditions,
            'evidence': self.evidence
        }


@dataclass
class CounterfactualScenario:
    """A counterfactual "what if" scenario."""
    id: str
    description: str
    intervention: Dict[str, Any]  # What we change (variable -> new_value)
    baseline_state: Dict[str, Any]  # Original state before intervention
    counterfactual_state: Dict[str, Any]  # State after intervention
    affected_variables: Set[str] = field(default_factory=set)
    expected_impact: float = 0.0
    confidence: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'description': self.description,
            'intervention': self.intervention,
            'baseline_state': self.baseline_state,
            'counterfactual_state': self.counterfactual_state,
            'affected_variables': list(self.affected_variables),
            'expected_impact': self.expected_impact,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ImpactPropagation:
    """Tracks how an intervention propagates through the causal graph."""
    intervention_variable: str
    intervention_value: Any
    propagation_path: List[Dict[str, Any]]  # Chain of causal effects
    final_impacts: Dict[str, Any] = field(default_factory=dict)
    confidence_chain: List[float] = field(default_factory=list)
    total_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'intervention_variable': self.intervention_variable,
            'intervention_value': self.intervention_value,
            'propagation_path': self.propagation_path,
            'final_impacts': self.final_impacts,
            'confidence_chain': self.confidence_chain,
            'total_confidence': self.total_confidence
        }


class CausalCounterfactualEngine:
    """
    🔬 Causal/Counterfactual Engine

    Models the causal structure of financial markets and simulates "what if" scenarios.
    Moves beyond correlation to understand WHY events cause other events.
    """

    def __init__(self, scenario_graph: ScenarioGraphEngine):
        self.scenario_graph = scenario_graph
        self.causal_relationships: Dict[Tuple[str, str], CausalRelationship] = {}
        self.counterfactual_scenarios: Dict[str, CounterfactualScenario] = {}
        self.baseline_states: Dict[str, Any] = {}  # Current market state

        self.causal_graph_file = "causal_graph.json"
        self.counterfactuals_file = "counterfactual_scenarios.json"

        # Initialize with base causal relationships
        self._initialize_base_causal_relationships()
        self._load_data()

    def _initialize_base_causal_relationships(self):
        """Initialize fundamental causal relationships in financial markets."""
        relationships = [
            # Fed rate decisions
            CausalRelationship(
                cause_variable="FED_RATE_DECISION",
                effect_variable="SPY",
                relationship_type="direct",
                strength=-0.6,  # Rate cuts boost stocks
                confidence=0.8,
                time_lag=1,
                conditions={"rate_direction": "cut"},
                evidence=["Historical Fed cut impacts", "Market reaction data"]
            ),
            CausalRelationship(
                cause_variable="FED_RATE_DECISION",
                effect_variable="QQQ",
                relationship_type="direct",
                strength=-0.7,  # Tech more sensitive to rates
                confidence=0.8,
                time_lag=1,
                conditions={"rate_direction": "cut"},
                evidence=["Tech sector rate sensitivity studies"]
            ),
            CausalRelationship(
                cause_variable="FED_RATE_DECISION",
                effect_variable="BTC-USD",
                relationship_type="direct",
                strength=-0.5,  # Crypto as risk asset
                confidence=0.6,
                time_lag=1,
                conditions={"rate_direction": "cut"},
                evidence=["Crypto rate correlation analysis"]
            ),

            # Inflation impacts
            CausalRelationship(
                cause_variable="CPI_INFLATION",
                effect_variable="FED_RATE_DECISION",
                relationship_type="direct",
                strength=0.8,  # High inflation -> higher rates
                confidence=0.9,
                time_lag=30,  # Fed reacts to inflation data
                evidence=["Fed reaction function studies"]
            ),
            CausalRelationship(
                cause_variable="CPI_INFLATION",
                effect_variable="SPY",
                relationship_type="mediated",
                strength=-0.4,  # Inflation -> Fed -> stocks
                confidence=0.7,
                time_lag=45,
                evidence=["Inflation-stock correlation data"]
            ),

            # Election outcomes
            CausalRelationship(
                cause_variable="ELECTION_OUTCOME",
                effect_variable="NVDA",
                relationship_type="direct",
                strength=0.5,  # Tech benefits from certain policies
                confidence=0.6,
                time_lag=30,
                conditions={"outcome": "democrat"},
                evidence=["Sector rotation by administration"]
            ),
            CausalRelationship(
                cause_variable="ELECTION_OUTCOME",
                effect_variable="XOM",
                relationship_type="direct",
                strength=-0.3,  # Energy policies vary by party
                confidence=0.5,
                time_lag=30,
                conditions={"outcome": "democrat"},
                evidence=["Energy policy historical data"]
            ),

            # AI breakthroughs
            CausalRelationship(
                cause_variable="AI_BREAKTHROUGH",
                effect_variable="NVDA",
                relationship_type="direct",
                strength=0.8,  # Direct AI hardware beneficiary
                confidence=0.8,
                time_lag=7,
                evidence=["AI hype cycles", "Chip demand data"]
            ),
            CausalRelationship(
                cause_variable="AI_BREAKTHROUGH",
                effect_variable="MSFT",
                relationship_type="direct",
                strength=0.7,  # Cloud/AI software leader
                confidence=0.8,
                time_lag=7,
                evidence=["AI adoption metrics"]
            ),

            # Oil price impacts
            CausalRelationship(
                cause_variable="OIL_PRICE_SHOCK",
                effect_variable="XOM",
                relationship_type="direct",
                strength=0.7,  # Oil companies benefit
                confidence=0.8,
                time_lag=1,
                evidence=["Oil company earnings sensitivity"]
            ),
            CausalRelationship(
                cause_variable="OIL_PRICE_SHOCK",
                effect_variable="BTC-USD",
                relationship_type="direct",
                strength=-0.4,  # Risk-off reduces crypto demand
                confidence=0.6,
                time_lag=1,
                evidence=["Crypto-oil correlation studies"]
            ),

            # BTC price targets
            CausalRelationship(
                cause_variable="BTC_PRICE_TARGET",
                effect_variable="BTC-USD",
                relationship_type="direct",
                strength=0.9,  # Direct price prediction
                confidence=0.9,
                time_lag=0,
                evidence=["Self-evident - direct price target"]
            ),
            CausalRelationship(
                cause_variable="BTC_PRICE_TARGET",
                effect_variable="SPY",
                relationship_type="correlation",
                strength=0.3,  # BTC as risk asset proxy
                confidence=0.4,
                time_lag=30,
                evidence=["Risk asset correlation data"]
            ),

            # FDA approvals
            CausalRelationship(
                cause_variable="FDA_AI_DRUG_APPROVAL",
                effect_variable="NVDA",
                relationship_type="direct",
                strength=0.6,  # AI drug approval boosts AI sector
                confidence=0.7,
                time_lag=30,
                evidence=["Sector spillover effects"]
            ),
        ]

        for rel in relationships:
            key = (rel.cause_variable, rel.effect_variable)
            self.causal_relationships[key] = rel

    def _load_data(self):
        """Load existing causal graph and counterfactuals."""
        # Load causal relationships
        if os.path.exists(self.causal_graph_file):
            try:
                with open(self.causal_graph_file, 'r') as f:
                    data = json.load(f)
                print(f"📊 Loaded causal graph: {len(data.get('relationships', {}))} relationships")
            except Exception as e:
                print(f"⚠️ Error loading causal graph: {e}")

        # Load counterfactual scenarios
        if os.path.exists(self.counterfactuals_file):
            try:
                with open(self.counterfactuals_file, 'r') as f:
                    data = json.load(f)
                print(f"🔬 Loaded counterfactual scenarios: {len(data.get('scenarios', {}))}")
            except Exception as e:
                print(f"⚠️ Error loading counterfactuals: {e}")

    def _save_data(self):
        """Save causal graph and counterfactuals."""
        # Save causal relationships
        causal_data = {
            'relationships': {
                f"{cause}_{effect}": rel.to_dict()
                for (cause, effect), rel in self.causal_relationships.items()
            },
            'last_updated': datetime.now().isoformat()
        }

        with open(self.causal_graph_file, 'w') as f:
            json.dump(causal_data, f, indent=2)

        # Save counterfactual scenarios
        counterfactual_data = {
            'scenarios': {
                scenario_id: scenario.to_dict()
                for scenario_id, scenario in self.counterfactual_scenarios.items()
            },
            'last_updated': datetime.now().isoformat()
        }

        with open(self.counterfactuals_file, 'w') as f:
            json.dump(counterfactual_data, f, indent=2)

    def set_baseline_state(self, state: Dict[str, Any]):
        """Set the current baseline market state."""
        self.baseline_states.update(state)
        print(f"📊 Updated baseline state with {len(state)} variables")

    def simulate_counterfactual(self, intervention: Dict[str, Any],
                              description: str = "") -> CounterfactualScenario:
        """Simulate a counterfactual scenario with the given intervention."""

        scenario_id = f"counterfactual_{int(datetime.now().timestamp())}"

        # Create baseline state (copy current known state)
        baseline_state = copy.deepcopy(self.baseline_states)

        # Apply intervention
        counterfactual_state = copy.deepcopy(baseline_state)
        counterfactual_state.update(intervention)

        # Propagate effects through causal graph
        propagation = self._propagate_intervention(intervention)

        # Update counterfactual state with propagated effects
        counterfactual_state.update(propagation.final_impacts)

        # Identify affected variables
        affected_variables = set()
        for var in intervention.keys():
            affected_variables.add(var)
        affected_variables.update(propagation.final_impacts.keys())

        # Calculate expected impact (simplified)
        expected_impact = sum(abs(change) for change in propagation.final_impacts.values() if isinstance(change, (int, float)))

        scenario = CounterfactualScenario(
            id=scenario_id,
            description=description or f"What if {list(intervention.keys())[0]} changes?",
            intervention=intervention,
            baseline_state=baseline_state,
            counterfactual_state=counterfactual_state,
            affected_variables=affected_variables,
            expected_impact=expected_impact,
            confidence=propagation.total_confidence
        )

        self.counterfactual_scenarios[scenario_id] = scenario
        self._save_data()

        return scenario

    def _propagate_intervention(self, intervention: Dict[str, Any]) -> ImpactPropagation:
        """Propagate an intervention through the causal graph."""

        propagation = ImpactPropagation(
            intervention_variable=list(intervention.keys())[0],
            intervention_value=list(intervention.values())[0],
            propagation_path=[],
            confidence_chain=[]
        )

        visited = set()
        to_visit = list(intervention.keys())

        while to_visit and len(propagation.propagation_path) < 10:  # Prevent infinite loops
            current_var = to_visit.pop(0)
            if current_var in visited:
                continue
            visited.add(current_var)

            # Find all effects of this variable
            effects = []
            for (cause, effect), rel in self.causal_relationships.items():
                if cause == current_var:
                    effects.append((effect, rel))

            for effect_var, relationship in effects:
                if effect_var in visited:
                    continue

                # Check if conditions are met
                if not self._check_relationship_conditions(relationship):
                    continue

                # Calculate effect
                if current_var in intervention:
                    cause_change = intervention[current_var]
                else:
                    cause_change = propagation.final_impacts.get(current_var, 0)

                if isinstance(cause_change, (int, float)):
                    effect_change = cause_change * relationship.strength

                    # Apply time lag (simplified - just store the effect)
                    propagation.final_impacts[effect_var] = effect_change
                    propagation.confidence_chain.append(relationship.confidence)

                    # Add to propagation path
                    propagation.propagation_path.append({
                        'from': current_var,
                        'to': effect_var,
                        'relationship': relationship.relationship_type,
                        'strength': relationship.strength,
                        'effect_change': effect_change,
                        'time_lag': relationship.time_lag
                    })

                    # Continue propagation
                    if effect_var not in to_visit:
                        to_visit.append(effect_var)

        # Calculate total confidence
        if propagation.confidence_chain:
            propagation.total_confidence = math.prod(propagation.confidence_chain) ** (1.0 / len(propagation.confidence_chain))
        else:
            propagation.total_confidence = 0.5

        return propagation

    def _check_relationship_conditions(self, relationship: CausalRelationship) -> bool:
        """Check if the conditions for a causal relationship are met."""
        # Simplified - in production would check baseline state against conditions
        return True

    def analyze_portfolio_counterfactual(self, portfolio: Dict[str, Any],
                                       intervention: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how a counterfactual scenario would affect a portfolio."""

        # Simulate the counterfactual
        scenario = self.simulate_counterfactual(intervention)

        # Calculate portfolio impact
        baseline_value = self._calculate_portfolio_value(portfolio, scenario.baseline_state)
        counterfactual_value = self._calculate_portfolio_value(portfolio, scenario.counterfactual_state)

        impact = counterfactual_value - baseline_value
        impact_percentage = (impact / baseline_value) * 100 if baseline_value != 0 else 0

        return {
            'scenario': scenario.to_dict(),
            'portfolio_impact': {
                'baseline_value': baseline_value,
                'counterfactual_value': counterfactual_value,
                'absolute_impact': impact,
                'percentage_impact': impact_percentage
            },
            'position_impacts': self._calculate_position_impacts(portfolio, scenario)
        }

    def _calculate_portfolio_value(self, portfolio: Dict[str, Any], state: Dict[str, Any]) -> float:
        """Calculate portfolio value given a market state."""
        # Simplified calculation - in production would use actual pricing
        total_value = 0.0

        for position in portfolio.get('positions', []):
            asset = position.get('asset', '')
            quantity = position.get('quantity', 0)

            # Get price from state (simplified)
            price = state.get(f"{asset}_price", state.get(asset, 100))
            total_value += price * quantity

        return total_value

    def _calculate_position_impacts(self, portfolio: Dict[str, Any],
                                  scenario: CounterfactualScenario) -> List[Dict[str, Any]]:
        """Calculate impact on individual positions."""
        impacts = []

        for position in portfolio.get('positions', []):
            asset = position.get('asset', '')
            baseline_price = scenario.baseline_state.get(f"{asset}_price",
                                                       scenario.baseline_state.get(asset, 100))
            counterfactual_price = scenario.counterfactual_state.get(f"{asset}_price",
                                                                   scenario.counterfactual_state.get(asset, 100))

            price_impact = counterfactual_price - baseline_price
            price_impact_pct = (price_impact / baseline_price) * 100 if baseline_price != 0 else 0

            quantity = position.get('quantity', 0)
            position_impact = price_impact * quantity

            impacts.append({
                'asset': asset,
                'baseline_price': baseline_price,
                'counterfactual_price': counterfactual_price,
                'price_impact': price_impact,
                'price_impact_pct': price_impact_pct,
                'quantity': quantity,
                'position_impact': position_impact
            })

        return impacts

    def find_key_lever_variables(self, target_variable: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """Find variables that have strong causal influence on a target variable."""
        levers = []

        # Find direct causes
        for (cause, effect), rel in self.causal_relationships.items():
            if effect == target_variable and abs(rel.strength) > 0.5:
                levers.append({
                    'variable': cause,
                    'relationship': rel.relationship_type,
                    'strength': rel.strength,
                    'confidence': rel.confidence,
                    'depth': 1
                })

        # Could extend to indirect causes with graph traversal
        # For now, keep it to direct relationships

        # Sort by absolute strength
        levers.sort(key=lambda x: abs(x['strength']), reverse=True)
        return levers[:10]  # Top 10 levers

    def generate_scenario_comparison_report(self, scenarios: List[CounterfactualScenario]) -> str:
        """Generate a human-readable comparison report of multiple scenarios."""

        report_parts = []

        report_parts.append("🔬 COUNTERFACTUAL SCENARIO COMPARISON REPORT")
        report_parts.append("=" * 60)
        report_parts.append("")

        for i, scenario in enumerate(scenarios, 1):
            report_parts.append(f"SCENARIO {i}: {scenario.description}")
            report_parts.append("-" * 40)

            # Intervention
            intervention = list(scenario.intervention.items())[0]
            report_parts.append(f"Intervention: {intervention[0]} → {intervention[1]}")
            report_parts.append("")

            # Key impacts
            impacts = []
            for var, new_value in scenario.counterfactual_state.items():
                old_value = scenario.baseline_state.get(var)
                if old_value is not None and old_value != new_value:
                    if isinstance(new_value, (int, float)) and isinstance(old_value, (int, float)):
                        change = new_value - old_value
                        impacts.append((var, change))

            if impacts:
                report_parts.append("Key Impacts:")
                for var, change in sorted(impacts, key=lambda x: abs(x[1]), reverse=True)[:5]:
                    report_parts.append(f"  • {var}: {change:+.2f}")
                report_parts.append("")

            report_parts.append(f"Confidence: {scenario.confidence:.1%}")
            report_parts.append(f"Expected Impact: {scenario.expected_impact:.2f}")
            report_parts.append("")

        return "\n".join(report_parts)


# Test/demo functions
async def test_causal_counterfactual_engine():
    """Test the causal counterfactual engine."""
    print("🔬 TESTING CAUSAL COUNTERFACTUAL ENGINE")
    print("=" * 50)

    # Mock scenario graph
    scenario_graph = ScenarioGraphEngine(None)
    engine = CausalCounterfactualEngine(scenario_graph)

    # Set baseline market state
    baseline_state = {
        'FED_RATE_DECISION': 0.25,
        'CPI_INFLATION': 3.2,
        'SPY': 450.0,
        'QQQ': 380.0,
        'BTC-USD': 95000.0,
        'NVDA': 850.0,
        'FED_RATE_DECISION_price': 0.25,
        'CPI_INFLATION_price': 3.2,
        'SPY_price': 450.0,
        'QQQ_price': 380.0,
        'BTC-USD_price': 95000.0,
        'NVDA_price': 850.0
    }
    engine.set_baseline_state(baseline_state)

    print(f"📊 Initialized with {len(engine.causal_relationships)} causal relationships")

    # Test counterfactual: What if Fed cuts rates by 0.5% instead of 0.25%?
    print("\n🎭 SIMULATING COUNTERFACTUAL SCENARIO:")
    print("What if Fed cuts rates by 0.5% instead of 0.25%?")

    intervention = {'FED_RATE_DECISION': 0.5}
    scenario = engine.simulate_counterfactual(
        intervention,
        "Fed cuts rates by 0.5% instead of 0.25%"
    )

    print(f"✅ Generated scenario: {scenario.id}")
    print(f"🎯 Intervention: {scenario.intervention}")
    print(f"📈 Expected impact: {scenario.expected_impact:.2f}")
    print(f"🎪 Confidence: {scenario.confidence:.1%}")
    print(f"🔗 Affected variables: {len(scenario.affected_variables)}")

    # Show key impacts
    print("\n💰 KEY IMPACTS:")
    impacts = []
    for var in scenario.affected_variables:
        old_val = scenario.baseline_state.get(var)
        new_val = scenario.counterfactual_state.get(var)
        if isinstance(new_val, (int, float)) and isinstance(old_val, (int, float)) and old_val != new_val:
            impacts.append((var, new_val - old_val))

    for var, change in sorted(impacts, key=lambda x: abs(x[1]), reverse=True)[:5]:
        print(f"   • {var}: {change:+.2f}")

    # Test portfolio counterfactual
    print("\n📊 PORTFOLIO COUNTERFACTUAL ANALYSIS:")
    sample_portfolio = {
        'positions': [
            {'asset': 'SPY', 'quantity': 100},
            {'asset': 'QQQ', 'quantity': 50},
            {'asset': 'BTC-USD', 'quantity': 0.5},
            {'asset': 'NVDA', 'quantity': 20}
        ]
    }

    portfolio_analysis = engine.analyze_portfolio_counterfactual(sample_portfolio, intervention)

    impact = portfolio_analysis['portfolio_impact']
    print(f"Portfolio baseline value: ${impact['baseline_value']:.2f}")
    print(f"Portfolio counterfactual value: ${impact['counterfactual_value']:.2f}")
    print(f"Absolute impact: ${impact['absolute_impact']:+.2f}")
    print(f"Percentage impact: {impact['percentage_impact']:+.1f}%")

    # Test key levers
    print("\n🔑 KEY LEVERS FOR SPY:")
    levers = engine.find_key_lever_variables('SPY')
    for lever in levers[:3]:
        print(f"   • {lever['variable']}: strength {lever['strength']:+.2f} (confidence: {lever['confidence']:.1%})")

    print("\n✅ Causal Counterfactual Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_causal_counterfactual_engine())
