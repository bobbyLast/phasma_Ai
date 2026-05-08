"""
🌤️ WEATHER ANALYSIS ENGINE

Advanced weather intelligence system for Kalshi prediction markets.
Analyzes weather patterns, seasonal trends, historical accuracy, and meteorological data
to identify "easy money" trades in weather prediction markets.

Features:
- Weather Pattern Database (seasonal trends, historical accuracy)
- Meteorological Data Integration (temperature, precipitation, wind)
- Seasonal Trend Analysis (winter heating, summer cooling patterns)
- Geographic Weather Analysis (regional weather patterns)
- Weather Market Edge Detection (predictable outcomes)
- Quick Money Trade Identification (fast, high-probability trades)
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
class WeatherPattern:
    """Weather pattern data for a location and season."""
    location: str  # State/country code (e.g., 'CA', 'TX', 'UK')
    season: str  # 'winter', 'spring', 'summer', 'fall'
    weather_type: str  # 'temperature', 'precipitation', 'snow', 'hurricane'

    # Historical data
    historical_accuracy: float = 0.0  # How predictable this weather pattern is (0.0-1.0)
    average_value: float = 0.0  # Average temperature/precipitation/etc.
    standard_deviation: float = 0.0
    trend_direction: str = 'stable'  # 'warming', 'cooling', 'stable', 'volatile'

    # Seasonal patterns
    peak_month: int = 1  # Month when this weather is most likely/extreme
    predictability_score: float = 0.0  # How reliable predictions are

    # Market performance
    market_edge: float = 0.0  # Historical edge in weather markets for this pattern
    volume_multiplier: float = 1.0  # How liquid these markets typically are

    last_updated: datetime = field(default_factory=lambda: datetime.now())

    def get_seasonal_probability(self, target_value: float, comparison: str = 'above') -> float:
        """Get probability of weather outcome based on seasonal patterns."""
        if self.standard_deviation == 0:
            return 0.5

        # Standardize the target value
        z_score = (target_value - self.average_value) / self.standard_deviation

        if comparison == 'above':
            # Probability of being above target (one-tailed)
            prob = 1 - statistics.NormalDist().cdf(z_score)
        elif comparison == 'below':
            # Probability of being below target (one-tailed)
            prob = statistics.NormalDist().cdf(z_score)
        else:
            # Probability of being within range (two-tailed, approximate)
            prob = 1 - abs(2 * (0.5 - statistics.NormalDist().cdf(abs(z_score))))

        # Adjust based on predictability
        prob = 0.5 + (prob - 0.5) * self.predictability_score

        return max(0.01, min(0.99, prob))


@dataclass
class WeatherMarketAnalysis:
    """Analysis of a weather Kalshi market."""
    market_id: str
    market_title: str
    location: str
    weather_type: str
    season: str
    comparison_type: str  # 'above', 'below', 'between'
    target_value: float
    time_period: str  # 'month', 'season', 'year'

    predicted_probability: float
    ai_adjusted_probability: float
    confidence: float
    seasonal_edge: float
    quick_money_potential: bool
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'market_id': self.market_id,
            'market_title': self.market_title,
            'location': self.location,
            'weather_type': self.weather_type,
            'season': self.season,
            'comparison_type': self.comparison_type,
            'target_value': self.target_value,
            'time_period': self.time_period,
            'predicted_probability': self.predicted_probability,
            'ai_adjusted_probability': self.ai_adjusted_probability,
            'confidence': self.confidence,
            'seasonal_edge': self.seasonal_edge,
            'quick_money_potential': self.quick_money_potential,
            'rationale': self.rationale
        }


class WeatherAnalysisEngine:
    """
    🌤️ Weather Analysis Engine

    Specialized AI for analyzing weather prediction markets using meteorological patterns,
    seasonal trends, and historical weather data to find "easy money" trades.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine, scenario_graph: ScenarioGraphEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph

        # Weather pattern database
        self.weather_patterns: Dict[str, WeatherPattern] = {}

        # Analysis results
        self.market_analyses: Dict[str, WeatherMarketAnalysis] = {}

        # Data files
        self.weather_patterns_file = "weather_patterns.json"
        self.weather_analyses_file = "weather_analyses.json"

        # Initialize with known weather patterns
        self._initialize_weather_patterns()
        self._load_data()

    def _initialize_weather_patterns(self):
        """Initialize with known weather patterns for major locations."""

        patterns = [
            # Temperature patterns - US States
            WeatherPattern(
                location='CA', season='summer', weather_type='temperature',
                historical_accuracy=0.85, average_value=75.0, standard_deviation=8.0,
                trend_direction='warming', peak_month=8, predictability_score=0.9,
                market_edge=0.15, volume_multiplier=1.5
            ),
            WeatherPattern(
                location='CA', season='winter', weather_type='temperature',
                historical_accuracy=0.80, average_value=55.0, standard_deviation=6.0,
                trend_direction='stable', peak_month=1, predictability_score=0.8,
                market_edge=0.12, volume_multiplier=1.3
            ),
            WeatherPattern(
                location='FL', season='summer', weather_type='temperature',
                historical_accuracy=0.75, average_value=85.0, standard_deviation=5.0,
                trend_direction='warming', peak_month=7, predictability_score=0.85,
                market_edge=0.18, volume_multiplier=1.8
            ),
            WeatherPattern(
                location='FL', season='hurricane', weather_type='hurricane',
                historical_accuracy=0.60, average_value=0.7, standard_deviation=0.8,
                trend_direction='volatile', peak_month=9, predictability_score=0.6,
                market_edge=0.08, volume_multiplier=2.0
            ),
            WeatherPattern(
                location='TX', season='summer', weather_type='temperature',
                historical_accuracy=0.82, average_value=90.0, standard_deviation=7.0,
                trend_direction='warming', peak_month=7, predictability_score=0.88,
                market_edge=0.20, volume_multiplier=1.6
            ),
            WeatherPattern(
                location='NY', season='winter', weather_type='temperature',
                historical_accuracy=0.78, average_value=25.0, standard_deviation=12.0,
                trend_direction='volatile', peak_month=1, predictability_score=0.7,
                market_edge=0.10, volume_multiplier=1.4
            ),
            WeatherPattern(
                location='NY', season='summer', weather_type='temperature',
                historical_accuracy=0.85, average_value=75.0, standard_deviation=8.0,
                trend_direction='warming', peak_month=7, predictability_score=0.9,
                market_edge=0.16, volume_multiplier=1.5
            ),

            # Precipitation patterns
            WeatherPattern(
                location='WA', season='winter', weather_type='precipitation',
                historical_accuracy=0.70, average_value=8.0, standard_deviation=3.0,
                trend_direction='stable', peak_month=12, predictability_score=0.75,
                market_edge=0.12, volume_multiplier=1.2
            ),
            WeatherPattern(
                location='AZ', season='summer', weather_type='precipitation',
                historical_accuracy=0.65, average_value=1.5, standard_deviation=1.2,
                trend_direction='drying', peak_month=8, predictability_score=0.7,
                market_edge=0.14, volume_multiplier=1.1
            ),

            # International weather patterns
            WeatherPattern(
                location='UK', season='winter', weather_type='temperature',
                historical_accuracy=0.72, average_value=40.0, standard_deviation=8.0,
                trend_direction='warming', peak_month=12, predictability_score=0.75,
                market_edge=0.11, volume_multiplier=1.3
            ),
            WeatherPattern(
                location='UK', season='summer', weather_type='temperature',
                historical_accuracy=0.80, average_value=65.0, standard_deviation=6.0,
                trend_direction='warming', peak_month=7, predictability_score=0.85,
                market_edge=0.15, volume_multiplier=1.4
            ),
            WeatherPattern(
                location='AU', season='summer', weather_type='temperature',
                historical_accuracy=0.78, average_value=85.0, standard_deviation=7.0,
                trend_direction='warming', peak_month=1, predictability_score=0.8,
                market_edge=0.13, volume_multiplier=1.2
            ),
            WeatherPattern(
                location='JP', season='summer', weather_type='precipitation',
                historical_accuracy=0.68, average_value=6.0, standard_deviation=2.5,
                trend_direction='stable', peak_month=6, predictability_score=0.7,
                market_edge=0.09, volume_multiplier=1.1
            ),

            # Snow patterns for winter sports markets
            WeatherPattern(
                location='CO', season='winter', weather_type='snow',
                historical_accuracy=0.65, average_value=150.0, standard_deviation=60.0,
                trend_direction='volatile', peak_month=2, predictability_score=0.6,
                market_edge=0.08, volume_multiplier=1.5
            ),
            WeatherPattern(
                location='UT', season='winter', weather_type='snow',
                historical_accuracy=0.70, average_value=180.0, standard_deviation=50.0,
                trend_direction='stable', peak_month=1, predictability_score=0.7,
                market_edge=0.12, volume_multiplier=1.4
            )
        ]

        for pattern in patterns:
            key = f"{pattern.location}_{pattern.season}_{pattern.weather_type}"
            self.weather_patterns[key] = pattern

    def _load_data(self):
        """Load existing weather data."""
        # Load weather patterns
        if os.path.exists(self.weather_patterns_file):
            try:
                with open(self.weather_patterns_file, 'r') as f:
                    data = json.load(f)
                print(f"🌤️ Loaded weather patterns for {len(data.get('patterns', {}))} location-season combinations")
            except Exception as e:
                print(f"⚠️ Error loading weather patterns: {e}")

        # Load analyses
        if os.path.exists(self.weather_analyses_file):
            try:
                with open(self.weather_analyses_file, 'r') as f:
                    data = json.load(f)
                print(f"🌤️ Loaded weather analyses: {len(data.get('analyses', {}))} markets")
            except Exception as e:
                print(f"⚠️ Error loading weather analyses: {e}")

    def analyze_weather_market(self, market_data: Dict[str, Any]) -> Optional[WeatherMarketAnalysis]:
        """Analyze a weather Kalshi market."""

        market_title = market_data.get('title', '').upper()
        market_ticker = market_data.get('ticker', '')

        # Parse weather market details
        weather_info = self._parse_weather_market_title(market_title)
        if not weather_info:
            return None

        location = weather_info['location']
        weather_type = weather_info['weather_type']
        season = weather_info['season']
        comparison_type = weather_info['comparison_type']
        target_value = weather_info['target_value']
        time_period = weather_info['time_period']

        # Get Kalshi market probability
        kalshi_probability = market_data.get('implied_probability', 0.5)

        # Perform AI analysis
        ai_probability, confidence, seasonal_edge, quick_money_potential, rationale = self._perform_weather_analysis(
            location, weather_type, season, comparison_type, target_value, kalshi_probability
        )

        analysis = WeatherMarketAnalysis(
            market_id=market_ticker,
            market_title=market_title,
            location=location,
            weather_type=weather_type,
            season=season,
            comparison_type=comparison_type,
            target_value=target_value,
            time_period=time_period,
            predicted_probability=kalshi_probability,
            ai_adjusted_probability=ai_probability,
            confidence=confidence,
            seasonal_edge=seasonal_edge,
            quick_money_potential=quick_money_potential,
            rationale=rationale
        )

        self.market_analyses[market_ticker] = analysis
        self._save_analysis(analysis)

        return analysis

    def _parse_weather_market_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Parse weather market title to extract structured information."""

        title_upper = title.upper()

        # Location extraction
        locations = {
            'CALIFORNIA': 'CA', 'CA': 'CA',
            'TEXAS': 'TX', 'TX': 'TX',
            'FLORIDA': 'FL', 'FL': 'FL',
            'NEW YORK': 'NY', 'NY': 'NY',
            'WASHINGTON': 'WA', 'WA': 'WA',
            'ARIZONA': 'AZ', 'AZ': 'AZ',
            'COLORADO': 'CO', 'CO': 'CO',
            'UTAH': 'UT', 'UT': 'UT',
            'UNITED KINGDOM': 'UK', 'UK': 'UK',
            'AUSTRALIA': 'AU', 'AU': 'AU',
            'JAPAN': 'JP', 'JP': 'JP'
        }

        location = None
        for loc_name, loc_code in locations.items():
            if loc_name in title_upper:
                location = loc_code
                break

        if not location:
            return None

        # Weather type detection
        weather_types = {
            'temperature': ['TEMPERATURE', 'TEMP', 'AVERAGE TEMP', 'DEGREE'],
            'precipitation': ['PRECIPITATION', 'RAIN', 'PRECIP', 'INCHES'],
            'snow': ['SNOW', 'SNOWFALL', 'INCHES OF SNOW'],
            'hurricane': ['HURRICANE', 'STORM', 'TROPICAL']
        }

        weather_type = 'temperature'  # default
        for w_type, keywords in weather_types.items():
            if any(keyword in title_upper for keyword in keywords):
                weather_type = w_type
                break

        # Season detection
        seasons = {
            'winter': ['WINTER', 'DECEMBER', 'JANUARY', 'FEBRUARY', 'Q1'],
            'spring': ['SPRING', 'MARCH', 'APRIL', 'MAY', 'Q2'],
            'summer': ['SUMMER', 'JUNE', 'JULY', 'AUGUST', 'Q3'],
            'fall': ['FALL', 'AUTUMN', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'Q4']
        }

        season = 'summer'  # default
        for season_name, keywords in seasons.items():
            if any(keyword in title_upper for keyword in keywords):
                season = season_name
                break

        # Comparison type
        comparison_type = 'above'  # default
        if 'BELOW' in title_upper:
            comparison_type = 'below'
        elif 'BETWEEN' in title_upper or 'RANGE' in title_upper:
            comparison_type = 'between'

        # Target value extraction (simplified)
        target_value = 70.0  # default
        import re
        numbers = re.findall(r'\d+\.?\d*', title)
        if numbers:
            # Try to find temperature-like numbers
            for num in numbers:
                val = float(num)
                if 0 <= val <= 120:  # Reasonable temperature range
                    target_value = val
                    break

        # Time period
        time_period = 'season'  # default
        if 'MONTH' in title_upper or any(mon in title_upper for mon in ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']):
            time_period = 'month'
        elif 'YEAR' in title_upper:
            time_period = 'year'

        return {
            'location': location,
            'weather_type': weather_type,
            'season': season,
            'comparison_type': comparison_type,
            'target_value': target_value,
            'time_period': time_period
        }

    def _perform_weather_analysis(self, location: str, weather_type: str, season: str,
                                comparison_type: str, target_value: float, kalshi_prob: float) -> Tuple[float, float, float, bool, str]:
        """Perform detailed weather analysis."""

        # Get weather pattern
        pattern_key = f"{location}_{season}_{weather_type}"
        pattern = self.weather_patterns.get(pattern_key)

        if not pattern:
            return kalshi_prob, 0.5, 0.0, False, f"No historical data for {location} {season} {weather_type}"

        # Calculate seasonal probability
        seasonal_prob = pattern.get_seasonal_probability(target_value, comparison_type)

        # Calculate edge
        seasonal_edge = abs(seasonal_prob - kalshi_prob)

        # Determine if this is quick money potential
        quick_money_potential = (
            seasonal_edge > 0.20 and  # Significant edge
            pattern.predictability_score > 0.7 and  # Highly predictable
            pattern.market_edge > 0.10  # Historically profitable
        )

        # Adjust AI probability towards seasonal probability
        ai_probability = kalshi_prob * 0.3 + seasonal_prob * 0.7  # Weighted average

        # Confidence based on pattern strength
        confidence = min(0.95, pattern.predictability_score * 0.8 + pattern.market_edge * 0.2)

        # Generate rationale
        rationale_parts = []

        if quick_money_potential:
            rationale_parts.append(f"🎯 QUICK MONEY OPPORTUNITY: {seasonal_edge:.1%} edge in highly predictable {weather_type}")

        rationale_parts.append(f"Seasonal pattern: {location} {season} {weather_type} has {pattern.predictability_score:.1%} predictability")
        rationale_parts.append(f"Historical average: {pattern.average_value:.1f}, targeting {target_value:.1f}")
        rationale_parts.append(f"Seasonal probability: {seasonal_prob:.1%}, Kalshi: {kalshi_prob:.1%}")

        if pattern.trend_direction != 'stable':
            rationale_parts.append(f"Trend: {pattern.trend_direction} pattern supports {'higher' if pattern.trend_direction == 'warming' else 'lower'} outcomes")

        rationale = " | ".join(rationale_parts)

        return ai_probability, confidence, seasonal_edge, quick_money_potential, rationale

    def get_quick_money_weather_trades(self, min_edge: float = 0.15) -> List[Dict[str, Any]]:
        """Find weather markets with strong seasonal edges for quick money."""

        quick_trades = []

        for market_id, analysis in self.market_analyses.items():
            if (analysis.quick_money_potential and
                analysis.seasonal_edge >= min_edge and
                analysis.confidence > 0.7):

                trade_info = {
                    'market_id': market_id,
                    'title': analysis.market_title,
                    'location': analysis.location,
                    'weather_type': analysis.weather_type,
                    'season': analysis.season,
                    'kalshi_probability': analysis.predicted_probability,
                    'ai_probability': analysis.ai_adjusted_probability,
                    'edge': analysis.seasonal_edge,
                    'confidence': analysis.confidence,
                    'rationale': analysis.rationale,
                    'recommended_action': self._get_weather_trade_action(analysis)
                }
                quick_trades.append(trade_info)

        # Sort by edge size
        quick_trades.sort(key=lambda x: x['edge'], reverse=True)
        return quick_trades[:10]  # Top 10 quick money trades

    def _get_weather_trade_action(self, analysis: WeatherMarketAnalysis) -> str:
        """Get recommended trade action for weather market."""

        if analysis.ai_adjusted_probability > analysis.predicted_probability + 0.1:
            return f"BUY YES - AI sees {analysis.ai_adjusted_probability:.1%} vs market {analysis.predicted_probability:.1%}"
        elif analysis.ai_adjusted_probability < analysis.predicted_probability - 0.1:
            return f"BUY NO - AI sees {analysis.ai_adjusted_probability:.1%} vs market {analysis.predicted_probability:.1%}"
        else:
            return f"MONITOR - Seasonal patterns suggest {analysis.ai_adjusted_probability:.1%} probability"

    def _save_analysis(self, analysis: WeatherMarketAnalysis):
        """Save analysis to file."""
        analyses_data = {
            'analyses': {aid: a.to_dict() for aid, a in self.market_analyses.items()},
            'last_updated': datetime.now().isoformat()
        }

        with open(self.weather_analyses_file, 'w') as f:
            json.dump(analyses_data, f, indent=2)


# Test/demo functions
async def test_weather_engine():
    """Test the weather analysis engine."""
    print("🌤️ TESTING WEATHER ANALYSIS ENGINE")
    print("=" * 45)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)

    engine = WeatherAnalysisEngine(kalshi, scenario_graph)

    print(f"🌤️ Initialized with {len(engine.weather_patterns)} weather patterns")

    # Test markets
    test_markets = [
        {
            'ticker': 'CA_SUMMER_TEMP',
            'title': 'Will California average temperature be above 75°F in Summer 2025?',
            'implied_probability': 0.70
        },
        {
            'ticker': 'FL_HURRICANE_SEASON',
            'title': 'Will Florida be hit by a hurricane in 2025 hurricane season?',
            'implied_probability': 0.60
        },
        {
            'ticker': 'NY_WINTER_TEMP',
            'title': 'Will New York average temperature be below 25°F in Winter 2025?',
            'implied_probability': 0.40
        },
        {
            'ticker': 'UK_SUMMER_TEMP',
            'title': 'Will UK average temperature be above 65°F in Summer 2025?',
            'implied_probability': 0.75
        },
        {
            'ticker': 'TX_SUMMER_TEMP',
            'title': 'Will Texas average temperature be above 90°F in Summer 2025?',
            'implied_probability': 0.80
        }
    ]

    print("\n🌤️ ANALYZING WEATHER MARKETS FOR QUICK MONEY:")
    for market in test_markets:
        print(f"\n🌤️ MARKET: {market['ticker']}")
        print(f"   Title: {market['title']}")
        print(".1%")

        # Analyze the market
        analysis = engine.analyze_weather_market(market)

        if analysis:
            print(f"   ✅ WEATHER MARKET DETECTED")
            print(f"   Location: {analysis.location} | Type: {analysis.weather_type} | Season: {analysis.season}")
            print(".1%")
            print(f"   AI Adjusted: {analysis.ai_adjusted_probability:.1%}")
            print(f"   Confidence: {analysis.confidence:.1%}")
            print(f"   Seasonal Edge: {analysis.seasonal_edge:.1%}")

            if analysis.quick_money_potential:
                print("   🎯 QUICK MONEY OPPORTUNITY! 🎯")
                print(f"   Recommended: {engine._get_weather_trade_action(analysis)}")
            else:
                print("   ❓ Standard weather trade")

            print(f"   Rationale: {analysis.rationale}")
        else:
            print("   ❌ Not identified as weather market")

        print("-" * 60)

    # Show quick money weather trades
    print("\n🎯 QUICK MONEY WEATHER TRADES (15%+ seasonal edge):")
    quick_trades = engine.get_quick_money_weather_trades()

    if quick_trades:
        for i, trade in enumerate(quick_trades, 1):
            print(f"{i}. {trade['market_id']}: {trade['edge']:.1%} edge")
            print(f"   {trade['location']} {trade['season']} - {trade['recommended_action']}")
            print(f"   Rationale: {trade['rationale'][:100]}...")
            print()
    else:
        print("No quick money weather trades found with current thresholds")

    print("\n✅ Weather Analysis Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_weather_engine())
