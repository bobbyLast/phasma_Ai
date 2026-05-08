"""
🏈 SPORTS ANALYSIS ENGINE

Advanced sports intelligence system for identifying "easy trades" in sports prediction markets.
Analyzes player statistics, team performance, injuries, and historical outcomes to find
systematic edges in sports betting and prediction markets.

Features:
- Player Stats Database (yards, points, rebounds, win probability)
- Team Performance Analysis (recent form, head-to-head records)
- Injury Impact Assessment (player availability and performance impact)
- Sports Market Edge Detection (systematic mispricings)
- Prop Bet Optimization (player-specific performance predictions)
- High-Confidence Sports Trade Identification (data-driven edges)
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
class PlayerProfile:
    """Player performance profile and statistics."""
    player_name: str
    sport: str  # 'NFL', 'NBA', 'MLB', 'Soccer', etc.
    position: str  # 'QB', 'RB', 'WR', 'PG', 'Pitcher', etc.
    team: str

    # Performance stats (rolling averages)
    recent_performance: List[float] = field(default_factory=list)  # last 5 games
    season_performance: List[float] = field(default_factory=list)  # season stats
    career_performance: List[float] = field(default_factory=list)  # career stats

    # Statistical metrics
    avg_performance: float = 0.0
    performance_std: float = 0.0
    trend_direction: str = 'stable'  # 'improving', 'declining', 'stable'
    consistency_score: float = 0.0  # how consistent performance is

    # Injury and availability
    injury_status: str = 'healthy'  # 'healthy', 'questionable', 'doubtful', 'out'
    injury_impact: float = 0.0  # performance impact of injury (0-1, 1=full impact)
    games_missed: int = 0

    # Matchup factors
    home_advantage: float = 0.0
    opponent_strength: float = 0.0
    weather_impact: float = 0.0  # for outdoor sports

    # Market edge
    historical_edge: float = 0.0  # how often line is wrong on this player
    public_bias: float = 0.0  # how much public money affects line
    confidence_multiplier: float = 1.0

    last_updated: datetime = field(default_factory=lambda: datetime.now())

    def predict_performance(self, target_value: float, prop_type: str, matchup_factors: Dict[str, float]) -> Tuple[float, float]:
        """Predict player performance for a given prop."""

        if not self.recent_performance:
            return 0.5, 0.5

        # Base prediction from recent form
        recent_avg = statistics.mean(self.recent_performance[-3:])  # last 3 games
        base_probability = statistics.NormalDist(recent_avg, self.performance_std).cdf(target_value)

        # Adjust for consistency
        base_probability = 0.5 + (base_probability - 0.5) * self.consistency_score

        # Adjust for matchup factors
        matchup_adjustment = (
            matchup_factors.get('home_advantage', 0) * self.home_advantage +
            matchup_factors.get('opponent_strength', 0) * self.opponent_strength +
            matchup_factors.get('weather', 0) * self.weather_impact
        )

        adjusted_probability = base_probability + matchup_adjustment
        adjusted_probability = max(0.05, min(0.95, adjusted_probability))

        # Adjust for injury
        if self.injury_status != 'healthy':
            injury_penalty = self.injury_impact * 0.3  # up to 30% performance reduction
            adjusted_probability = adjusted_probability * (1 - injury_penalty)

        # Confidence based on data quality and recency
        confidence = min(0.9, len(self.recent_performance) / 10.0)  # more data = more confidence
        if self.injury_status != 'healthy':
            confidence *= 0.7  # lower confidence with injuries

        return adjusted_probability, confidence

    def get_easy_sports_trade(self, target_value: float, market_prob: float, prop_type: str,
                            matchup_factors: Dict[str, float]) -> Tuple[float, str, str]:
        """Get easy sports trade recommendation."""

        if len(self.recent_performance) < 3:
            return 0.5, "Insufficient performance data", "MONITOR"

        ai_prob, confidence = self.predict_performance(target_value, prop_type, matchup_factors)

        edge = abs(ai_prob - market_prob)

        # Easy trade conditions
        if edge > 0.25 and confidence > 0.7:  # >25% edge, high confidence
            if ai_prob > market_prob + 0.15:
                return confidence, f"Strong edge: AI sees {ai_prob:.1%} vs market {market_prob:.1%} ({edge:.1%} edge)", f"BUY {prop_type.upper()} OVER"
            elif ai_prob < market_prob - 0.15:
                return confidence, f"Strong edge: AI sees {ai_prob:.1%} vs market {market_prob:.1%} ({edge:.1%} edge)", f"BUY {prop_type.upper()} UNDER"
        elif self.consistency_score > 0.8 and edge > 0.15:
            direction = "OVER" if ai_prob > market_prob else "UNDER"
            return 0.8, f"Highly consistent player with {edge:.1%} edge vs market", f"TRADE {prop_type.upper()} {direction}"

        return 0.5, "No clear edge in current matchup", "MONITOR"


@dataclass
class TeamProfile:
    """Team performance profile."""
    team_name: str
    sport: str
    league: str

    # Performance metrics
    recent_form: List[str] = field(default_factory=list)  # 'W', 'L', 'T' for last 10 games
    season_record: str = '0-0'  # wins-losses
    home_record: str = '0-0'
    away_record: str = '0-0'

    # Statistical ratings
    offensive_rating: float = 0.0
    defensive_rating: float = 0.0
    overall_rating: float = 0.0

    # Key factors
    injuries: List[str] = field(default_factory=list)  # injured players
    home_advantage: float = 0.0
    rest_advantage: float = 0.0  # back-to-back games, etc.

    last_updated: datetime = field(default_factory=lambda: datetime.now())


@dataclass
class SportsAnalysis:
    """Analysis of sports market opportunity."""
    market_type: str  # 'player_prop', 'game_outcome', 'spread'
    sport: str
    player_or_team: str
    prop_type: str  # 'points', 'yards', 'rebounds', 'over/under', etc.
    target_value: float
    market_probability: float
    ai_probability: float
    edge: float
    easy_trade_confidence: float
    rationale: str
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'market_type': self.market_type,
            'sport': self.sport,
            'player_or_team': self.player_or_team,
            'prop_type': self.prop_type,
            'target_value': self.target_value,
            'market_probability': self.market_probability,
            'ai_probability': self.ai_probability,
            'edge': self.edge,
            'easy_trade_confidence': self.easy_trade_confidence,
            'rationale': self.rationale,
            'recommended_action': self.recommended_action
        }


class SportsAnalysisEngine:
    """
    🏈 Sports Analysis Engine

    Specialized AI for analyzing sports prediction markets and finding "easy trades"
    based on player statistics, team performance, and matchup analysis.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine, scenario_graph: ScenarioGraphEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph

        # Player and team databases
        self.player_profiles: Dict[str, PlayerProfile] = {}
        self.team_profiles: Dict[str, TeamProfile] = {}

        # Analysis results
        self.sports_analyses: Dict[str, SportsAnalysis] = {}

        # Data files
        self.players_file = "sports_players.json"
        self.teams_file = "sports_teams.json"
        self.analyses_file = "sports_analyses.json"

        # Initialize with known players and teams
        self._initialize_sports_data()
        self._load_data()

    def _initialize_sports_data(self):
        """Initialize with known sports data."""

        # NFL Players
        nfl_players = [
            PlayerProfile(
                player_name='Patrick Mahomes',
                sport='NFL',
                position='QB',
                team='Chiefs',
                recent_performance=[320, 285, 340, 295, 310],
                season_performance=[285, 320, 295, 340, 310, 275, 330, 300],
                career_performance=[275, 285, 320, 295, 340, 310, 330, 300],
                avg_performance=305.0,
                performance_std=25.0,
                trend_direction='improving',
                consistency_score=0.85,
                injury_status='healthy',
                injury_impact=0.0,
                home_advantage=0.08,
                opponent_strength=-0.05,
                weather_impact=0.02,
                historical_edge=0.15,
                public_bias=0.10,
                confidence_multiplier=1.4
            ),

            PlayerProfile(
                player_name='Christian McCaffrey',
                sport='NFL',
                position='RB',
                team='49ers',
                recent_performance=[85, 120, 95, 110, 75],
                season_performance=[85, 120, 95, 110, 75, 135, 90, 105],
                career_performance=[75, 85, 120, 95, 110, 135, 90, 105],
                avg_performance=100.0,
                performance_std=20.0,
                trend_direction='stable',
                consistency_score=0.75,
                injury_status='healthy',
                home_advantage=0.06,
                opponent_strength=0.03,
                weather_impact=0.05,
                historical_edge=0.12,
                public_bias=0.08,
                confidence_multiplier=1.3
            ),

            PlayerProfile(
                player_name='Cooper Kupp',
                sport='NFL',
                position='WR',
                team='Rams',
                recent_performance=[110, 95, 125, 85, 115],
                season_performance=[110, 95, 125, 85, 115, 135, 90, 120],
                career_performance=[85, 110, 95, 125, 135, 90, 120, 115],
                avg_performance=110.0,
                performance_std=18.0,
                trend_direction='stable',
                consistency_score=0.80,
                injury_status='questionable',
                injury_impact=0.25,
                home_advantage=0.04,
                opponent_strength=0.02,
                weather_impact=0.03,
                historical_edge=0.10,
                public_bias=0.12,
                confidence_multiplier=1.25
            )
        ]

        # NBA Players
        nba_players = [
            PlayerProfile(
                player_name='LeBron James',
                sport='NBA',
                position='SF',
                team='Lakers',
                recent_performance=[28, 32, 25, 30, 27],
                season_performance=[28, 32, 25, 30, 27, 35, 22, 29],
                career_performance=[25, 28, 32, 30, 27, 35, 22, 29],
                avg_performance=28.5,
                performance_std=4.0,
                trend_direction='stable',
                consistency_score=0.90,
                injury_status='healthy',
                home_advantage=0.07,
                opponent_strength=0.01,
                weather_impact=0.0,
                historical_edge=0.08,
                public_bias=0.15,
                confidence_multiplier=1.2
            ),

            PlayerProfile(
                player_name='Stephen Curry',
                sport='NBA',
                position='PG',
                team='Warriors',
                recent_performance=[35, 28, 32, 38, 30],
                season_performance=[35, 28, 32, 38, 30, 42, 25, 33],
                career_performance=[28, 35, 32, 38, 30, 42, 25, 33],
                avg_performance=33.0,
                performance_std=6.0,
                trend_direction='improving',
                consistency_score=0.75,
                injury_status='healthy',
                home_advantage=0.05,
                opponent_strength=0.03,
                weather_impact=0.0,
                historical_edge=0.18,
                public_bias=0.20,
                confidence_multiplier=1.5
            ),

            PlayerProfile(
                player_name='Giannis Antetokounmpo',
                sport='NBA',
                position='PF',
                team='Bucks',
                recent_performance=[32, 35, 28, 30, 38],
                season_performance=[32, 35, 28, 30, 38, 25, 40, 33],
                career_performance=[28, 32, 35, 30, 38, 25, 40, 33],
                avg_performance=33.5,
                performance_std=5.5,
                trend_direction='stable',
                consistency_score=0.85,
                injury_status='healthy',
                home_advantage=0.08,
                opponent_strength=0.05,
                weather_impact=0.0,
                historical_edge=0.14,
                public_bias=0.18,
                confidence_multiplier=1.4
            )
        ]

        # MLB Players
        mlb_players = [
            PlayerProfile(
                player_name='Shohei Ohtani',
                sport='MLB',
                position='DH',
                team='Dodgers',
                recent_performance=[1.2, 0.8, 1.5, 0.9, 1.3],  # ERA-like stat
                season_performance=[1.2, 0.8, 1.5, 0.9, 1.3, 1.0, 0.7, 1.4],
                career_performance=[0.8, 1.2, 1.5, 0.9, 1.3, 1.0, 0.7, 1.4],
                avg_performance=1.1,
                performance_std=0.3,
                trend_direction='improving',
                consistency_score=0.80,
                injury_status='healthy',
                home_advantage=0.06,
                opponent_strength=0.02,
                weather_impact=0.08,
                historical_edge=0.16,
                public_bias=0.12,
                confidence_multiplier=1.4
            ),

            PlayerProfile(
                player_name='Mookie Betts',
                sport='MLB',
                position='RF',
                team='Dodgers',
                recent_performance=[0.320, 0.285, 0.340, 0.295, 0.310],
                season_performance=[0.320, 0.285, 0.340, 0.295, 0.310, 0.330, 0.280, 0.325],
                career_performance=[0.285, 0.320, 0.340, 0.295, 0.310, 0.330, 0.280, 0.325],
                avg_performance=0.310,
                performance_std=0.025,
                trend_direction='stable',
                consistency_score=0.85,
                injury_status='healthy',
                home_advantage=0.04,
                opponent_strength=0.01,
                weather_impact=0.05,
                historical_edge=0.11,
                public_bias=0.09,
                confidence_multiplier=1.3
            )
        ]

        # Add all players
        for player in nfl_players + nba_players + mlb_players:
            self.player_profiles[player.player_name] = player

        # Sample teams
        teams = [
            TeamProfile(
                team_name='Chiefs',
                sport='NFL',
                league='AFC West',
                recent_form=['W', 'W', 'L', 'W', 'W', 'W', 'L', 'W'],
                season_record='8-3',
                home_record='5-1',
                away_record='3-2',
                offensive_rating=0.85,
                defensive_rating=0.80,
                overall_rating=0.825,
                home_advantage=0.07,
                rest_advantage=0.03
            ),

            TeamProfile(
                team_name='Lakers',
                sport='NBA',
                league='Western Conference',
                recent_form=['W', 'L', 'W', 'W', 'L', 'W', 'W', 'L'],
                season_record='12-8',
                home_record='8-3',
                away_record='4-5',
                offensive_rating=0.82,
                defensive_rating=0.75,
                overall_rating=0.785,
                home_advantage=0.08,
                rest_advantage=0.02
            )
        ]

        for team in teams:
            self.team_profiles[team.team_name] = team

    def _load_data(self):
        """Load existing sports data."""
        # Load players
        if os.path.exists(self.players_file):
            try:
                with open(self.players_file, 'r') as f:
                    data = json.load(f)
                print(f"🏈 Loaded player profiles: {len(data.get('players', {}))} athletes")
            except Exception as e:
                print(f" Error loading player profiles: {e}")

        # Load teams
        if os.path.exists(self.teams_file):
            try:
                with open(self.teams_file, 'r') as f:
                    data = json.load(f)
                print(f"🏈 Loaded team profiles: {len(data.get('teams', {}))} teams")
            except Exception as e:
                print(f" Error loading team profiles: {e}")

        # Load analyses
        if os.path.exists(self.analyses_file):
            try:
                with open(self.analyses_file, 'r') as f:
                    data = json.load(f)
                print(f"🏈 Loaded sports analyses: {len(data.get('analyses', {}))} markets")
            except Exception as e:
                print(f" Error loading sports analyses: {e}")

    def analyze_sports_market(self, market_data: Dict[str, Any]) -> Optional[SportsAnalysis]:
        """Analyze sports market opportunity."""

        market_type = market_data.get('market_type', 'player_prop')
        player_name = market_data.get('player_name', '')
        prop_type = market_data.get('prop_type', '')
        target_value = market_data.get('target_value', 0.0)
        market_prob = market_data.get('market_probability', 0.5)

        # Get player profile
        player = self.player_profiles.get(player_name)
        if not player:
            return None

        # Matchup factors (simplified)
        matchup_factors = {
            'home_advantage': 0.05 if market_data.get('is_home', True) else 0.0,
            'opponent_strength': market_data.get('opponent_rating', 0.5) - 0.5,
            'weather': market_data.get('weather_impact', 0.0)
        }

        # Perform AI analysis
        ai_probability, edge, easy_trade_confidence, rationale, action = self._perform_sports_analysis(
            player, target_value, market_prob, prop_type, matchup_factors
        )

        analysis = SportsAnalysis(
            market_type=market_type,
            sport=player.sport,
            player_or_team=player_name,
            prop_type=prop_type,
            target_value=target_value,
            market_probability=market_prob,
            ai_probability=ai_probability,
            edge=edge,
            easy_trade_confidence=easy_trade_confidence,
            rationale=rationale,
            recommended_action=action
        )

        self.sports_analyses[f"{player_name}_{prop_type}"] = analysis
        self._save_analysis(analysis)

        return analysis

    def _perform_sports_analysis(self, player: PlayerProfile, target_value: float, market_prob: float,
                               prop_type: str, matchup_factors: Dict[str, float]) -> Tuple[float, float, float, str, str]:
        """Perform detailed sports analysis."""

        # Get AI probability and confidence
        ai_prob, confidence = player.predict_performance(target_value, prop_type, matchup_factors)

        edge = abs(ai_prob - market_prob)

        # Get easy trade assessment
        easy_confidence, trade_rationale, action = player.get_easy_sports_trade(
            target_value, market_prob, prop_type, matchup_factors
        )

        # Generate comprehensive rationale
        rationale_parts = [
            f"Player: {player.player_name} ({player.position}, {player.team})",
            f"Sport: {player.sport}",
            f"Prop: {prop_type} {target_value}",
            f"Recent Performance: {player.recent_performance[-3:]} (avg: {statistics.mean(player.recent_performance[-3:]):.1f})",
            f"Consistency: {player.consistency_score:.1%}",
            f"Injury Status: {player.injury_status}",
            f"AI Probability: {ai_prob:.1%} vs Market: {market_prob:.1%} (edge: {edge:.1%})",
            trade_rationale
        ]

        if player.trend_direction != 'stable':
            rationale_parts.append(f"Trend: Performance is {player.trend_direction}")

        if matchup_factors['home_advantage'] > 0:
            rationale_parts.append("Home advantage applies")

        if player.injury_status != 'healthy':
            rationale_parts.append(f"Injury impact: {player.injury_impact:.1%} performance reduction expected")

        rationale = " | ".join(rationale_parts)

        return ai_prob, edge, easy_confidence, rationale, action

    def get_easy_sports_trades(self, min_confidence: float = 0.75) -> List[Dict[str, Any]]:
        """Find sports markets with strong statistical edges."""

        easy_trades = []

        for market_key, analysis in self.sports_analyses.items():
            if analysis.easy_trade_confidence >= min_confidence:
                trade_info = {
                    'player': analysis.player_or_team,
                    'sport': analysis.sport,
                    'prop_type': analysis.prop_type,
                    'target_value': analysis.target_value,
                    'market_probability': analysis.market_probability,
                    'ai_probability': analysis.ai_probability,
                    'edge': analysis.edge,
                    'confidence': analysis.easy_trade_confidence,
                    'rationale': analysis.rationale,
                    'recommended_action': analysis.recommended_action
                }
                easy_trades.append(trade_info)

        # Sort by confidence
        easy_trades.sort(key=lambda x: x['confidence'], reverse=True)
        return easy_trades[:10]  # Top 10 easy sports trades

    def _save_analysis(self, analysis: SportsAnalysis):
        """Save analysis to file."""
        analyses_data = {
            'analyses': {aid: a.to_dict() for aid, a in self.sports_analyses.items()},
            'last_updated': datetime.now().isoformat()
        }

        with open(self.analyses_file, 'w') as f:
            json.dump(analyses_data, f, indent=2)


