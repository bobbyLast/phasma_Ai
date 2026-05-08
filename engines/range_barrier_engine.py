"""
🔒 RANGE BARRIER ENGINE

Advanced volatility analysis system for identifying "easy trades" in low-volatility assets
and barrier market structures where extreme moves are systematically mispriced.

Features:
- Volatility Regime Detection (low-vol, normal, high-vol periods)
- Barrier Market Analysis (knock-in/knock-out pricing inefficiencies)
- Range Trading Opportunities (assets stuck in tight ranges)
- Volatility Expansion Prediction (breakout vs mean-reversion)
- Low-Volatility Edge Detection (overpriced extreme move probabilities)
- High-Confidence Range Trade Identification (volatility-based edges)
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
class VolatilityProfile:
    """Volatility profile for an asset or market."""
    asset_name: str
    asset_type: str  # 'equity', 'bond', 'commodity', 'crypto', 'index'

    # Historical volatility data
    daily_volatility: List[float] = field(default_factory=list)
    weekly_volatility: List[float] = field(default_factory=list)
    monthly_volatility: List[float] = field(default_factory=list)

    # Volatility statistics
    avg_daily_vol: float = 0.0
    avg_weekly_vol: float = 0.0
    avg_monthly_vol: float = 0.0
    vol_of_vol: float = 0.0  # volatility of volatility

    # Current regime
    current_regime: str = 'normal'  # 'low_vol', 'normal', 'high_vol'
    regime_duration_days: int = 0
    regime_strength: float = 0.0  # how extreme the current regime is

    # Range characteristics
    tight_range_probability: float = 0.0  # probability of staying in tight range
    breakout_probability: float = 0.0  # probability of breaking out
    mean_reversion_strength: float = 0.0

    # Barrier market performance
    barrier_market_edge: float = 0.0  # historical edge in barrier markets
    range_trading_edge: float = 0.0  # edge in range-bound trading

    # Market efficiency
    overreaction_tendency: float = 0.0  # tendency to overreact to news
    institutional_flow_impact: float = 0.0

    last_updated: datetime = field(default_factory=lambda: datetime.now())

    def classify_volatility_regime(self, current_vol: float) -> Tuple[str, float]:
        """Classify current volatility regime."""

        if not self.daily_volatility:
            return 'normal', 0.0

        # Calculate percentiles
        sorted_vols = sorted(self.daily_volatility)
        p10 = sorted_vols[int(len(sorted_vols) * 0.1)]
        p90 = sorted_vols[int(len(sorted_vols) * 0.9)]

        if current_vol <= p10:
            regime = 'low_vol'
            strength = (p10 - current_vol) / p10  # how far below 10th percentile
        elif current_vol >= p90:
            regime = 'high_vol'
            strength = (current_vol - p90) / p90  # how far above 90th percentile
        else:
            regime = 'normal'
            strength = 0.0

        return regime, strength

    def predict_range_barrier_outcome(self, barrier_type: str, barrier_level: float,
                                    current_price: float, time_to_barrier: int) -> Tuple[float, float]:
        """Predict outcome of barrier/range market."""

        # Distance to barrier (normalized)
        distance = abs(barrier_level - current_price) / current_price

        # Time decay factor
        time_factor = 1.0 - (time_to_barrier / 365.0)  # annual time decay

        # Base probability based on volatility regime
        if self.current_regime == 'low_vol':
            # In low vol, more likely to stay within ranges
            if barrier_type in ['stays_within', 'below_barrier', 'above_barrier']:
                base_prob = 0.7 + (self.regime_strength * 0.2)  # up to 90% in extreme low vol
            else:  # hits barrier
                base_prob = 0.3 - (self.regime_strength * 0.2)  # down to 10%
        elif self.current_regime == 'high_vol':
            # In high vol, more likely to hit barriers
            if barrier_type in ['hits_barrier', 'breaks_range']:
                base_prob = 0.7 + (self.regime_strength * 0.2)
            else:
                base_prob = 0.3 - (self.regime_strength * 0.2)
        else:
            # Normal vol
            if barrier_type in ['stays_within', 'below_barrier', 'above_barrier']:
                base_prob = 0.6
            else:
                base_prob = 0.4

        # Adjust for distance and time
        if barrier_type in ['stays_within', 'below_barrier', 'above_barrier']:
            # Further barriers are more likely to be respected
            distance_bonus = distance * 0.3
            base_prob += distance_bonus
        else:
            # Closer barriers more likely to be hit
            distance_penalty = (1 - distance) * 0.3
            base_prob += distance_penalty

        # Apply time decay
        base_prob *= time_factor

        # Apply mean reversion in tight ranges
        if self.tight_range_probability > 0.7:
            if barrier_type in ['stays_within', 'below_barrier', 'above_barrier']:
                base_prob += 0.1  # bonus for staying in range

        base_prob = max(0.01, min(0.99, base_prob))

        # Confidence based on data quality and regime clarity
        confidence = min(0.9, len(self.daily_volatility) / 50.0)  # more data = more confidence
        confidence *= (1.0 + self.regime_strength * 0.5)  # stronger regime = more confidence

        return base_prob, confidence

    def get_easy_range_barrier_trade(self, barrier_type: str, barrier_level: float,
                                   current_price: float, time_to_barrier: int,
                                   market_prob: float) -> Tuple[float, str, str]:
        """Get easy trade based on volatility/range analysis."""

        ai_prob, confidence = self.predict_range_barrier_outcome(
            barrier_type, barrier_level, current_price, time_to_barrier
        )

        edge = abs(ai_prob - market_prob)

        # Easy trade conditions
        if self.current_regime == 'low_vol' and self.regime_strength > 0.5:
            if edge > 0.2 and confidence > 0.7:
                if ai_prob > market_prob + 0.15:
                    return confidence, f"Extreme low-vol regime: AI sees {ai_prob:.1%} vs market {market_prob:.1%} ({edge:.1%} edge)", f"BUY {barrier_type.upper()}"
                elif ai_prob < market_prob - 0.15:
                    return confidence, f"Extreme low-vol regime: AI sees {ai_prob:.1%} vs market {market_prob:.1%} ({edge:.1%} edge)", f"SELL {barrier_type.upper()}"
        elif self.tight_range_probability > 0.8 and time_to_barrier > 30:
            if barrier_type in ['stays_within', 'below_barrier', 'above_barrier'] and edge > 0.15:
                return 0.8, f"Tight range asset with {self.tight_range_probability:.1%} range probability - underpriced stability", f"BUY RANGE STABILITY"
        elif self.mean_reversion_strength > 0.7 and abs(current_price - barrier_level) / current_price < 0.05:
            # Close to barrier, likely to mean revert
            return 0.75, f"Strong mean reversion near barrier - market overpricing breakout", "BUY MEAN REVERSION"

        return 0.5, "No clear volatility-based edge", "MONITOR"


@dataclass
class RangeBarrierAnalysis:
    """Analysis of range/barrier market opportunity."""
    asset_name: str
    asset_type: str
    barrier_type: str
    barrier_level: float
    current_price: float
    time_to_barrier: int
    volatility_regime: str
    regime_strength: float
    ai_probability: float
    market_probability: float
    edge: float
    easy_trade_confidence: float
    rationale: str
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'asset_name': self.asset_name,
            'asset_type': self.asset_type,
            'barrier_type': self.barrier_type,
            'barrier_level': self.barrier_level,
            'current_price': self.current_price,
            'time_to_barrier': self.time_to_barrier,
            'volatility_regime': self.volatility_regime,
            'regime_strength': self.regime_strength,
            'ai_probability': self.ai_probability,
            'market_probability': self.market_probability,
            'edge': self.edge,
            'easy_trade_confidence': self.easy_trade_confidence,
            'rationale': self.rationale,
            'recommended_action': self.recommended_action
        }


class RangeBarrierEngine:
    """
    🔒 Range Barrier Engine

    Specialized AI for analyzing volatility regimes and finding "easy trades"
    in barrier markets and range-bound assets.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine, scenario_graph: ScenarioGraphEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph

        # Volatility profile database
        self.volatility_profiles: Dict[str, VolatilityProfile] = {}

        # Analysis results
        self.range_barrier_analyses: Dict[str, RangeBarrierAnalysis] = {}

        # Data files
        self.profiles_file = "volatility_profiles.json"
        self.analyses_file = "range_barrier_analyses.json"

        # Initialize with known volatility profiles
        self._initialize_volatility_profiles()
        self._load_data()

    def _initialize_volatility_profiles(self):
        """Initialize with known asset volatility profiles."""

        profiles = [
            # Equity indices
            VolatilityProfile(
                asset_name='SPY',
                asset_type='equity_index',
                daily_volatility=[0.012, 0.008, 0.015, 0.009, 0.011, 0.014, 0.007, 0.013],
                weekly_volatility=[0.025, 0.018, 0.032, 0.021, 0.028, 0.019, 0.035, 0.022],
                monthly_volatility=[0.045, 0.038, 0.052, 0.041, 0.048, 0.039, 0.055, 0.042],
                avg_daily_vol=0.011,
                avg_weekly_vol=0.025,
                avg_monthly_vol=0.045,
                vol_of_vol=0.3,
                current_regime='normal',
                regime_duration_days=15,
                regime_strength=0.2,
                tight_range_probability=0.6,
                breakout_probability=0.4,
                mean_reversion_strength=0.65,
                barrier_market_edge=0.08,
                range_trading_edge=0.06,
                overreaction_tendency=0.7,
                institutional_flow_impact=0.8
            ),

            VolatilityProfile(
                asset_name='QQQ',
                asset_type='equity_index',
                daily_volatility=[0.015, 0.011, 0.018, 0.012, 0.014, 0.017, 0.009, 0.016],
                weekly_volatility=[0.032, 0.022, 0.038, 0.026, 0.035, 0.024, 0.041, 0.028],
                monthly_volatility=[0.055, 0.042, 0.062, 0.048, 0.058, 0.044, 0.065, 0.049],
                avg_daily_vol=0.014,
                avg_weekly_vol=0.033,
                avg_monthly_vol=0.053,
                vol_of_vol=0.35,
                current_regime='normal',
                regime_duration_days=12,
                regime_strength=0.25,
                tight_range_probability=0.55,
                breakout_probability=0.45,
                mean_reversion_strength=0.6,
                barrier_market_edge=0.10,
                range_trading_edge=0.07,
                overreaction_tendency=0.8,
                institutional_flow_impact=0.75
            ),

            # Bonds (typically lower vol)
            VolatilityProfile(
                asset_name='TLT',
                asset_type='bond_etf',
                daily_volatility=[0.008, 0.005, 0.009, 0.006, 0.007, 0.008, 0.004, 0.007],
                weekly_volatility=[0.015, 0.012, 0.018, 0.014, 0.016, 0.013, 0.019, 0.015],
                monthly_volatility=[0.025, 0.022, 0.028, 0.024, 0.026, 0.023, 0.029, 0.025],
                avg_daily_vol=0.007,
                avg_weekly_vol=0.015,
                avg_monthly_vol=0.025,
                vol_of_vol=0.2,
                current_regime='low_vol',
                regime_duration_days=45,
                regime_strength=0.6,
                tight_range_probability=0.75,
                breakout_probability=0.25,
                mean_reversion_strength=0.8,
                barrier_market_edge=0.05,
                range_trading_edge=0.04,
                overreaction_tendency=0.5,
                institutional_flow_impact=0.9
            ),

            # Commodities (high vol, mean reverting)
            VolatilityProfile(
                asset_name='GLD',
                asset_type='commodity_etf',
                daily_volatility=[0.018, 0.014, 0.022, 0.016, 0.019, 0.021, 0.013, 0.020],
                weekly_volatility=[0.035, 0.028, 0.042, 0.032, 0.038, 0.029, 0.045, 0.034],
                monthly_volatility=[0.065, 0.052, 0.072, 0.058, 0.068, 0.055, 0.075, 0.061],
                avg_daily_vol=0.018,
                avg_weekly_vol=0.035,
                avg_monthly_vol=0.061,
                vol_of_vol=0.4,
                current_regime='normal',
                regime_duration_days=8,
                regime_strength=0.15,
                tight_range_probability=0.5,
                breakout_probability=0.5,
                mean_reversion_strength=0.75,
                barrier_market_edge=0.12,
                range_trading_edge=0.08,
                overreaction_tendency=0.6,
                institutional_flow_impact=0.7
            ),

            # Crypto (extreme vol)
            VolatilityProfile(
                asset_name='BTC',
                asset_type='crypto',
                daily_volatility=[0.045, 0.032, 0.058, 0.038, 0.052, 0.061, 0.029, 0.055],
                weekly_volatility=[0.085, 0.062, 0.095, 0.072, 0.088, 0.078, 0.102, 0.081],
                monthly_volatility=[0.125, 0.095, 0.145, 0.115, 0.135, 0.105, 0.155, 0.125],
                avg_daily_vol=0.046,
                avg_weekly_vol=0.083,
                avg_monthly_vol=0.125,
                vol_of_vol=0.6,
                current_regime='high_vol',
                regime_duration_days=22,
                regime_strength=0.4,
                tight_range_probability=0.3,
                breakout_probability=0.7,
                mean_reversion_strength=0.5,
                barrier_market_edge=0.18,
                range_trading_edge=0.12,
                overreaction_tendency=0.9,
                institutional_flow_impact=0.4
            ),

            # Stable assets (very low vol)
            VolatilityProfile(
                asset_name='VIG',
                asset_type='dividend_etf',
                daily_volatility=[0.006, 0.004, 0.007, 0.005, 0.006, 0.007, 0.003, 0.006],
                weekly_volatility=[0.012, 0.009, 0.015, 0.011, 0.013, 0.010, 0.016, 0.012],
                monthly_volatility=[0.020, 0.017, 0.023, 0.019, 0.021, 0.018, 0.024, 0.020],
                avg_daily_vol=0.006,
                avg_weekly_vol=0.012,
                avg_monthly_vol=0.020,
                vol_of_vol=0.15,
                current_regime='low_vol',
                regime_duration_days=60,
                regime_strength=0.7,
                tight_range_probability=0.85,
                breakout_probability=0.15,
                mean_reversion_strength=0.9,
                barrier_market_edge=0.03,
                range_trading_edge=0.02,
                overreaction_tendency=0.3,
                institutional_flow_impact=0.95
            )
        ]

        for profile in profiles:
            self.volatility_profiles[profile.asset_name] = profile

    def _load_data(self):
        """Load existing volatility data."""
        # Load profiles
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                print(f"🔒 Loaded volatility profiles: {len(data.get('profiles', {}))} assets")
            except Exception as e:
                print(f" Error loading volatility profiles: {e}")

        # Load analyses
        if os.path.exists(self.analyses_file):
            try:
                with open(self.analyses_file, 'r') as f:
                    data = json.load(f)
                print(f"🔒 Loaded range barrier analyses: {len(data.get('analyses', {}))} barrier markets")
            except Exception as e:
                print(f" Error loading range barrier analyses: {e}")

    def analyze_range_barrier_market(self, market_data: Dict[str, Any]) -> Optional[RangeBarrierAnalysis]:
        """Analyze range/barrier market opportunity."""

        asset_name = market_data.get('asset_name', '').upper()
        barrier_type = market_data.get('barrier_type', 'stays_within')
        barrier_level = market_data.get('barrier_level', 0.0)
        current_price = market_data.get('current_price', 0.0)
        time_to_barrier = market_data.get('time_to_barrier', 30)
        market_prob = market_data.get('market_probability', 0.5)

        # Get volatility profile
        profile = self.volatility_profiles.get(asset_name)
        if not profile:
            return None

        # Update current regime
        current_vol = market_data.get('current_volatility', profile.avg_daily_vol)
        regime, strength = profile.classify_volatility_regime(current_vol)
        profile.current_regime = regime
        profile.regime_strength = strength

        # Perform AI analysis
        ai_probability, edge, easy_trade_confidence, rationale, action = self._perform_range_barrier_analysis(
            profile, barrier_type, barrier_level, current_price, time_to_barrier, market_prob
        )

        analysis = RangeBarrierAnalysis(
            asset_name=asset_name,
            asset_type=profile.asset_type,
            barrier_type=barrier_type,
            barrier_level=barrier_level,
            current_price=current_price,
            time_to_barrier=time_to_barrier,
            volatility_regime=profile.current_regime,
            regime_strength=profile.regime_strength,
            ai_probability=ai_probability,
            market_probability=market_prob,
            edge=edge,
            easy_trade_confidence=easy_trade_confidence,
            rationale=rationale,
            recommended_action=action
        )

        self.range_barrier_analyses[f"{asset_name}_{barrier_type}"] = analysis
        self._save_analysis(analysis)

        return analysis

    def _perform_range_barrier_analysis(self, profile: VolatilityProfile, barrier_type: str,
                                      barrier_level: float, current_price: float,
                                      time_to_barrier: int, market_prob: float) -> Tuple[float, float, float, str, str]:
        """Perform detailed range/barrier analysis."""

        # Get AI probability
        ai_prob, confidence = profile.predict_range_barrier_outcome(
            barrier_type, barrier_level, current_price, time_to_barrier
        )

        edge = abs(ai_prob - market_prob)

        # Get easy trade assessment
        easy_confidence, trade_rationale, action = profile.get_easy_range_barrier_trade(
            barrier_type, barrier_level, current_price, time_to_barrier, market_prob
        )

        # Generate comprehensive rationale
        rationale_parts = [
            f"Asset: {profile.asset_name} ({profile.asset_type})",
            f"Barrier Type: {barrier_type} at {barrier_level:.2f}",
            f"Current Price: {current_price:.2f} | Time to Barrier: {time_to_barrier} days",
            f"Volatility Regime: {profile.current_regime} (strength: {profile.regime_strength:.1%})",
            f"Avg Daily Vol: {profile.avg_daily_vol:.1%} | Current: {current_price * profile.avg_daily_vol:.1%}",  # rough estimate
            f"Tight Range Probability: {profile.tight_range_probability:.1%}",
            f"Mean Reversion Strength: {profile.mean_reversion_strength:.1%}",
            f"AI Probability: {ai_prob:.1%} vs Market: {market_prob:.1%} (edge: {edge:.1%})",
            trade_rationale
        ]

        if profile.current_regime == 'low_vol' and profile.regime_strength > 0.5:
            rationale_parts.append("Extreme low-vol regime favors range stability")

        if profile.tight_range_probability > 0.8:
            rationale_parts.append("Asset historically stays in tight ranges")

        rationale = " | ".join(rationale_parts)

        return ai_prob, edge, easy_confidence, rationale, action

    def get_easy_range_barrier_trades(self, min_confidence: float = 0.75) -> List[Dict[str, Any]]:
        """Find barrier/range markets with strong volatility-based edges."""

        easy_trades = []

        for market_key, analysis in self.range_barrier_analyses.items():
            if analysis.easy_trade_confidence >= min_confidence:
                trade_info = {
                    'asset': analysis.asset_name,
                    'asset_type': analysis.asset_type,
                    'barrier_type': analysis.barrier_type,
                    'barrier_level': analysis.barrier_level,
                    'current_price': analysis.current_price,
                    'time_to_barrier': analysis.time_to_barrier,
                    'volatility_regime': analysis.volatility_regime,
                    'regime_strength': analysis.regime_strength,
                    'ai_probability': analysis.ai_probability,
                    'market_probability': analysis.market_probability,
                    'edge': analysis.edge,
                    'confidence': analysis.easy_trade_confidence,
                    'rationale': analysis.rationale,
                    'recommended_action': analysis.recommended_action
                }
                easy_trades.append(trade_info)

        # Sort by confidence
        easy_trades.sort(key=lambda x: x['confidence'], reverse=True)
        return easy_trades[:10]  # Top 10 easy range/barrier trades

    def _save_analysis(self, analysis: RangeBarrierAnalysis):
        """Save analysis to file."""
        analyses_data = {
            'analyses': {aid: a.to_dict() for aid, a in self.range_barrier_analyses.items()},
            'last_updated': datetime.now().isoformat()
        }

        with open(self.analyses_file, 'w') as f:
            json.dump(analyses_data, f, indent=2)


