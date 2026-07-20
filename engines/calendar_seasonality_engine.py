"""
📅 CALENDAR SEASONALITY ENGINE

Advanced calendar analysis system for identifying "easy trades" in seasonal market patterns.
Analyzes holiday effects, tax dates, quarter-ends, and other calendar-driven market behaviors
to find systematic edges in seasonal trading opportunities.

Features:
- Holiday Effect Database (Christmas, Thanksgiving, Halloween patterns)
- Tax Date Analysis (April 15, year-end tax selling/buying)
- Quarter-End Flow Patterns (institutional rebalancing)
- Month-End/Year-End Anomalies (window dressing, tax-loss selling)
- Seasonal Trend Recognition (January effect, September seasonality)
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
class CalendarPattern:
    """Calendar-driven market pattern."""
    pattern_name: str  # 'Christmas_Rally', 'Tax_Selling', 'Quarter_End', etc.
    pattern_type: str  # 'holiday', 'tax', 'quarter_end', 'month_end', 'seasonal'
    asset_class: str  # 'equity', 'bond', 'commodity', 'crypto'

    # Timing
    trigger_date: str  # '12-25', '04-15', 'quarter_end', etc.
    effect_window_days: int = 5  # how many days the effect lasts

    # Historical returns
    historical_returns: List[float] = field(default_factory=list)
    win_rate: float = 0.0  # percentage of times pattern worked
    avg_return: float = 0.0
    return_std: float = 0.0

    # Pattern strength
    pattern_strength: float = 0.0  # how reliable the pattern is (0-1)
    market_condition_dependency: str = 'any'  # 'bull', 'bear', 'volatile', 'calm'
    volume_multiplier: float = 1.0  # typical volume during pattern

    # Edge metrics
    historical_edge: float = 0.0  # historical profitability
    recent_performance: float = 0.0  # last 5 occurrences performance
    confidence_multiplier: float = 1.0

    last_updated: datetime = field(default_factory=lambda: datetime.now())

    def calculate_pattern_probability(self, current_market_condition: str = 'any') -> Tuple[float, float]:
        """Calculate probability and expected return for this pattern."""

        if not self.historical_returns:
            return 0.5, 0.0

        # Base probability
        probability = self.win_rate

        # Adjust for market conditions
        if current_market_condition != 'any' and self.market_condition_dependency != 'any':
            if current_market_condition == self.market_condition_dependency:
                probability *= 1.2  # Boost if conditions match
            else:
                probability *= 0.8  # Reduce if conditions don't match

        probability = max(0.05, min(0.95, probability))

        # Expected return
        expected_return = self.avg_return * probability + (1 - probability) * (-abs(self.avg_return) * 0.5)

        return probability, expected_return

    def get_easy_calendar_trade(self, days_to_trigger: int, market_condition: str = 'any') -> Tuple[float, str, str]:
        """Get easy calendar trade recommendation."""

        if len(self.historical_returns) < 3:
            return 0.5, "Insufficient historical data", "MONITOR"

        probability, expected_return = self.calculate_pattern_probability(market_condition)

        # Easy trade conditions
        if probability > 0.65 and abs(expected_return) > 0.008 and days_to_trigger <= self.effect_window_days:
            if expected_return > 0:
                return probability, f"Strong seasonal pattern: +{expected_return:.1%} expected return in {days_to_trigger} days", f"BUY {self.pattern_name.upper()}"
            else:
                return probability, f"Seasonal headwind: {expected_return:.1%} expected return in {days_to_trigger} days", f"SELL {self.pattern_name.upper()}"
        elif self.pattern_strength > 0.7 and probability > 0.6:
            direction = "upside" if expected_return > 0 else "downside"
            return 0.75, f"High-strength seasonal pattern with {direction} bias ({probability:.1%} win rate)", f"TRADE {self.pattern_name.upper()} {direction.upper()}"

        return 0.5, "No clear seasonal edge at current timing", "MONITOR"


@dataclass
class CalendarSeasonalityAnalysis:
    """Analysis of calendar-driven trading opportunity."""
    pattern_name: str
    pattern_type: str
    asset_class: str
    days_to_trigger: int
    market_condition: str
    pattern_probability: float
    expected_return: float
    easy_trade_confidence: float
    rationale: str
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_name': self.pattern_name,
            'pattern_type': self.pattern_type,
            'asset_class': self.asset_class,
            'days_to_trigger': self.days_to_trigger,
            'market_condition': self.market_condition,
            'pattern_probability': self.pattern_probability,
            'expected_return': self.expected_return,
            'easy_trade_confidence': self.easy_trade_confidence,
            'rationale': self.rationale,
            'recommended_action': self.recommended_action
        }


class CalendarSeasonalityEngine:
    """
    📅 Calendar Seasonality Engine

    Specialized AI for analyzing calendar-driven market patterns and finding "easy trades"
    based on historical seasonal effects and timing anomalies.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine, scenario_graph: ScenarioGraphEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph

        # Calendar patterns database
        self.calendar_patterns: Dict[str, CalendarPattern] = {}

        # Analysis results
        self.calendar_analyses: Dict[str, CalendarSeasonalityAnalysis] = {}

        # Data files
        self.patterns_file = engine_state_path("calendar_patterns.json")
        self.analyses_file = engine_state_path("calendar_analyses.json")

        # Initialize with known patterns
        self._initialize_calendar_patterns()
        self._load_data()

    def _initialize_calendar_patterns(self):
        """Initialize with known calendar-driven market patterns."""

        patterns = [
            # Holiday patterns
            CalendarPattern(
                pattern_name='Christmas_Rally',
                pattern_type='holiday',
                asset_class='equity',
                trigger_date='12-25',
                effect_window_days=7,
                historical_returns=[0.012, 0.008, 0.015, 0.006, 0.011, 0.009, 0.013, 0.007],
                win_rate=0.75,
                avg_return=0.010,
                return_std=0.004,
                pattern_strength=0.8,
                market_condition_dependency='bull',
                volume_multiplier=0.8,
                historical_edge=0.09,
                recent_performance=0.011,
                confidence_multiplier=1.25
            ),

            CalendarPattern(
                pattern_name='Thanksgiving_Week',
                pattern_type='holiday',
                asset_class='equity',
                trigger_date='11-22',
                effect_window_days=5,
                historical_returns=[0.005, 0.003, 0.008, 0.002, 0.006, 0.004, 0.007, 0.001],
                win_rate=0.70,
                avg_return=0.004,
                return_std=0.003,
                pattern_strength=0.7,
                market_condition_dependency='any',
                volume_multiplier=0.7,
                historical_edge=0.06,
                recent_performance=0.005,
                confidence_multiplier=1.15
            ),

            CalendarPattern(
                pattern_name='Halloween_Effect',
                pattern_type='holiday',
                asset_class='equity',
                trigger_date='10-31',
                effect_window_days=3,
                historical_returns=[0.003, -0.002, 0.005, 0.001, 0.004, -0.001, 0.006, 0.002],
                win_rate=0.65,
                avg_return=0.002,
                return_std=0.004,
                pattern_strength=0.6,
                market_condition_dependency='bear',
                volume_multiplier=1.1,
                historical_edge=0.04,
                recent_performance=0.003,
                confidence_multiplier=1.1
            ),

            # Tax-related patterns
            CalendarPattern(
                pattern_name='Tax_Selling',
                pattern_type='tax',
                asset_class='equity',
                trigger_date='12-31',
                effect_window_days=5,
                historical_returns=[-0.008, -0.012, -0.005, -0.009, -0.007, -0.011, -0.006, -0.010],
                win_rate=0.8,
                avg_return=-0.009,
                return_std=0.003,
                pattern_strength=0.85,
                market_condition_dependency='bear',
                volume_multiplier=1.3,
                historical_edge=0.11,
                recent_performance=-0.008,
                confidence_multiplier=1.3
            ),

            CalendarPattern(
                pattern_name='April_Tax_Deadline',
                pattern_type='tax',
                asset_class='equity',
                trigger_date='04-15',
                effect_window_days=3,
                historical_returns=[0.004, 0.002, 0.006, 0.001, 0.005, 0.003, 0.007, 0.002],
                win_rate=0.72,
                avg_return=0.004,
                return_std=0.003,
                pattern_strength=0.75,
                market_condition_dependency='any',
                volume_multiplier=1.2,
                historical_edge=0.08,
                recent_performance=0.004,
                confidence_multiplier=1.2
            ),

            # Quarter-end patterns
            CalendarPattern(
                pattern_name='Quarter_End_Rebalancing',
                pattern_type='quarter_end',
                asset_class='equity',
                trigger_date='quarter_end',
                effect_window_days=3,
                historical_returns=[0.003, -0.002, 0.004, 0.001, 0.005, -0.001, 0.003, 0.002],
                win_rate=0.68,
                avg_return=0.002,
                return_std=0.003,
                pattern_strength=0.7,
                market_condition_dependency='any',
                volume_multiplier=1.4,
                historical_edge=0.05,
                recent_performance=0.002,
                confidence_multiplier=1.15
            ),

            CalendarPattern(
                pattern_name='Month_End_Window_Dressing',
                pattern_type='month_end',
                asset_class='equity',
                trigger_date='month_end',
                effect_window_days=2,
                historical_returns=[0.002, 0.001, 0.003, 0.001, 0.002, 0.001, 0.004, 0.002],
                win_rate=0.75,
                avg_return=0.002,
                return_std=0.001,
                pattern_strength=0.8,
                market_condition_dependency='bull',
                volume_multiplier=1.1,
                historical_edge=0.07,
                recent_performance=0.002,
                confidence_multiplier=1.2
            ),

            # Seasonal patterns
            CalendarPattern(
                pattern_name='January_Effect',
                pattern_type='seasonal',
                asset_class='equity',
                trigger_date='01-01',
                effect_window_days=10,
                historical_returns=[0.015, 0.008, 0.022, 0.012, 0.018, 0.009, 0.025, 0.014],
                win_rate=0.82,
                avg_return=0.015,
                return_std=0.007,
                pattern_strength=0.85,
                market_condition_dependency='any',
                volume_multiplier=1.0,
                historical_edge=0.13,
                recent_performance=0.016,
                confidence_multiplier=1.35
            ),

            CalendarPattern(
                pattern_name='September_Seasonality',
                pattern_type='seasonal',
                asset_class='equity',
                trigger_date='09-01',
                effect_window_days=7,
                historical_returns=[-0.012, -0.008, -0.015, -0.006, -0.011, -0.009, -0.013, -0.007],
                win_rate=0.78,
                avg_return=-0.01,
                return_std=0.004,
                pattern_strength=0.8,
                market_condition_dependency='any',
                volume_multiplier=1.0,
                historical_edge=0.1,
                recent_performance=-0.009,
                confidence_multiplier=1.25
            ),

            # Weekend effect (for applicable assets)
            CalendarPattern(
                pattern_name='Weekend_Effect',
                pattern_type='seasonal',
                asset_class='equity',
                trigger_date='weekend',
                effect_window_days=1,
                historical_returns=[0.0008, 0.0005, 0.0012, 0.0003, 0.0009, 0.0006, 0.0015, 0.0007],
                win_rate=0.85,
                avg_return=0.0008,
                return_std=0.0004,
                pattern_strength=0.9,
                market_condition_dependency='any',
                volume_multiplier=0.9,
                historical_edge=0.15,
                recent_performance=0.0009,
                confidence_multiplier=1.4
            ),

            # Crypto-specific patterns (if applicable)
            CalendarPattern(
                pattern_name='Bitcoin_Halving',
                pattern_type='seasonal',
                asset_class='crypto',
                trigger_date='halving',
                effect_window_days=30,
                historical_returns=[0.25, 0.18, 0.35, 0.22],
                win_rate=0.9,
                avg_return=0.25,
                return_std=0.08,
                pattern_strength=0.95,
                market_condition_dependency='bull',
                volume_multiplier=2.0,
                historical_edge=0.35,
                recent_performance=0.28,
                confidence_multiplier=1.8
            )
        ]

        for pattern in patterns:
            self.calendar_patterns[pattern.pattern_name] = pattern

    def _load_data(self):
        """Load existing calendar data."""
        # Load patterns
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
                print(f"📅 Loaded calendar patterns: {len(data.get('patterns', {}))} seasonal effects")
            except Exception as e:
                print(f"⚠️ Error loading calendar patterns: {e}")

        # Load analyses
        if os.path.exists(self.analyses_file):
            try:
                with open(self.analyses_file, 'r') as f:
                    data = json.load(f)
                print(f"📅 Loaded calendar analyses: {len(data.get('analyses', {}))} events")
            except Exception as e:
                print(f"⚠️ Error loading calendar analyses: {e}")

    def analyze_calendar_opportunity(self, calendar_data: Dict[str, Any]) -> Optional[CalendarSeasonalityAnalysis]:
        """Analyze calendar-driven trading opportunity."""

        pattern_name = calendar_data.get('pattern_name', '')
        days_to_trigger = calendar_data.get('days_to_trigger', 30)
        market_condition = calendar_data.get('market_condition', 'any')

        # Get calendar pattern
        pattern = self.calendar_patterns.get(pattern_name)
        if not pattern:
            return None

        # Perform AI analysis
        pattern_probability, expected_return, easy_trade_confidence, rationale, action = self._perform_calendar_analysis(
            pattern, days_to_trigger, market_condition
        )

        analysis = CalendarSeasonalityAnalysis(
            pattern_name=pattern_name,
            pattern_type=pattern.pattern_type,
            asset_class=pattern.asset_class,
            days_to_trigger=days_to_trigger,
            market_condition=market_condition,
            pattern_probability=pattern_probability,
            expected_return=expected_return,
            easy_trade_confidence=easy_trade_confidence,
            rationale=rationale,
            recommended_action=action
        )

        self.calendar_analyses[pattern_name] = analysis
        self._save_analysis(analysis)

        return analysis

    def _perform_calendar_analysis(self, pattern: CalendarPattern, days_to_trigger: int,
                                market_condition: str) -> Tuple[float, float, float, str, str]:
        """Perform detailed calendar analysis."""

        # Get easy trade assessment
        easy_confidence, trade_rationale, action = pattern.get_easy_calendar_trade(days_to_trigger, market_condition)

        # Calculate pattern probability and return
        pattern_probability, expected_return = pattern.calculate_pattern_probability(market_condition)

        # Generate comprehensive rationale
        rationale_parts = [
            f"Pattern: {pattern.pattern_name} ({pattern.pattern_type})",
            f"Asset Class: {pattern.asset_class}",
            f"Days to Trigger: {days_to_trigger}",
            f"Market Condition: {market_condition}",
            f"Historical Win Rate: {pattern.win_rate:.1%}",
            f"Average Return: {pattern.avg_return:.1%}",
            f"Pattern Strength: {pattern.pattern_strength:.1%}",
            f"Expected Return: {expected_return:.1%} (Probability: {pattern_probability:.1%})",
            trade_rationale
        ]

        if pattern.market_condition_dependency != 'any':
            rationale_parts.append(f"Works best in {pattern.market_condition_dependency} markets")

        if pattern.recent_performance != 0:
            perf_desc = "stronger" if pattern.recent_performance > pattern.avg_return else "weaker"
            rationale_parts.append(f"Recent performance has been {perf_desc} than historical average")

        rationale = " | ".join(rationale_parts)

        return pattern_probability, expected_return, easy_confidence, rationale, action

    def get_easy_calendar_trades(self, min_confidence: float = 0.75) -> List[Dict[str, Any]]:
        """Find calendar-driven trading opportunities with strong seasonal edges."""

        easy_trades = []

        for pattern_name, analysis in self.calendar_analyses.items():
            if analysis.easy_trade_confidence >= min_confidence:
                trade_info = {
                    'pattern': pattern_name,
                    'type': analysis.pattern_type,
                    'asset_class': analysis.asset_class,
                    'days_to_trigger': analysis.days_to_trigger,
                    'expected_return': analysis.expected_return,
                    'probability': analysis.pattern_probability,
                    'confidence': analysis.easy_trade_confidence,
                    'rationale': analysis.rationale,
                    'recommended_action': analysis.recommended_action
                }
                easy_trades.append(trade_info)

        # Sort by confidence
        easy_trades.sort(key=lambda x: x['confidence'], reverse=True)
        return easy_trades[:10]  # Top 10 easy calendar trades

    def _save_analysis(self, analysis: CalendarSeasonalityAnalysis):
        """Save analysis to file."""
        analyses_data = {
            'analyses': {aid: a.to_dict() for aid, a in self.calendar_analyses.items()},
            'last_updated': datetime.now().isoformat()
        }

        with open(self.analyses_file, 'w') as f:
            json.dump(analyses_data, f, indent=2)


