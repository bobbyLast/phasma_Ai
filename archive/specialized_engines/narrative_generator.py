"""
📖 NARRATIVE GENERATOR

Transforms complex AI analysis into compelling human stories for:
- Winners Gallery highlight reels
- Telegram signal notifications
- Portfolio performance narratives
- Market scenario explanations

Turns quantitative data into engaging, actionable stories that traders can understand and act upon.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
import random
from collections import defaultdict

try:
    from engines.top_10_dashboard import UniverseOpportunity, Top10OpportunitiesDashboard
    from engines.scenario_graph_engine import ScenarioTree
    from engines.cross_venue_radar import MispricingOpportunity
except ImportError:
    # Mocks for testing
    @dataclass
    class UniverseOpportunity:
        id: str = ""
        opportunity_type: str = ""
        title: str = ""
        description: str = ""
        primary_asset: str = ""
        secondary_assets: List[str] = field(default_factory=list)
        score: Any = None
        expected_return: float = 0.0
        risk_level: str = 'medium'
        time_horizon: str = 'medium'
        confidence_level: float = 0.0
        recommended_position_size: float = 0.0
        rationale: str = ""
        action_required: str = ""
        tags: Set[str] = field(default_factory=set)
        last_updated: datetime = field(default_factory=datetime.now)
        metadata: Dict[str, Any] = field(default_factory=dict)

    class Top10OpportunitiesDashboard:
        pass

    @dataclass
    class ScenarioTree:
        id: str = ""
        name: str = ""
        root_event: str = ""
        branches: List[Any] = field(default_factory=list)
        total_probability: float = 0.0
        expected_pl: float = 0.0
        risk_adjusted_score: float = 0.0
        description: str = ""
        created_at: datetime = field(default_factory=datetime.now)

    @dataclass
    class MispricingOpportunity:
        id: str = ""
        event_id: str = ""
        primary_venue: str = ""
        secondary_venue: str = ""
        probability_difference: float = 0.0
        arbitrage_direction: str = ""
        edge_size: float = 0.0
        confidence: float = 0.5
        estimated_return: float = 0.0
        risk_adjusted_score: float = 0.0
        description: str = ""
        recommended_action: str = ""
        timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class NarrativeTemplate:
    """Template for generating narratives."""
    template_type: str  # 'opportunity', 'scenario', 'arbitrage', 'performance'
    structure: List[str]  # List of narrative sections
    tone_options: List[str]  # 'professional', 'excited', 'cautious', 'confident'
    length_options: List[str]  # 'brief', 'detailed', 'comprehensive'

    def generate_narrative(self, data: Dict[str, Any], tone: str = 'professional',
                          length: str = 'detailed') -> str:
        """Generate a narrative using this template."""
        # This would be implemented with actual template logic
        return f"Generated {self.template_type} narrative"


class NarrativeGenerator:
    """
    📖 Narrative Generator

    Transforms quantitative trading data into compelling human stories.
    Makes complex market analysis accessible and actionable.
    """

    def __init__(self):
        self.templates = self._load_templates()
        self.narratives_file = "generated_narratives.json"
        self.generated_narratives: Dict[str, Dict[str, Any]] = {}

    def _load_templates(self) -> Dict[str, NarrativeTemplate]:
        """Load narrative templates."""
        templates = {}

        # Opportunity narrative template
        templates['opportunity'] = NarrativeTemplate(
            template_type='opportunity',
            structure=[
                'hook',           # Grab attention
                'context',        # Set the scene
                'analysis',       # Explain the AI reasoning
                'opportunity',    # Describe the trade setup
                'rationale',      # Why it makes sense
                'action',         # What to do
                'risk_reward',    # The payoff profile
                'urgency'         # Why act now
            ],
            tone_options=['professional', 'excited', 'confident', 'cautious'],
            length_options=['brief', 'detailed', 'comprehensive']
        )

        # Scenario narrative template
        templates['scenario'] = NarrativeTemplate(
            template_type='scenario',
            structure=[
                'setup',          # The scenario premise
                'probability',    # Likelihood assessment
                'catalysts',      # What would make it happen
                'impacts',        # Market consequences
                'opportunities',  # Trading implications
                'hedges',         # Risk management
                'timeline'        # When to expect outcomes
            ],
            tone_options=['analytical', 'strategic', 'forward_looking'],
            length_options=['brief', 'detailed', 'comprehensive']
        )

        # Arbitrage narrative template
        templates['arbitrage'] = NarrativeTemplate(
            template_type='arbitrage',
            structure=[
                'discovery',      # How the mispricing was found
                'explanation',    # Why it exists
                'mechanics',      # How the arbitrage works
                'edge',          # Size of the opportunity
                'execution',     # How to trade it
                'risks',         # What could go wrong
                'horizon'        # How long it lasts
            ],
            tone_options=['quantitative', 'opportunistic', 'methodical'],
            length_options=['brief', 'detailed', 'technical']
        )

        return templates

    def generate_opportunity_narrative(self, opportunity: UniverseOpportunity,
                                      tone: str = 'confident',
                                      length: str = 'detailed') -> str:
        """Generate a compelling narrative for a trading opportunity."""

        if length == 'brief':
            return self._generate_brief_opportunity_narrative(opportunity)
        elif length == 'detailed':
            return self._generate_detailed_opportunity_narrative(opportunity)
        else:  # comprehensive
            return self._generate_comprehensive_opportunity_narrative(opportunity)

    def _generate_brief_opportunity_narrative(self, opp: UniverseOpportunity) -> str:
        """Generate a brief opportunity narrative."""
        return f"""🚀 {opp.title}

