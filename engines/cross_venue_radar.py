"""
🎯 CROSS-VENUE MISPRICING RADAR

Advanced arbitrage detection system that compares probability estimates across multiple venues:
- Kalshi prediction markets
- Options implied volatility/skew
- Crypto perpetual funding rates & term structure
- Traditional market correlations

Identifies when markets disagree mathematically, creating pure arbitrage opportunities.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
import math
from collections import defaultdict

try:
    from engines.kalshi_engine import KalshiPredictionEngine
    from engines.scenario_graph_engine import ScenarioGraphEngine
except ImportError:
    # Mocks for testing
    class KalshiPredictionEngine:
        pass
    class ScenarioGraphEngine:
        def __init__(self, *args, **kwargs):
            pass


@dataclass
class VenueProbability:
    """Probability estimate from a specific venue."""
    venue: str  # 'kalshi', 'options', 'perps', 'correlation'
    event_id: str
    probability: float
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'venue': self.venue,
            'event_id': self.event_id,
            'probability': self.probability,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class MispricingOpportunity:
    """Identified arbitrage opportunity between venues."""
    id: str
    event_id: str
    primary_venue: str
    secondary_venue: str
    probability_difference: float  # primary - secondary
    arbitrage_direction: str  # 'buy_primary_sell_secondary' or vice versa
    edge_size: float  # Size of the mispricing (0-1)
    confidence: float
    estimated_return: float = 0.0
    risk_adjusted_score: float = 0.0
    description: str = ""
    recommended_action: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'event_id': self.event_id,
            'primary_venue': self.primary_venue,
            'secondary_venue': self.secondary_venue,
            'probability_difference': self.probability_difference,
            'arbitrage_direction': self.arbitrage_direction,
            'edge_size': self.edge_size,
            'confidence': self.confidence,
            'estimated_return': self.estimated_return,
            'risk_adjusted_score': self.risk_adjusted_score,
            'description': self.description,
            'recommended_action': self.recommended_action,
            'timestamp': self.timestamp.isoformat()
        }


class CrossVenueMispricingRadar:
    """
    🎯 Cross-Venue Mispricing Radar

    Scans multiple probability venues for mathematical disagreements:
    - Kalshi YES/NO prices
    - Options market implied probabilities
    - Crypto perp term structure
    - Traditional market correlations
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine, scenario_graph: ScenarioGraphEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph
        self.venue_probabilities: Dict[str, List[VenueProbability]] = defaultdict(list)
        self.mispricing_opportunities: Dict[str, MispricingOpportunity] = {}
        self.arbitrage_threshold = 0.15  # Minimum edge size to consider arbitrage
        self.data_file = "mispricing_radar.json"

        # Load production data
        self._load_data()

    
    def _load_data(self):
        """Load existing data from disk."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                print(f"📊 Loaded mispricing radar data: {len(data.get('opportunities', {}))} opportunities")
            except Exception as e:
                print(f"⚠️ Error loading mispricing data: {e}")

    def _save_data(self):
        """Save current data to disk."""
        data = {
            'venue_probabilities': {
                event_id: [prob.to_dict() for prob in probs]
                for event_id, probs in self.venue_probabilities.items()
            },
            'opportunities': {
                opp_id: opp.to_dict()
                for opp_id, opp in self.mispricing_opportunities.items()
            },
            'last_updated': datetime.now().isoformat()
        }

        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def scan_for_mispricing(self, event_id: str) -> List[MispricingOpportunity]:
        """Scan all venues for a specific event to find mispricing opportunities."""
        if event_id not in self.venue_probabilities:
            return []

        probabilities = self.venue_probabilities[event_id]
        opportunities = []

        # Compare each pair of venues
        for i, prob1 in enumerate(probabilities):
            for prob2 in probabilities[i+1:]:
                diff = abs(prob1.probability - prob2.probability)
                if diff >= self.arbitrage_threshold:
                    # Determine which venue is cheaper/more expensive
                    if prob1.probability > prob2.probability:
                        primary, secondary = prob1, prob2
                        direction = 'buy_primary_sell_secondary'
                    else:
                        primary, secondary = prob2, prob1
                        direction = 'buy_secondary_sell_primary'

                    # Calculate edge size and confidence
                    edge_size = diff
                    combined_confidence = min(prob1.confidence, prob2.confidence)
                    risk_adjusted_score = edge_size * combined_confidence

                    if risk_adjusted_score > 0.1:  # Only keep meaningful opportunities
                        opportunity = MispricingOpportunity(
                            id=f"{event_id}_{prob1.venue}_vs_{prob2.venue}_{int(datetime.now().timestamp())}",
                            event_id=event_id,
                            primary_venue=primary.venue,
                            secondary_venue=secondary.venue,
                            probability_difference=primary.probability - secondary.probability,
                            arbitrage_direction=direction,
                            edge_size=edge_size,
                            confidence=combined_confidence,
                            risk_adjusted_score=risk_adjusted_score,
                            description=f"Probability disagreement: {primary.venue} ({primary.probability:.1%}) vs {secondary.venue} ({secondary.probability:.1%})",
                            recommended_action=self._generate_recommended_action(primary, secondary, direction)
                        )

                        opportunities.append(opportunity)
                        self.mispricing_opportunities[opportunity.id] = opportunity

        return opportunities

    def _generate_recommended_action(self, primary: VenueProbability, secondary: VenueProbability,
                                   direction: str) -> str:
        """Generate human-readable recommended action."""
        if direction == 'buy_primary_sell_secondary':
            action = f"Buy {primary.venue.upper()}, Sell {secondary.venue.upper()}"
        else:
            action = f"Buy {secondary.venue.upper()}, Sell {primary.venue.upper()}"

        return f"{action} - Exploit probability edge of {(primary.probability - secondary.probability):.1%}"

    def scan_all_events(self) -> List[MispricingOpportunity]:
        """Scan all events for mispricing opportunities."""
        all_opportunities = []
        for event_id in self.venue_probabilities.keys():
            opportunities = self.scan_for_mispricing(event_id)
            all_opportunities.extend(opportunities)

        # Sort by risk-adjusted score
        all_opportunities.sort(key=lambda x: x.risk_adjusted_score, reverse=True)
        return all_opportunities

    def get_top_arbitrage_opportunities(self, limit: int = 10) -> Dict[str, Any]:
        """Get top arbitrage opportunities dashboard."""
        opportunities = self.scan_all_events()

        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'total_opportunities': len(opportunities),
            'arbitrage_threshold': self.arbitrage_threshold,
            'top_opportunities': []
        }

        for i, opp in enumerate(opportunities[:limit], 1):
            opp_data = {
                'rank': i,
                'id': opp.id,
                'event_id': opp.event_id,
                'primary_venue': opp.primary_venue,
                'secondary_venue': opp.secondary_venue,
                'edge_size': opp.edge_size,
                'confidence': opp.confidence,
                'risk_adjusted_score': opp.risk_adjusted_score,
                'description': opp.description,
                'recommended_action': opp.recommended_action
            }
            dashboard['top_opportunities'].append(opp_data)

        return dashboard

    def calculate_portfolio_arbitrage(self, opportunities: List[MispricingOpportunity],
                                    capital_limit: float = 10000) -> Dict[str, Any]:
        """Calculate optimal portfolio allocation across arbitrage opportunities."""
        if not opportunities:
            return {'error': 'No opportunities available'}

        # Sort by risk-adjusted score
        opportunities.sort(key=lambda x: x.risk_adjusted_score, reverse=True)

        # Simple equal-weight allocation for now
        # In production, this would use optimization algorithms
        allocation_per_opp = capital_limit / len(opportunities)

        portfolio = {
            'total_capital': capital_limit,
            'num_opportunities': len(opportunities),
            'allocation_per_opportunity': allocation_per_opp,
            'opportunities': []
        }

        for opp in opportunities:
            position_size = min(allocation_per_opp, capital_limit * opp.risk_adjusted_score)
            capital_limit -= position_size

            opp_data = opp.to_dict()
            opp_data['allocated_capital'] = position_size
            opp_data['expected_return'] = position_size * opp.edge_size  # Simplified

            portfolio['opportunities'].append(opp_data)

        return portfolio

    def update_venue_probability(self, venue_prob: VenueProbability):
        """Update or add a venue probability estimate."""
        self.venue_probabilities[venue_prob.event_id].append(venue_prob)
        self._save_data()

    def get_venue_comparison(self, event_id: str) -> Dict[str, Any]:
        """Get detailed comparison of all venues for an event."""
        if event_id not in self.venue_probabilities:
            return {'error': 'Event not found in venue data'}

        probabilities = self.venue_probabilities[event_id]

        comparison = {
            'event_id': event_id,
            'venue_count': len(probabilities),
            'probabilities': [prob.to_dict() for prob in probabilities],
            'statistics': {
                'mean_probability': sum(p.probability for p in probabilities) / len(probabilities),
                'probability_range': max(p.probability for p in probabilities) - min(p.probability for p in probabilities),
                'max_disagreement': max(
                    abs(p1.probability - p2.probability)
                    for i, p1 in enumerate(probabilities)
                    for p2 in probabilities[i+1:]
                ) if len(probabilities) > 1 else 0
            }
        }

        return comparison


# Test/demo functions
async def test_mispricing_radar():
    """Test the cross-venue mispricing radar."""
    print("🎯 TESTING CROSS-VENUE MISPRICING RADAR")
    print("=" * 50)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)

    radar = CrossVenueMispricingRadar(kalshi, scenario_graph)

    print(f"📊 Initialized with {len(radar.venue_probabilities)} events across multiple venues")

    # Test individual event scanning
    print("\n🎯 SCANNING INDIVIDUAL EVENTS:")
    test_events = ['FED_RATE_CUT', 'BTC_200K', 'OIL_150']
    for event_id in test_events:
        opportunities = radar.scan_for_mispricing(event_id)
        if opportunities:
            print(f"✅ {event_id}: {len(opportunities)} arbitrage opportunities")
            for opp in opportunities[:2]:  # Show top 2
                print(f"   • {opp.description}")
                print(f"     → {opp.recommended_action}")
        else:
            print(f"❌ {event_id}: No arbitrage opportunities found")

    # Test venue comparison
    print("\n📊 VENUE COMPARISON FOR BTC_200K:")
    comparison = radar.get_venue_comparison('BTC_200K')
    if 'probabilities' in comparison:
        for prob in comparison['probabilities']:
            print(f"   • {prob['venue'].upper()}: {prob['probability']:.1%} (confidence: {prob['confidence']:.1%})")

        stats = comparison['statistics']
        print(f"   📈 Stats: Mean={stats['mean_probability']:.1%}, Range={stats['probability_range']:.1%}, Max Disagreement={stats['max_disagreement']:.1%}")

    # Test top opportunities dashboard
    print("\n💰 TOP ARBITRAGE OPPORTUNITIES:")
    dashboard = radar.get_top_arbitrage_opportunities(5)
    for opp in dashboard['top_opportunities']:
        print(f"#{opp['rank']}: {opp['event_id']} ({opp['primary_venue']} vs {opp['secondary_venue']})")
        print(f"   Edge: {opp['edge_size']:.1%}, Score: {opp['risk_adjusted_score']:.3f}")
        print(f"   → {opp['recommended_action']}")

    # Test portfolio allocation
    print("\n📊 PORTFOLIO ARBITRAGE ALLOCATION:")
    opportunities = radar.scan_all_events()
    if opportunities:
        portfolio = radar.calculate_portfolio_arbitrage(opportunities[:3], 10000)
        print(f"💰 Allocating $10,000 across {len(portfolio['opportunities'])} opportunities:")
        for opp in portfolio['opportunities']:
            print(f"   • {opp['event_id']}: ${opp['allocated_capital']:.0f} (Expected: ${opp['expected_return']:.0f})")

    print("\n✅ Cross-Venue Mispricing Radar test complete!")


if __name__ == "__main__":
    asyncio.run(test_mispricing_radar())