# Test/demo functions
async def test_range_barrier_engine():
    """Test the range barrier analysis engine."""
    print("🔒 TESTING RANGE BARRIER ENGINE")
    print("=" * 45)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)

    engine = RangeBarrierEngine(kalshi, scenario_graph)

    print(f"🔒 Initialized with {len(engine.volatility_profiles)} volatility profiles")

    # Test range/barrier markets
    test_markets = [
        {
            'asset_name': 'SPY',
            'barrier_type': 'stays_within',
            'barrier_level': 450.0,
            'current_price': 440.0,
            'time_to_barrier': 30,
            'market_probability': 0.65,
            'current_volatility': 0.008  # Low vol regime
        },
        {
            'asset_name': 'TLT',
            'barrier_type': 'below_barrier',
            'barrier_level': 95.0,
            'current_price': 92.0,
            'time_to_barrier': 60,
            'market_probability': 0.55,
            'current_volatility': 0.004  # Very low vol
        },
        {
            'asset_name': 'BTC',
            'barrier_type': 'hits_barrier',
            'barrier_level': 50000.0,
            'current_price': 48000.0,
            'time_to_barrier': 14,
            'market_probability': 0.70,
            'current_volatility': 0.055  # High vol
        },
        {
            'asset_name': 'VIG',
            'barrier_type': 'stays_within',
            'barrier_level': 180.0,
            'current_price': 178.0,
            'time_to_barrier': 90,
            'market_probability': 0.75,
            'current_volatility': 0.003  # Extreme low vol
        }
    ]

    print("\n🔒 ANALYZING RANGE/BARRIER MARKETS FOR VOLATILITY EDGES:")
    for market in test_markets:
        print(f"\n🔒 ASSET: {market['asset_name']} - {market['barrier_type']} {market['barrier_level']}")
        print(f"   Current: {market['current_price']} | Days to Barrier: {market['time_to_barrier']}")
        print(f"   Market Probability: {market['market_probability']:.1%}")

        # Analyze the range/barrier market
        analysis = engine.analyze_range_barrier_market(market)

        if analysis:
            print("    VOLATILITY ANALYSIS COMPLETE")
            print(f"   Regime: {analysis.volatility_regime} (strength: {analysis.regime_strength:.1%})")
            print(f"   AI Probability: {analysis.ai_probability:.1%}")
            print(f"   Edge: {analysis.edge:.1%}")
            print(f"   Easy Trade Confidence: {analysis.easy_trade_confidence:.1%}")

            if analysis.easy_trade_confidence > 0.75:
                print("   🎯 EASY VOLATILITY TRADE OPPORTUNITY! 🎯")
                print(f"   Recommended: {analysis.recommended_action}")
            else:
                print("   ❓ Standard volatility profile")

            print(f"   Rationale: {analysis.rationale}")
        else:
            print("    No volatility profile for this asset")

        print("-" * 70)

    # Show easy range/barrier trades
    print("\n🎯 EASY RANGE/BARRIER TRADES (75%+ confidence):")
    easy_trades = engine.get_easy_range_barrier_trades()

    if easy_trades:
        for i, trade in enumerate(easy_trades, 1):
            print(f"{i}. {trade['asset']} ({trade['asset_type']}): {trade['confidence']:.1%} confidence")
            print(f"   Barrier: {trade['barrier_type']} at {trade['barrier_level']}")
            print(f"   Regime: {trade['volatility_regime']} | Edge: {trade['edge']:.1%}")
            print(f"   {trade['recommended_action']}")
            print(f"   Rationale: {trade['rationale'][:100]}...")
            print()
    else:
        print("No easy range/barrier trades found with current thresholds")

    print("\n Range Barrier Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_range_barrier_engine())