{opp.description}

💰 Expected Return: {opp.expected_return:.0%}
🎯 Confidence: {opp.confidence_level:.0%}
⚡ Action: {opp.action_required}

#PhasmaAI #TradingOpportunity"""

    def _generate_detailed_opportunity_narrative(self, opp: UniverseOpportunity) -> str:
        """Generate a detailed opportunity narrative."""

        # Build the narrative
        narrative_parts = []

        # Hook
        if opp.opportunity_type == 'kalshi_market':
            narrative_parts.append(f"🎯 PREDICTION MARKET OPPORTUNITY: {opp.title}")
        elif opp.opportunity_type == 'cross_market_arbitrage':
            narrative_parts.append(f"💎 CROSS-MARKET ARBITRAGE: {opp.title}")
        elif opp.opportunity_type == 'scenario_tree':
            narrative_parts.append(f"🌍 SCENARIO PLAY: {opp.title}")
        else:
            narrative_parts.append(f"🚀 TRADING OPPORTUNITY: {opp.title}")

        narrative_parts.append("")  # Empty line

        # Context & Analysis
        narrative_parts.append(f"📊 THE SETUP:")
        narrative_parts.append(f"{opp.description}")
        narrative_parts.append("")

        # Rationale
        narrative_parts.append(f"🧠 WHY THIS MATTERS:")
        narrative_parts.append(f"{opp.rationale}")
        narrative_parts.append("")

        # Numbers
        narrative_parts.append(f"📈 THE NUMBERS:")
        narrative_parts.append(f"• Expected Return: {opp.expected_return:.1%}")
        narrative_parts.append(f"• Confidence Level: {opp.confidence_level:.1%}")
        narrative_parts.append(f"• Risk Level: {opp.risk_level.title()}")
        narrative_parts.append(f"• Time Horizon: {opp.time_horizon.title()}")
        if opp.recommended_position_size > 0:
            narrative_parts.append(f"• Suggested Position: ${opp.recommended_position_size:,.0f}")
        narrative_parts.append("")

        # Action
        narrative_parts.append(f"⚡ EXECUTE THE TRADE:")
        narrative_parts.append(f"{opp.action_required}")
        narrative_parts.append("")

        # Risk/Reward
        narrative_parts.append(f"⚖️ RISK/REWARD PROFILE:")
        if opp.expected_return > 0.20:
            narrative_parts.append("High-reward opportunity with elevated risk")
        elif opp.expected_return > 0.10:
            narrative_parts.append("Solid risk-adjusted opportunity")
        else:
            narrative_parts.append("Conservative position with steady upside")

        if opp.tags:
            narrative_parts.append("")
            narrative_parts.append(f"🏷️ TAGS: {' • '.join(f'#{tag}' for tag in opp.tags)}")

        narrative_parts.append("")
        narrative_parts.append("🤖 Phasma AI - Advanced Market Intelligence")

        return "\n".join(narrative_parts)

    def _generate_comprehensive_opportunity_narrative(self, opp: UniverseOpportunity) -> str:
        """Generate a comprehensive opportunity narrative with full analysis."""
        # Similar to detailed but with more depth - would include metadata analysis
        detailed = self._generate_detailed_opportunity_narrative(opp)

        # Add comprehensive elements
        comprehensive_parts = [detailed]

        if opp.metadata:
            comprehensive_parts.append("")
            comprehensive_parts.append("🔬 TECHNICAL ANALYSIS:")
            for key, value in opp.metadata.items():
                if isinstance(value, (int, float)):
                    comprehensive_parts.append(f"• {key.replace('_', ' ').title()}: {value}")
                elif isinstance(value, str) and len(value) < 100:
                    comprehensive_parts.append(f"• {key.replace('_', ' ').title()}: {value}")

        return "\n".join(comprehensive_parts)

    def generate_scenario_narrative(self, scenario: ScenarioTree,
                                   tone: str = 'strategic',
                                   length: str = 'detailed') -> str:
        """Generate a narrative for a scenario tree."""

        narrative_parts = []

        # Header
        narrative_parts.append(f"🌍 SCENARIO ANALYSIS: {scenario.name}")
        narrative_parts.append("")
        narrative_parts.append(f"🎭 Premise: {scenario.description}")
        narrative_parts.append("")

        # Probability breakdown
        narrative_parts.append("📊 PROBABILITY BREAKDOWN:")
        for branch in scenario.branches:
            narrative_parts.append(f"• {branch.description}: {branch.probability:.1%}")
        narrative_parts.append("")

        # Expected outcomes
        narrative_parts.append("🎯 IMPLICATIONS:")
        if scenario.expected_pl > 0:
            narrative_parts.append(f"Expected payoff profile shows {scenario.expected_pl:.1%} potential return")
        else:
            narrative_parts.append("Defensive positioning recommended for this scenario")

        narrative_parts.append("")
        narrative_parts.append(f"🎖️ Scenario Score: {scenario.risk_adjusted_score:.3f}")
        narrative_parts.append("")
        narrative_parts.append("🤖 Phasma AI Scenario Engine")

        return "\n".join(narrative_parts)

    def generate_arbitrage_narrative(self, arbitrage: MispricingOpportunity,
                                    tone: str = 'quantitative',
                                    length: str = 'detailed') -> str:
        """Generate a narrative for an arbitrage opportunity."""

        narrative_parts = []

        # Header
        narrative_parts.append(f"💎 ARBITRAGE DISCOVERY: {arbitrage.event_id}")
        narrative_parts.append("")
        narrative_parts.append(f"🎯 Mispricing Found: {arbitrage.description}")
        narrative_parts.append("")

        # The edge
        narrative_parts.append("📊 THE EDGE:")
        narrative_parts.append(f"• Probability Difference: {arbitrage.probability_difference:.1%}")
        narrative_parts.append(f"• Edge Size: {arbitrage.edge_size:.1%}")
        narrative_parts.append(f"• Confidence: {arbitrage.confidence:.1%}")
        narrative_parts.append(f"• Risk-Adjusted Score: {arbitrage.risk_adjusted_score:.3f}")
        narrative_parts.append("")

        # Execution
        narrative_parts.append("⚡ EXECUTION:")
        narrative_parts.append(f"{arbitrage.recommended_action}")
        narrative_parts.append("")

        # Risk management
        narrative_parts.append("🛡️ RISK MANAGEMENT:")
        narrative_parts.append("• Monitor for convergence as expiration approaches")
        narrative_parts.append("• Position sizing based on edge confidence")
        narrative_parts.append("• Stop conditions if edge disappears")

        narrative_parts.append("")
        narrative_parts.append("🤖 Phasma AI Arbitrage Engine")

        return "\n".join(narrative_parts)

    def generate_portfolio_narrative(self, portfolio_data: Dict[str, Any],
                                    performance_period: str = "last_24h") -> str:
        """Generate a narrative for portfolio performance."""

        narrative_parts = []

        narrative_parts.append("📊 PORTFOLIO PERFORMANCE NARRATIVE")
        narrative_parts.append(f"Period: {performance_period.upper()}")
        narrative_parts.append("")

        # Performance summary
        total_return = portfolio_data.get('total_return', 0)
        if total_return > 0:
            narrative_parts.append(f"🟢 GAIN: +{total_return:.2f}%")
        else:
            narrative_parts.append(f"🔴 LOSS: {total_return:.2f}%")

        # Key highlights
        winners = portfolio_data.get('top_performers', [])
        if winners:
            narrative_parts.append("")
            narrative_parts.append("🏆 TOP PERFORMERS:")
            for winner in winners[:3]:
                narrative_parts.append(f"• {winner.get('symbol', 'N/A')}: +{winner.get('return', 0):.1f}%")

        # Analysis
        narrative_parts.append("")
        narrative_parts.append("🧠 ANALYSIS:")
        narrative_parts.append("• Market regime: " + portfolio_data.get('regime_assessment', 'Mixed conditions'))
        narrative_parts.append("• Best performing strategy: " + portfolio_data.get('best_strategy', 'Cross-market arbitrage'))

        narrative_parts.append("")
        narrative_parts.append("🤖 Phasma AI Portfolio Intelligence")

        return "\n".join(narrative_parts)

    def generate_top_10_highlight_reel(self, top_10_data: Dict[str, Any]) -> str:
        """Generate a highlight reel narrative for the top 10 opportunities."""

        narrative_parts = []

        narrative_parts.append("🎬 PHASMA AI TOP 10 OPPORTUNITIES HIGHLIGHT REEL")
        narrative_parts.append("=" * 50)
        narrative_parts.append("")

        # Market overview
        narrative_parts.append("🌍 MARKET OVERVIEW:")
        narrative_parts.append(f"Total opportunities tracked: {top_10_data.get('total_opportunities', 0)}")
        narrative_parts.append(f"Last refresh: {top_10_data.get('timestamp', 'Unknown')}")
        narrative_parts.append("")

        # Top opportunities
        narrative_parts.append("🥇 TOP OPPORTUNITIES:")
        narrative_parts.append("")

        for opp in top_10_data.get('top_10', []):
            rank = opp.get('rank', '?')
            title = opp.get('title', 'Unknown')
            score = opp.get('score', {}).get('total_score', 0)
            expected_return = opp.get('expected_return', 0)
            action = opp.get('action_required', 'No action specified')

            narrative_parts.append(f"#{rank}: {title}")
            narrative_parts.append(f"   Score: {score:.3f} | Expected: {expected_return:.1%}")
            narrative_parts.append(f"   → {action}")
            narrative_parts.append("")

        # Market insights
        narrative_parts.append("💡 MARKET INSIGHTS:")
        narrative_parts.append("• AI is identifying multi-venue arbitrage opportunities")
        narrative_parts.append("• Cross-market scenarios showing strong conviction")
        narrative_parts.append("• Traditional signals remain robust foundation")
        narrative_parts.append("")

        narrative_parts.append("🤖 Phasma AI - Universe Opportunity Scanner")

        return "\n".join(narrative_parts)

    def generate_market_update_narrative(self, market_conditions: Dict[str, Any]) -> str:
        """Generate a market update narrative."""

        narrative_parts = []

        narrative_parts.append("🌍 PHASMA AI MARKET UPDATE")
        narrative_parts.append("")

        # Market regime
        regime = market_conditions.get('regime', 'neutral')
        if regime == 'bullish':
            narrative_parts.append("🟢 BULLISH REGIME DETECTED")
        elif regime == 'bearish':
            narrative_parts.append("🔴 BEARISH REGIME DETECTED")
        else:
            narrative_parts.append("🟡 NEUTRAL/MIXED CONDITIONS")

        narrative_parts.append("")

        # Key drivers
        drivers = market_conditions.get('key_drivers', [])
        if drivers:
            narrative_parts.append("🎯 KEY MARKET DRIVERS:")
            for driver in drivers:
                narrative_parts.append(f"• {driver}")
            narrative_parts.append("")

        # Opportunity outlook
        outlook = market_conditions.get('opportunity_outlook', 'Mixed opportunities available')
        narrative_parts.append(f"🎪 OPPORTUNITY OUTLOOK:")
        narrative_parts.append(f"{outlook}")

        narrative_parts.append("")
        narrative_parts.append("🤖 Phasma AI Market Intelligence")

        return "\n".join(narrative_parts)

    def save_narrative(self, narrative_id: str, narrative_data: Dict[str, Any]):
        """Save a generated narrative."""
        self.generated_narratives[narrative_id] = {
            'narrative': narrative_data.get('narrative', ''),
            'type': narrative_data.get('type', 'general'),
            'timestamp': datetime.now().isoformat(),
            'metadata': narrative_data
        }

        # Save to file
        with open(self.narratives_file, 'w') as f:
            json.dump(self.generated_narratives, f, indent=2)

    def get_narrative_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent narrative generation history."""
        narratives = list(self.generated_narratives.values())
        narratives.sort(key=lambda x: x['timestamp'], reverse=True)
        return narratives[:limit]


# Test/demo functions
async def test_narrative_generator():
    """Test the narrative generator."""
    print("📖 TESTING NARRATIVE GENERATOR")
    print("=" * 50)

    generator = NarrativeGenerator()

    # Mock opportunity data
    mock_opportunity = UniverseOpportunity(
        id="test_apple_ceo",
        opportunity_type="traditional_signal",
        title="Tim Cook Apple CEO Reappointment Cross-Market",
        description="High probability Tim Cook remains Apple CEO - stock impact opportunity",
        primary_asset="AAPL",
        expected_return=0.25,
        risk_level="low",
        time_horizon="long",
        confidence_level=0.8,
        recommended_position_size=10000,
        rationale="CEO track record analysis shows positive Apple stock impact",
        action_required="Buy AAPL calls with 6-12 month expiry",
        tags={"ceo", "apple", "fundamental"}
    )

    print("📝 GENERATING OPPORTUNITY NARRATIVES:")
    print()

    # Brief narrative
    print("BRIEF VERSION:")
    brief = generator.generate_opportunity_narrative(mock_opportunity, length='brief')
    print(brief)
    print("-" * 50)

    # Detailed narrative
    print("DETAILED VERSION:")
    detailed = generator.generate_opportunity_narrative(mock_opportunity, length='detailed')
    print(detailed)
    print("-" * 50)

    # Scenario narrative test
    print("SCENARIO NARRATIVE:")
    mock_scenario = ScenarioTree(
        id="scenario_fed_cut",
        name="Fed Rate Cut Scenario",
        root_event="FED_RATE_CUT",
        branches=[],
        description="Federal Reserve implements 0.25% rate cut in March 2025",
        risk_adjusted_score=0.7
    )

    scenario_narrative = generator.generate_scenario_narrative(mock_scenario)
    print(scenario_narrative)
    print("-" * 50)

    # Arbitrage narrative test
    print("ARBITRAGE NARRATIVE:")
    mock_arbitrage = MispricingOpportunity(
        id="arb_btc_kalshi_options",
        event_id="BTC_200K",
        primary_venue="kalshi",
        secondary_venue="options",
        probability_difference=0.15,
        edge_size=0.15,
        confidence=0.75,
        description="Kalshi shows 25% BTC probability vs options 40%",
        recommended_action="Buy Kalshi YES, Sell equivalent options position",
        risk_adjusted_score=0.105
    )

    arbitrage_narrative = generator.generate_arbitrage_narrative(mock_arbitrage)
    print(arbitrage_narrative)
    print("-" * 50)

    # Portfolio narrative test
    print("PORTFOLIO NARRATIVE:")
    mock_portfolio = {
        'total_return': 2.34,
        'top_performers': [
            {'symbol': 'AAPL', 'return': 5.2},
            {'symbol': 'NVDA', 'return': 3.8},
            {'symbol': 'BTC-USD', 'return': 2.1}
        ],
        'regime_assessment': 'Bullish with volatility',
        'best_strategy': 'Cross-market arbitrage'
    }

    portfolio_narrative = generator.generate_portfolio_narrative(mock_portfolio)
    print(portfolio_narrative)
    print("-" * 50)

    # Market update test
    print("MARKET UPDATE NARRATIVE:")
    mock_market = {
        'regime': 'bullish',
        'key_drivers': [
            'Fed rate cut expectations building',
            'AI sector momentum accelerating',
            'Cross-market arbitrage opportunities emerging'
        ],
        'opportunity_outlook': 'Strong conviction in multi-asset strategies'
    }

    market_narrative = generator.generate_market_update_narrative(mock_market)
    print(market_narrative)

    print("\n✅ Narrative Generator test complete!")


if __name__ == "__main__":
    asyncio.run(test_narrative_generator())