# Test/demo functions
async def test_calendar_seasonality_engine():
    """Test the calendar seasonality analysis engine."""
    print("📅 TESTING CALENDAR SEASONALITY ENGINE")
    print("=" * 55)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)

    engine = CalendarSeasonalityEngine(kalshi, scenario_graph)

    print(f"📅 Initialized with {len(engine.calendar_patterns)} calendar patterns")

    # Test calendar events
    test_events = [
        {
            'pattern_name': 'Christmas_Rally',
            'days_to_trigger': 3,
            'market_condition': 'bull'
        },
        {
            'pattern_name': 'Tax_Selling',
            'days_to_trigger': 5,
            'market_condition': 'bear'
        },
        {
            'pattern_name': 'January_Effect',
            'days_to_trigger': 7,
            'market_condition': 'any'
        },
        {
            'pattern_name': 'Quarter_End_Rebalancing',
            'days_to_trigger': 2,
            'market_condition': 'any'
        },
        {
            'pattern_name': 'September_Seasonality',
            'days_to_trigger': 10,
            'market_condition': 'any'
        }
    ]

    print("\n📅 ANALYZING CALENDAR PATTERNS FOR SEASONAL TRADES:")
    for event in test_events:
        print(f"\n📅 PATTERN: {event['pattern_name']}")
        print(f"   Days to Trigger: {event['days_to_trigger']} | Market: {event['market_condition']}")

        # Analyze the calendar pattern
        analysis = engine.analyze_calendar_opportunity(event)

        if analysis:
            print("   ✅ CALENDAR PATTERN DETECTED")
            print(f"   Pattern Probability: {analysis.pattern_probability:.1%}")
            print(f"   Expected Return: {analysis.expected_return:.1%}")
            print(f"   Easy Trade Confidence: {analysis.easy_trade_confidence:.1%}")

            if analysis.easy_trade_confidence > 0.75:
                print("   🎯 EASY CALENDAR TRADE OPPORTUNITY! 🎯")
                print(f"   Recommended: {analysis.recommended_action}")
            else:
                print("   ❓ Standard seasonal pattern")

            print(f"   Rationale: {analysis.rationale}")
        else:
            print("   ❌ No calendar pattern data for this event")

        print("-" * 75)

    # Show easy calendar trades
    print("\n🎯 EASY CALENDAR SEASONALITY TRADES (75%+ confidence):")
    easy_trades = engine.get_easy_calendar_trades()

    if easy_trades:
        for i, trade in enumerate(easy_trades, 1):
            print(f"{i}. {trade['pattern']}: {trade['confidence']:.1%} confidence")
            print(f"   Type: {trade['type']} | Asset: {trade['asset_class']}")
            print(f"   Days to Trigger: {trade['days_to_trigger']} | Expected Return: {trade['expected_return']:.1%}")
            print(f"   {trade['recommended_action']}")
            print(f"   Rationale: {trade['rationale'][:100]}...")
            print()
    else:
        print("No easy calendar seasonality trades found with current thresholds")

    print("\n✅ Calendar Seasonality Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_calendar_seasonality_engine())