# Test/demo functions
async def test_sports_analysis_engine():
    """Test the sports analysis engine."""
    print("🏈 TESTING SPORTS ANALYSIS ENGINE")
    print("=" * 45)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)

    engine = SportsAnalysisEngine(kalshi, scenario_graph)

    print(f"🏈 Initialized with {len(engine.player_profiles)} player profiles and {len(engine.team_profiles)} team profiles")

    # Test sports markets
    test_markets = [
        {
            'market_type': 'player_prop',
            'player_name': 'Patrick Mahomes',
            'prop_type': 'passing_yards',
            'target_value': 300.0,
            'market_probability': 0.65,
            'is_home': True,
            'opponent_rating': 0.6,
            'weather_impact': 0.02
        },
        {
            'market_type': 'player_prop',
            'player_name': 'Stephen Curry',
            'prop_type': 'points',
            'target_value': 30.5,
            'market_probability': 0.55,
            'is_home': False,
            'opponent_rating': 0.7,
            'weather_impact': 0.0
        },
        {
            'market_type': 'player_prop',
            'player_name': 'Cooper Kupp',
            'prop_type': 'receiving_yards',
            'target_value': 85.5,
            'market_probability': 0.60,
            'is_home': True,
            'opponent_rating': 0.5,
            'weather_impact': 0.01
        },
        {
            'market_type': 'player_prop',
            'player_name': 'LeBron James',
            'prop_type': 'points',
            'target_value': 28.5,
            'market_probability': 0.50,
            'is_home': True,
            'opponent_rating': 0.55,
            'weather_impact': 0.0
        },
        {
            'market_type': 'player_prop',
            'player_name': 'Shohei Ohtani',
            'prop_type': 'hits',
            'target_value': 1.5,
            'market_probability': 0.55,
            'is_home': False,
            'opponent_rating': 0.6,
            'weather_impact': 0.05
        }
    ]

    print("\n🏈 ANALYZING SPORTS MARKETS FOR STATISTICAL EDGES:")
    for market in test_markets:
        print(f"\n🏈 PLAYER: {market['player_name']} - {market['prop_type']} {market['target_value']}")
        print(".1%")

        # Analyze the sports market
        analysis = engine.analyze_sports_market(market)

        if analysis:
            print("    SPORTS MARKET DETECTED")
            print(f"   AI Probability: {analysis.ai_probability:.1%}")
            print(f"   Market Edge: {analysis.edge:.1%}")
            print(f"   Easy Trade Confidence: {analysis.easy_trade_confidence:.1%}")

            if analysis.easy_trade_confidence > 0.75:
                print("   🎯 EASY SPORTS TRADE OPPORTUNITY! 🎯")
                print(f"   Recommended: {analysis.recommended_action}")
            else:
                print("   ❓ Standard sports market"

            print(f"   Rationale: {analysis.rationale}")
        else:
            print("    No player data for this market"

        print("-" * 70)

    # Show easy sports trades
    print("\n🎯 EASY SPORTS TRADES (75%+ confidence):")
    easy_trades = engine.get_easy_sports_trades()

    if easy_trades:
        for i, trade in enumerate(easy_trades, 1):
            print(f"{i}. {trade['player']} ({trade['sport']}): {trade['confidence']:.1%} confidence")
            print(f"   Prop: {trade['prop_type']} {trade['target_value']} | Edge: {trade['edge']:.1%}")
            print(f"   {trade['recommended_action']}")
            print(f"   Rationale: {trade['rationale'][:100]}...")
            print()
    else:
        print("No easy sports trades found with current thresholds")

    print("\n Sports Analysis Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_sports_analysis_engine())
