"""
🌍 WORLD-STATE / SCENARIO GRAPH ENGINE

Advanced multi-market scenario modeling system that treats Kalshi events as interconnected
nodes in a global market graph. Creates scenario trees, probability-weighted outcomes,
and cross-market arbitrage opportunities.

Features:
- Event/Asset Graph Modeling
- Scenario Tree Generation
- Probability-Weighted Outcomes
- Cross-Market Impact Analysis
- Scenario Ranking & Optimization
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict

try:
    from engines.kalshi_engine import KalshiPredictionEngine
except ImportError:
    # Mock for testing
    class KalshiPredictionEngine:
        pass


@dataclass
class GraphNode:
    """Represents a node in the world-state graph (event or asset)."""
    id: str
    node_type: str  # 'event' or 'asset'
    name: str
    description: str
    probability: float = 0.5
    impact_strength: float = 0.0
    connected_nodes: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.node_type,
            'name': self.name,
            'description': self.description,
            'probability': self.probability,
            'impact_strength': self.impact_strength,
            'connected_nodes': list(self.connected_nodes),
            'metadata': self.metadata
        }


@dataclass
class GraphEdge:
    """Represents a relationship between two nodes."""
    from_node: str
    to_node: str
    edge_type: str  # 'causes', 'correlates_with', 'hedges', 'amplifies'
    strength: float  # -1.0 to 1.0 (negative = inverse relationship)
    confidence: float = 0.5
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'from': self.from_node,
            'to': self.to_node,
            'type': self.edge_type,
            'strength': self.strength,
            'confidence': self.confidence,
            'description': self.description
        }


@dataclass
class ScenarioBranch:
    """Represents a branch in a scenario tree."""
    node_id: str
    outcome: str  # 'yes', 'no', or 'asset_up', 'asset_down', etc.
    probability: float
    impact_multiplier: float = 1.0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'outcome': self.outcome,
            'probability': self.probability,
            'impact_multiplier': self.impact_multiplier,
            'description': self.description
        }


@dataclass
class ScenarioTree:
    """A complete scenario tree with probability-weighted outcomes."""
    id: str
    name: str
    root_event: str
    branches: List[ScenarioBranch]
    total_probability: float = 0.0
    expected_pl: float = 0.0
    risk_adjusted_score: float = 0.0
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'root_event': self.root_event,
            'branches': [b.to_dict() for b in self.branches],
            'total_probability': self.total_probability,
            'expected_pl': self.expected_pl,
            'risk_adjusted_score': self.risk_adjusted_score,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }


class ScenarioGraphEngine:
    """
    🌍 World-State Scenario Graph Engine

    Models the entire market universe as an interconnected graph where:
    - Nodes = Kalshi events + traditional assets
    - Edges = causal/correlation relationships
    - Scenarios = probability-weighted outcome trees
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine):
        self.kalshi = kalshi_engine
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.scenarios: Dict[str, ScenarioTree] = {}
        from core.runtime_paths import runtime_path
        self.graph_file = runtime_path("scenario_graph.json")
        self._load_graph()

    def _load_graph(self):
        """Load existing graph from disk."""
        if os.path.exists(self.graph_file):
            try:
                with open(self.graph_file, 'r') as f:
                    data = json.load(f)

                # Load nodes
                for node_data in data.get('nodes', []):
                    node = GraphNode(
                        id=node_data['id'],
                        node_type=node_data['type'],
                        name=node_data['name'],
                        description=node_data['description'],
                        probability=node_data.get('probability', 0.5),
                        impact_strength=node_data.get('impact_strength', 0.0),
                        connected_nodes=set(node_data.get('connected_nodes', [])),
                        metadata=node_data.get('metadata', {})
                    )
                    self.nodes[node.id] = node

                # Load edges
                for edge_data in data.get('edges', []):
                    edge = GraphEdge(
                        from_node=edge_data['from'],
                        to_node=edge_data['to'],
                        edge_type=edge_data['type'],
                        strength=edge_data['strength'],
                        confidence=edge_data.get('confidence', 0.5),
                        description=edge_data.get('description', '')
                    )
                    self.edges.append(edge)

                print(f"📊 Loaded scenario graph: {len(self.nodes)} nodes, {len(self.edges)} edges")

            except Exception as e:
                print(f"⚠️ Error loading scenario graph: {e}")
                self._initialize_base_graph()

        else:
            self._initialize_base_graph()

    def _initialize_base_graph(self):
        """Create initial graph structure with major market relationships."""
        print("🌍 Initializing base scenario graph...")

        # Major Kalshi event categories
        kalshi_events = [
            ("FED_RATE_CUT", "Federal Reserve cuts interest rates by 0.25%", "macro"),
            ("CPI_HIGH", "CPI inflation exceeds 3%", "macro"),
            ("SPX_CRASH", "S&P 500 drops 10%+ in Q1 2025", "equity"),
            ("BTC_200K", "Bitcoin reaches $200K by end of 2025", "crypto"),
            ("OIL_150", "Oil exceeds $150/barrel in 2025", "commodity"),
            ("AI_BREAKTHROUGH", "Major AI breakthrough announced in 2025", "tech"),
            ("ELECTION_DEM", "Democrat wins 2024 US election", "political"),
            ("FDA_AI_DRUG", "FDA approves AI-assisted drug", "healthcare"),
        ]

        # Major assets
        assets = [
            ("SPY", "SPDR S&P 500 ETF Trust"),
            ("QQQ", "Invesco QQQ Trust"),
            ("BTC-USD", "Bitcoin"),
            ("NVDA", "NVIDIA Corporation"),
            ("XOM", "Exxon Mobil Corporation"),
            ("MSFT", "Microsoft Corporation"),
            ("TSLA", "Tesla, Inc."),
            ("META", "Meta Platforms, Inc."),
        ]

        # Create nodes
        for event_id, description, category in kalshi_events:
            self.nodes[event_id] = GraphNode(
                id=event_id,
                node_type='event',
                name=event_id.replace('_', ' ').title(),
                description=description,
                metadata={'category': category, 'source': 'kalshi'}
            )

        for asset_id, description in assets:
            self.nodes[asset_id] = GraphNode(
                id=asset_id,
                node_type='asset',
                name=asset_id,
                description=description,
                metadata={'asset_type': 'equity' if asset_id != 'BTC-USD' else 'crypto'}
            )

        # Create base relationships
        self._create_base_relationships()
        self._save_graph()

    def _create_base_relationships(self):
        """Create fundamental market relationships."""
        relationships = [
            # Fed rate cuts -> broad market positive
            ("FED_RATE_CUT", "SPY", "causes", 0.8, "Rate cuts typically boost equities"),
            ("FED_RATE_CUT", "QQQ", "causes", 0.8, "Tech benefits from lower rates"),
            ("FED_RATE_CUT", "BTC-USD", "causes", 0.6, "Crypto often rallies on rate cuts"),

            # High inflation -> negative for stocks
            ("CPI_HIGH", "SPY", "causes", -0.7, "High inflation pressures stocks"),
            ("CPI_HIGH", "QQQ", "causes", -0.6, "Tech sensitive to inflation"),
            ("CPI_HIGH", "BTC-USD", "causes", -0.5, "BTC can be inflation hedge but volatile"),

            # Market crash -> correlated assets
            ("SPX_CRASH", "QQQ", "correlates_with", 0.9, "Tech follows broad market"),
            ("SPX_CRASH", "BTC-USD", "correlates_with", -0.3, "BTC can decouple in crashes"),

            # BTC price target -> BTC asset
            ("BTC_200K", "BTC-USD", "predicts", 0.9, "Direct price target prediction"),

            # Oil crisis -> energy stocks up, BTC risk-off
            ("OIL_150", "XOM", "causes", 0.8, "Oil companies benefit from high prices"),
            ("OIL_150", "BTC-USD", "causes", -0.5, "Risk-off reduces crypto demand"),

            # AI breakthrough -> tech stocks
            ("AI_BREAKTHROUGH", "NVDA", "causes", 0.9, "NVIDIA leads AI hardware"),
            ("AI_BREAKTHROUGH", "MSFT", "causes", 0.8, "Microsoft major AI player"),
            ("AI_BREAKTHROUGH", "META", "causes", 0.7, "Meta invested heavily in AI"),

            # Election outcomes -> market reactions
            ("ELECTION_DEM", "SPY", "causes", 0.4, "Democratic policies can favor certain sectors"),
            ("ELECTION_DEM", "NVDA", "causes", 0.5, "Dem focus on tech/AI"),
            ("ELECTION_DEM", "XOM", "causes", -0.3, "Dem energy policies less favorable"),

            # FDA AI drug -> healthcare/tech crossover
            ("FDA_AI_DRUG", "NVDA", "causes", 0.7, "AI drug approval boosts AI sector"),
            ("FDA_AI_DRUG", "MSFT", "causes", 0.6, "Healthcare AI applications"),
        ]

        for from_id, to_id, edge_type, strength, description in relationships:
            if from_id in self.nodes and to_id in self.nodes:
                edge = GraphEdge(
                    from_node=from_id,
                    to_node=to_id,
                    edge_type=edge_type,
                    strength=strength,
                    confidence=0.7,
                    description=description
                )
                self.edges.append(edge)

                # Update node connections
                self.nodes[from_id].connected_nodes.add(to_id)
                self.nodes[to_id].connected_nodes.add(from_id)

    def _save_graph(self):
        """Save current graph to disk."""
        data = {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges],
            'scenarios': [scenario.to_dict() for scenario in self.scenarios.values()],
            'last_updated': datetime.now().isoformat()
        }

        with open(self.graph_file, 'w') as f:
            json.dump(data, f, indent=2)

    def update_from_kalshi_markets(self, market_data: List[Dict[str, Any]]):
        """Update graph with real Kalshi market data."""
        for market in market_data:
            market_id = market.get('ticker', '').replace('-', '_').upper()

            if market_id not in self.nodes:
                # Create new event node
                self.nodes[market_id] = GraphNode(
                    id=market_id,
                    node_type='event',
                    name=market.get('title', market_id),
                    description=market.get('title', ''),
                    probability=market.get('implied_probability', 0.5),
                    metadata={
                        'source': 'kalshi',
                        'ticker': market.get('ticker'),
                        'volume': market.get('volume', 0),
                        'open_interest': market.get('open_interest', 0)
                    }
                )

            # Update existing node with current data
            else:
                node = self.nodes[market_id]
                node.probability = market.get('implied_probability', node.probability)
                node.metadata.update({
                    'last_updated': datetime.now().isoformat(),
                    'volume': market.get('volume', 0),
                    'open_interest': market.get('open_interest', 0)
                })

        self._save_graph()

    def find_connected_assets(self, event_id: str) -> List[Tuple[str, float]]:
        """Find all assets connected to an event with their impact strengths."""
        if event_id not in self.nodes:
            return []

        connected_assets = []
        for edge in self.edges:
            if edge.from_node == event_id and self.nodes[edge.to_node].node_type == 'asset':
                connected_assets.append((edge.to_node, edge.strength))

        return connected_assets

    def generate_scenario_tree(self, root_event: str, max_depth: int = 3) -> Optional[ScenarioTree]:
        """Generate a scenario tree starting from a root event."""
        if root_event not in self.nodes:
            return None

        scenario_id = f"scenario_{root_event}_{int(datetime.now().timestamp())}"
        branches = []

        # Root event branch
        root_node = self.nodes[root_event]
        branches.append(ScenarioBranch(
            node_id=root_event,
            outcome='yes',
            probability=root_node.probability,
            description=f"{root_node.name} occurs"
        ))

        branches.append(ScenarioBranch(
            node_id=root_event,
            outcome='no',
            probability=1 - root_node.probability,
            description=f"{root_node.name} does not occur"
        ))

        # For now, keep it simple - just the root event
        # In full implementation, we'd recursively build deeper trees

        scenario = ScenarioTree(
            id=scenario_id,
            name=f"Scenario Tree: {root_node.name}",
            root_event=root_event,
            branches=branches,
            total_probability=1.0,  # Always sums to 1 for root
            description=f"Probability tree for {root_node.description}"
        )

        self.scenarios[scenario_id] = scenario
        return scenario

    def rank_scenarios_by_profit_potential(self, limit: int = 5) -> List[ScenarioTree]:
        """Rank all scenarios by profit potential."""
        # For now, rank by root event probability and impact strength
        # In full implementation, this would calculate expected P/L

        scored_scenarios = []
        for scenario in self.scenarios.values():
            root_node = self.nodes.get(scenario.root_event)
            if root_node:
                score = root_node.probability * root_node.impact_strength
                scenario.risk_adjusted_score = score
                scored_scenarios.append(scenario)

        # Sort by score descending
        scored_scenarios.sort(key=lambda s: s.risk_adjusted_score, reverse=True)
        return scored_scenarios[:limit]

    def get_top_scenarios_dashboard(self, limit: int = 10) -> Dict[str, Any]:
        """Generate top scenarios dashboard."""
        top_scenarios = self.rank_scenarios_by_profit_potential(limit)

        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'total_scenarios': len(self.scenarios),
            'top_scenarios': []
        }

        for i, scenario in enumerate(top_scenarios, 1):
            root_node = self.nodes.get(scenario.root_event)
            if root_node:
                scenario_data = {
                    'rank': i,
                    'id': scenario.id,
                    'name': scenario.name,
                    'root_event': scenario.root_event,
                    'probability': root_node.probability,
                    'impact_strength': root_node.impact_strength,
                    'score': scenario.risk_adjusted_score,
                    'description': scenario.description
                }
                dashboard['top_scenarios'].append(scenario_data)

        return dashboard

    def analyze_cross_market_arbitrage(self, event_id: str) -> Dict[str, Any]:
        """Analyze potential arbitrage between event and connected assets."""
        if event_id not in self.nodes:
            return {'error': 'Event not found'}

        event_node = self.nodes[event_id]
        connected_assets = self.find_connected_assets(event_id)

        arbitrage_opportunities = []

        for asset_id, impact_strength in connected_assets:
            asset_node = self.nodes[asset_id]

            # Simple arbitrage check: if impact is strong enough
            if abs(impact_strength) > 0.6:
                opportunity = {
                    'asset': asset_id,
                    'impact_strength': impact_strength,
                    'direction': 'bullish' if impact_strength > 0 else 'bearish',
                    'confidence': min(abs(impact_strength), 0.9),
                    'description': f"{'Bullish' if impact_strength > 0 else 'Bearish'} arbitrage opportunity in {asset_node.name}"
                }
                arbitrage_opportunities.append(opportunity)

        return {
            'event': event_id,
            'event_probability': event_node.probability,
            'arbitrage_opportunities': arbitrage_opportunities,
            'total_opportunities': len(arbitrage_opportunities)
        }


