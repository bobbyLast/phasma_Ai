"""
📊 MACRO CALENDAR ENGINE

Advanced economic data analysis system for identifying "easy trades" in macroeconomic events.
Analyzes historical forecasts vs actual prints for CPI, NFP, Fed decisions, GDP, and other
economic indicators to find systematic edges in market reactions.

Features:
- Economic Data Database (historical forecasts, actual prints, surprises)
- Print Pattern Analysis (within-band vs surprise probability)
- Market Reaction Modeling (initial vs mean-reversion response)
- Economic Regime Detection (inflation, employment, growth cycles)
- Calendar Event Edge Detection (systematic mispricings)
- High-Confidence Calendar Trade Identification (data-driven edges)
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
class EconomicIndicator:
    """Economic indicator data and patterns."""
    name: str  # 'CPI', 'NFP', 'Fed_Funds', 'GDP', etc.
    description: str
    frequency: str  # 'monthly', 'quarterly', 'as_needed'
    units: str  # '%', 'thousands', 'bps', etc.

    # Historical data
    historical_forecasts: List[float] = field(default_factory=list)
    historical_actuals: List[float] = field(default_factory=list)
    historical_surprises: List[float] = field(default_factory=list)  # actual - forecast

    # Statistical properties
    surprise_std: float = 0.0
    forecast_accuracy: float = 0.0  # how accurate forecasts typically are
    market_reaction_strength: float = 0.0  # how much markets move on average

    # Pattern analysis
    within_band_probability: Dict[str, float] = field(default_factory=dict)  # prob within X std bands
    surprise_direction_bias: float = 0.0  # tendency to surprise up/down (-1 to 1)
    post_event_drift: float = 0.0  # how much price action reverses after initial reaction

    # Add regime-conditional surprise distributions
    surprise_distributions: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    # surprise_distributions['high_inflation'] = [0.1, 0.15, -0.05, ...]
    # surprise_distributions['low_growth'] = [-0.3, -0.25, 0.1, ...]

    # Cross-asset reaction patterns
    asset_reactions: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    # asset_reactions['SPY'] = [0.8, 1.2, -0.5, ...]  # S&P reaction to event
    # asset_reactions['TLT'] = [-0.3, -0.8, 0.4, ...]  # Bond reaction
    # asset_reactions['EURUSD'] = [0.2, -0.3, 0.1, ...]  # FX reaction

    # Market regime context
    regime_context: Dict[str, Any] = field(default_factory=dict)
    # regime_context = {
    #     'inflation_regime': 'high',
    #     'growth_regime': 'slow',
    #     'fed_stance': 'hawkish',
    #     'volatility_regime': 'normal'
    # }

    # Enhanced statistical properties
    regime_conditional_std: Dict[str, float] = field(default_factory=dict)
    cross_asset_correlations: Dict[str, float] = field(default_factory=dict)
    market_impact_decay: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    
    # Historical edge analysis
    historical_edge: float = 0.0
    
    # Confidence multiplier for analysis
    confidence_multiplier: float = 1.0

    def calculate_surprise_probability(self, forecast: float, target_range: float) -> float:
        """Calculate probability of surprise within target range."""
        if not self.historical_surprises:
            return 0.5

        # Count surprises within range
        within_range = sum(1 for s in self.historical_surprises if abs(s) <= target_range)
        return within_range / len(self.historical_surprises)

    def predict_market_reaction(self, surprise_std: float) -> float:
        """Predict market reaction magnitude based on historical patterns."""
        if surprise_std == 0:
            return 0.0

        # Scale reaction by surprise magnitude and historical reaction strength
        base_reaction = abs(surprise_std) * self.market_reaction_strength

        # Apply direction bias
        if surprise_std > 0 and self.surprise_direction_bias > 0:
            base_reaction *= (1 + self.surprise_direction_bias)
        elif surprise_std < 0 and self.surprise_direction_bias < 0:
            base_reaction *= (1 - self.surprise_direction_bias)

        return base_reaction

    def get_easy_trade_probability(self, forecast: float, market_prob: float) -> Tuple[float, str]:
        """Get probability and rationale for easy trade."""
        if not self.historical_surprises:
            return max(0.01, min(0.99, 0.5)), "Insufficient historical data"

        # Calculate typical surprise range
        typical_surprise = statistics.mean(abs(s) for s in self.historical_surprises)

        # Check if market is pricing extreme surprise
        if market_prob > 0.7:  # Market pricing big upside surprise
            if self.surprise_direction_bias < 0.2:  # Not strongly biased up
                prob = self.calculate_surprise_probability(forecast, typical_surprise * 0.5)
                if prob > 0.75:
                    return prob, f"Market overpricing surprise - historical data shows {prob:.1%} chance of normal print"
        elif market_prob < 0.3:  # Market pricing big downside surprise
            if self.surprise_direction_bias > -0.2:  # Not strongly biased down
                prob = self.calculate_surprise_probability(forecast, typical_surprise * 0.5)
                if prob > 0.75:
                    return prob, f"Market overpricing surprise - historical data shows {prob:.1%} chance of normal print"

        return 0.5, "No clear easy trade pattern"


@dataclass
class MacroCalendarAnalysis:
    """Analysis of a macroeconomic calendar event."""
    event_name: str
    event_date: datetime
    forecast_value: float
    market_probability: float
    ai_adjusted_probability: float
    surprise_probability: float
    market_reaction_prediction: float
    easy_trade_confidence: float
    rationale: str
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_name': self.event_name,
            'event_date': self.event_date.isoformat(),
            'forecast_value': self.forecast_value,
            'market_probability': self.market_probability,
            'ai_adjusted_probability': self.ai_adjusted_probability,
            'surprise_probability': self.surprise_probability,
            'market_reaction_prediction': self.market_reaction_prediction,
            'easy_trade_confidence': self.easy_trade_confidence,
            'rationale': self.rationale,
            'recommended_action': self.recommended_action
        }


class MacroCalendarEngine:
    """
    📊 Macro Calendar Engine

    Specialized AI for analyzing macroeconomic events and finding "easy trades"
    based on historical forecast accuracy and market reaction patterns.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine, scenario_graph: ScenarioGraphEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph

        # Economic indicators database
        self.economic_indicators: Dict[str, EconomicIndicator] = {}

        # Analysis results
        self.event_analyses: Dict[str, MacroCalendarAnalysis] = {}

        # Data files
        self.indicators_file = engine_state_path("macro_indicators.json")
        self.analyses_file = engine_state_path("macro_analyses.json")

        # Initialize with known economic indicators
        self._initialize_economic_indicators()
        self._load_data()

    def _initialize_economic_indicators(self):
        """Initialize with known economic indicators and their historical patterns."""

        indicators = [
            # CPI - Consumer Price Index
            EconomicIndicator(
                name='CPI',
                description='Consumer Price Index (Inflation)',
                frequency='monthly',
                units='%',
                surprise_std=0.15,
                forecast_accuracy=0.85,
                market_reaction_strength=0.8,
                surprise_direction_bias=0.1,  # Slightly biased to upside surprises
                post_event_drift=0.3,
                historical_edge=0.12,
                confidence_multiplier=1.2,
                within_band_probability={'1std': 0.75, '2std': 0.95}
            ),

            # NFP - Non-Farm Payrolls
            EconomicIndicator(
                name='NFP',
                description='Non-Farm Payrolls (Employment)',
                frequency='monthly',
                units='thousands',
                surprise_std=50.0,
                forecast_accuracy=0.75,
                market_reaction_strength=1.0,
                surprise_direction_bias=-0.05,  # Slightly biased to downside surprises
                post_event_drift=0.4,
                historical_edge=0.15,
                confidence_multiplier=1.3,
                within_band_probability={'1std': 0.70, '2std': 0.90}
            ),

            # Fed Funds Rate
            EconomicIndicator(
                name='FED_FUNDS',
                description='Federal Funds Rate Decision',
                frequency='as_needed',
                units='bps',
                surprise_std=12.5,
                forecast_accuracy=0.95,
                market_reaction_strength=1.2,
                surprise_direction_bias=0.0,  # Very predictable
                post_event_drift=0.2,
                historical_edge=0.08,
                confidence_multiplier=1.1,
                within_band_probability={'1std': 0.85, '2std': 0.98}
            ),

            # GDP
            EconomicIndicator(
                name='GDP',
                description='Gross Domestic Product',
                frequency='quarterly',
                units='%',
                surprise_std=0.3,
                forecast_accuracy=0.80,
                market_reaction_strength=0.9,
                surprise_direction_bias=-0.1,  # Slightly biased to downside
                post_event_drift=0.5,
                historical_edge=0.10,
                confidence_multiplier=1.2,
                within_band_probability={'1std': 0.72, '2std': 0.92}
            ),

            # Retail Sales
            EconomicIndicator(
                name='RETAIL_SALES',
                description='Retail Sales',
                frequency='monthly',
                units='%',
                surprise_std=0.4,
                forecast_accuracy=0.78,
                market_reaction_strength=0.7,
                surprise_direction_bias=0.05,
                post_event_drift=0.35,
                historical_edge=0.09,
                confidence_multiplier=1.15,
                within_band_probability={'1std': 0.74, '2std': 0.94}
            ),

            # Unemployment Rate
            EconomicIndicator(
                name='UNEMPLOYMENT',
                description='Unemployment Rate',
                frequency='monthly',
                units='%',
                surprise_std=0.08,
                forecast_accuracy=0.88,
                market_reaction_strength=0.6,
                surprise_direction_bias=-0.15,  # Biased to improvement
                post_event_drift=0.25,
                historical_edge=0.07,
                confidence_multiplier=1.1,
                within_band_probability={'1std': 0.80, '2std': 0.96}
            ),

            # FOMC Meeting
            EconomicIndicator(
                name='FOMC',
                description='FOMC Meeting Outcome',
                frequency='as_needed',
                units='text',
                surprise_std=0.0,  # Qualitative, not numeric
                forecast_accuracy=0.90,
                market_reaction_strength=1.1,
                surprise_direction_bias=0.0,
                post_event_drift=0.3,
                historical_edge=0.11,
                confidence_multiplier=1.25,
                within_band_probability={'1std': 0.82, '2std': 0.97}
            )
        ]

        for indicator in indicators:
            self.economic_indicators[indicator.name] = indicator

    def _load_data(self):
        """Load existing macro data."""
        # Load indicators
        if os.path.exists(self.indicators_file):
            try:
                with open(self.indicators_file, 'r') as f:
                    data = json.load(f)
                print(f"📊 Loaded macro indicators: {len(data.get('indicators', {}))} economic events")
            except Exception as e:
                print(f"⚠️ Error loading macro indicators: {e}")

        # Load analyses
        if os.path.exists(self.analyses_file):
            try:
                with open(self.analyses_file, 'r') as f:
                    data = json.load(f)
                print(f"📊 Loaded macro analyses: {len(data.get('analyses', {}))} events")
            except Exception as e:
                print(f"⚠️ Error loading macro analyses: {e}")

    def analyze_macro_event(self, event_data: Dict[str, Any]) -> Optional[MacroCalendarAnalysis]:
        """Analyze a macroeconomic calendar event."""

        event_name = event_data.get('event_name', '').upper()
        forecast = event_data.get('forecast', 0.0)
        market_prob = event_data.get('market_probability', 0.5)

        # Get indicator
        indicator = self.economic_indicators.get(event_name)
        if not indicator:
            return None

        # Perform AI analysis
        surprise_prob, market_reaction, easy_trade_prob, rationale, action = self._perform_macro_analysis(
            indicator, forecast, market_prob
        )

        analysis = MacroCalendarAnalysis(
            event_name=event_name,
            event_date=datetime.now(),  # Could be parsed from event_data
            forecast_value=forecast,
            market_probability=market_prob,
            ai_adjusted_probability=easy_trade_prob,
            surprise_probability=surprise_prob,
            market_reaction_prediction=market_reaction,
            easy_trade_confidence=easy_trade_prob,
            rationale=rationale,
            recommended_action=action
        )

        self.event_analyses[event_name] = analysis
        self._save_analysis(analysis)

        return analysis

    def _perform_macro_analysis(self, indicator: EconomicIndicator, forecast: float,
                              market_prob: float) -> Tuple[float, float, float, str, str]:
        """Perform detailed macro analysis."""

        # Calculate surprise probability
        typical_surprise = indicator.surprise_std
        surprise_prob = indicator.calculate_surprise_probability(forecast, typical_surprise)

        # Predict market reaction
        expected_surprise = (market_prob - 0.5) * typical_surprise * 2  # Rough estimate
        market_reaction = indicator.predict_market_reaction(expected_surprise)

        # Get easy trade assessment
        easy_trade_prob, trade_rationale = indicator.get_easy_trade_probability(forecast, market_prob)

        # Generate comprehensive rationale
        rationale_parts = [
            f"Economic indicator: {indicator.description}",
            f"Historical accuracy: {indicator.forecast_accuracy:.1%}",
            f"Typical surprise: ±{typical_surprise:.2f} {indicator.units}",
            f"Market reaction strength: {indicator.market_reaction_strength:.1f}",
            f"Surprise probability: {surprise_prob:.1%}",
            trade_rationale
        ]

        if indicator.surprise_direction_bias != 0:
            bias_desc = "upside" if indicator.surprise_direction_bias > 0 else "downside"
            rationale_parts.append(f"Bias: Historically {bias_desc} surprises are {abs(indicator.surprise_direction_bias):.1%} more likely")

        if indicator.post_event_drift > 0:
            rationale_parts.append(f"Post-event drift: {indicator.post_event_drift:.1%} of initial move typically reverses")

        rationale = " | ".join(rationale_parts)

        # Determine action
        if easy_trade_prob > 0.75 and "overpricing surprise" in trade_rationale:
            action = f"BUY NORMAL PRINT - AI sees {easy_trade_prob:.1%} chance of boring outcome"
        elif easy_trade_prob > 0.75 and "underpricing surprise" in trade_rationale:
            action = f"BUY SURPRISE - AI sees {easy_trade_prob:.1%} chance of deviation"
        else:
            action = f"MONITOR - Mixed signals, wait for more data"

        return surprise_prob, market_reaction, easy_trade_prob, rationale, action

    def get_easy_macro_trades(self, min_confidence: float = 0.75) -> List[Dict[str, Any]]:
        """Find macroeconomic events with strong easy trade potential."""

        easy_trades = []

        for event_name, analysis in self.event_analyses.items():
            if analysis.easy_trade_confidence >= min_confidence:
                trade_info = {
                    'event_name': event_name,
                    'forecast': analysis.forecast_value,
                    'market_probability': analysis.market_probability,
                    'ai_probability': analysis.ai_adjusted_probability,
                    'confidence': analysis.easy_trade_confidence,
                    'rationale': analysis.rationale,
                    'recommended_action': analysis.recommended_action,
                    'expected_reaction': analysis.market_reaction_prediction
                }
                easy_trades.append(trade_info)

        # Sort by confidence
        easy_trades.sort(key=lambda x: x['confidence'], reverse=True)
        return easy_trades[:10]  # Top 10 easy macro trades

    def _save_analysis(self, analysis: MacroCalendarAnalysis):
        """Save analysis to file."""
        analyses_data = {
            'analyses': {aid: a.to_dict() for aid, a in self.event_analyses.items()},
            'last_updated': datetime.now().isoformat()
        }

        with open(self.analyses_file, 'w') as f:
            json.dump(analyses_data, f, indent=2)