# Test/demo functions
async def test_scenario_graph_engine():
    """Test the scenario graph engine."""
    print("🌍 TESTING SCENARIO GRAPH ENGINE")
    print("=" * 50)

    # Mock kalshi engine for testing
    class MockKalshiEngine:
        pass

    kalshi = MockKalshiEngine()
    graph_engine = ScenarioGraphEngine(kalshi)

    print(f"📊 Graph initialized with {len(graph_engine.nodes)} nodes and {len(graph_engine.edges)} edges")

    # Test scenario generation
    print("\n🎯 GENERATING SCENARIOS:")
    for event_id in ['FED_RATE_CUT', 'BTC_200K', 'AI_BREAKTHROUGH']:
        if event_id in graph_engine.nodes:
            scenario = graph_engine.generate_scenario_tree(event_id)
            if scenario:
                print(f"✅ Generated scenario for {event_id}: {scenario.name}")

    # Test arbitrage analysis
    print("\n💰 ARBITRAGE ANALYSIS:")
    for event_id in ['FED_RATE_CUT', 'OIL_150']:
        analysis = graph_engine.analyze_cross_market_arbitrage(event_id)
        if analysis.get('arbitrage_opportunities'):
            print(f"🎯 {event_id}: {len(analysis['arbitrage_opportunities'])} arbitrage opportunities")
            for opp in analysis['arbitrage_opportunities']:
                print(f"   • {opp['direction'].upper()} {opp['asset']} ({opp['confidence']:.1%} confidence)")

    # Test top scenarios dashboard
    print("\n📈 TOP SCENARIOS DASHBOARD:")
    dashboard = graph_engine.get_top_scenarios_dashboard(5)
    for scenario in dashboard['top_scenarios']:
        print(f"#{scenario['rank']}: {scenario['root_event']} (Score: {scenario['score']:.3f})")

    print("\n✅ Scenario Graph Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_scenario_graph_engine())