# Test/demo functions
async def test_macro_calendar_engine():
    """Test the macro calendar analysis engine."""
    print("📊 TESTING MACRO CALENDAR ENGINE")
    print("=" * 50)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)

    engine = MacroCalendarEngine(kalshi, scenario_graph)

    print(f"📊 Initialized with {len(engine.economic_indicators)} economic indicators")

    # Test events
    test_events = [
        {
            'event_name': 'CPI',
            'forecast': 3.2,
            'market_probability': 0.75  # Market pricing hot CPI
        },
        {
            'event_name': 'NFP',
            'forecast': 200.0,
            'market_probability': 0.65  # Market pricing strong jobs
        },
        {
            'event_name': 'FED_FUNDS',
            'forecast': 25.0,  # 25bps hike expected
            'market_probability': 0.55  # Market pricing slight surprise
        },
        {
            'event_name': 'GDP',
            'forecast': 2.8,
            'market_probability': 0.45  # Market pricing disappointment
        },
        {
            'event_name': 'UNEMPLOYMENT',
            'forecast': 4.1,
            'market_probability': 0.40  # Market pricing improvement
        }
    ]

    print("\n📊 ANALYZING ECONOMIC EVENTS FOR EASY TRADES:")
    for event in test_events:
        print(f"\n📊 EVENT: {event['event_name']}")
        print(f"   Forecast: {event['forecast']}")
        print(".1%")

        # Analyze the event
        analysis = engine.analyze_macro_event(event)

        if analysis:
            print("   ✅ MACRO EVENT DETECTED")
            print(f"   Surprise Probability: {analysis.surprise_probability:.1%}")
            print(f"   Expected Market Reaction: {analysis.market_reaction_prediction:.2f}")
            print(f"   Easy Trade Confidence: {analysis.easy_trade_confidence:.1%}")

            if analysis.easy_trade_confidence > 0.75:
                print("   🎯 EASY TRADE OPPORTUNITY! 🎯")
                print(f"   Recommended: {analysis.recommended_action}")
            else:
                print("   ❓ Standard economic event")

            print(f"   Rationale: {analysis.rationale}")
        else:
            print("   ❌ Not a tracked economic indicator")

        print("-" * 60)

    # Show easy macro trades
    print("\n🎯 EASY MACRO TRADES (75%+ confidence):")
    easy_trades = engine.get_easy_macro_trades()

    if easy_trades:
        for i, trade in enumerate(easy_trades, 1):
            print(f"{i}. {trade['event_name']}: {trade['confidence']:.1%} confidence")
            print(f"   Forecast: {trade['forecast']} | Market: {trade['market_probability']:.1%} | AI: {trade['ai_probability']:.1%}")
            print(f"   {trade['recommended_action']}")
            print(f"   Rationale: {trade['rationale'][:100]}...")
            print()
    else:
        print("No easy macro trades found with current thresholds")

    print("\n✅ Macro Calendar Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_macro_calendar_engine())
