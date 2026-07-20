"""
📊 MICROSTRUCTURE ENGINE

Capability-honest microstructure analysis.

Without consolidated L2 / full depth (Alpaca Basic / IEX quotes):
  capability = limited_quote_microstructure
  — never claim "easy trades" from canned profiles alone.
  — use bid/ask/spread/slippage when available; else degrade size or block aggressive entries.
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
class MicrostructureProfile:
    """Microstructure profile for a market or instrument."""
    market_name: str
    market_type: str  # 'equity', 'crypto', 'prediction_market', 'forex'

    # Liquidity metrics
    avg_daily_volume: float = 0.0
    avg_spread_bps: float = 0.0
    market_depth: float = 0.0  # liquidity depth score

    # Order flow patterns
    bid_ask_imbalance_history: List[float] = field(default_factory=list)
    volume_spike_history: List[float] = field(default_factory=list)
    price_impact_history: List[float] = field(default_factory=list)

    # Anomaly detection
    volume_spike_threshold: float = 0.0  # std deviations for spike
    price_move_threshold: float = 0.0  # std deviations for unusual move
    imbalance_threshold: float = 0.0  # threshold for order flow imbalance

    # Mean reversion patterns
    short_term_reversion: float = 0.0  # tendency to revert within minutes/hours
    overreaction_tendency: float = 0.0  # tendency to overreact to news
    institutional_impact: float = 0.0  # how much institutions move price

    # Market efficiency
    arbitrage_opportunities: float = 0.0  # frequency of arb opportunities
    latency_arbitrage: float = 0.0  # speed-based edge opportunities
    fragmentation_impact: float = 0.0  # cross-venue inefficiencies

    # Edge metrics
    microstructure_edge: float = 0.0  # historical edge from microstructure
    volume_anomaly_edge: float = 0.0
    liquidity_edge: float = 0.0

    last_updated: datetime = field(default_factory=lambda: datetime.now())

    def detect_volume_anomaly(self, current_volume: float, recent_avg_volume: float) -> Tuple[bool, float]:
        """Detect unusual volume activity."""

        if recent_avg_volume == 0:
            return False, 0.0

        volume_ratio = current_volume / recent_avg_volume
        volume_zscore = (volume_ratio - 1) / self.volume_spike_threshold if self.volume_spike_threshold > 0 else 0

        is_anomaly = abs(volume_zscore) > 2.0  # 2 std deviations
        return is_anomaly, volume_zscore

    def detect_price_anomaly(self, current_price: float, recent_prices: List[float]) -> Tuple[bool, float]:
        """Detect unusual price movements."""

        if len(recent_prices) < 5:
            return False, 0.0

        recent_avg = statistics.mean(recent_prices)
        recent_std = statistics.stdev(recent_prices)

        if recent_std == 0:
            return False, 0.0

        price_zscore = (current_price - recent_avg) / recent_std
        is_anomaly = abs(price_zscore) > self.price_move_threshold

        return is_anomaly, price_zscore

    def detect_flow_imbalance(self, bid_volume: float, ask_volume: float) -> Tuple[bool, float]:
        """Detect order flow imbalances."""

        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return False, 0.0

        imbalance_ratio = (bid_volume - ask_volume) / total_volume
        is_imbalance = abs(imbalance_ratio) > self.imbalance_threshold

        return is_imbalance, imbalance_ratio

    def predict_microstructure_reversion(self, anomaly_type: str, anomaly_strength: float,
                                       time_since_anomaly: int) -> Tuple[float, float]:
        """Predict likelihood and speed of price reversion after microstructure anomaly."""

        # Base reversion probability
        if anomaly_type == 'volume_spike':
            base_reversion = self.short_term_reversion * 0.8
        elif anomaly_type == 'price_move':
            base_reversion = self.overreaction_tendency * 0.9
        elif anomaly_type == 'flow_imbalance':
            base_reversion = self.institutional_impact * 0.7
        else:
            base_reversion = 0.5

        # Adjust for anomaly strength
        strength_multiplier = min(1.5, 1.0 + abs(anomaly_strength) * 0.2)

        # Time decay (reversion weakens over time)
        time_decay = max(0.1, 1.0 - (time_since_anomaly / 60.0))  # minutes

        reversion_probability = base_reversion * strength_multiplier * time_decay
        reversion_probability = max(0.05, min(0.95, reversion_probability))

        # Speed of reversion (minutes)
        reversion_speed = 5 + (30 * (1 - reversion_probability))  # faster for stronger signals

        return reversion_probability, reversion_speed

    def get_easy_microstructure_trade(self, current_data: Dict[str, Any]) -> Tuple[float, str, str]:
        """Legacy name kept for callers — capability-gated; never claims easy L2 trades."""
        capability = str(
            current_data.get("capability")
            or getattr(self, "capability", None)
            or "limited_quote_microstructure"
        )
        has_quote = any(
            current_data.get(k) is not None
            for k in ("bid", "ask", "bid_price", "ask_price", "spread_bps")
        )
        has_depth = bool(current_data.get("l2_depth") or current_data.get("full_depth"))

        if capability == "limited_quote_microstructure" and not has_depth:
            # Without real L2: only soft liquidity/spread advice, never "easy trade"
            spread = current_data.get("spread_bps")
            try:
                spread_f = float(spread) if spread is not None else None
            except (TypeError, ValueError):
                spread_f = None
            if spread_f is not None and spread_f > 50:
                return 0.2, "Wide spread under limited_quote_microstructure — degrade size / block aggressive", "DEGRADE_OR_BLOCK"
            if has_quote:
                return 0.35, "Limited quote microstructure only — no L2 easy-trade claim", "MONITOR"
            return 0.15, "No bid/ask/depth — cannot assert microstructure edge", "BLOCK_AGGRESSIVE"

        # Full-depth path (only when explicitly available)
        anomalies = []
        current_vol = current_data.get('current_volume', 0)
        recent_avg_vol = current_data.get('recent_avg_volume', 0)
        vol_anomaly, vol_zscore = self.detect_volume_anomaly(current_vol, recent_avg_vol)
        if vol_anomaly:
            anomalies.append(('volume_spike', vol_zscore))
        current_price = current_data.get('current_price', 0)
        recent_prices = current_data.get('recent_prices', [])
        price_anomaly, price_zscore = self.detect_price_anomaly(current_price, recent_prices)
        if price_anomaly:
            anomalies.append(('price_move', price_zscore))
        bid_vol = current_data.get('bid_volume', 0)
        ask_vol = current_data.get('ask_volume', 0)
        flow_imbalance, imbalance_ratio = self.detect_flow_imbalance(bid_vol, ask_vol)
        if flow_imbalance:
            anomalies.append(('flow_imbalance', imbalance_ratio))
        if not anomalies:
            return 0.4, "No microstructure anomalies (full depth path)", "MONITOR"
        strongest_anomaly = max(anomalies, key=lambda x: abs(x[1]))
        anomaly_type, anomaly_strength = strongest_anomaly
        time_since = current_data.get('time_since_anomaly', 5)
        reversion_prob, reversion_speed = self.predict_microstructure_reversion(
            anomaly_type, anomaly_strength, time_since
        )
        if reversion_prob > 0.75 and abs(anomaly_strength) > 2.0 and has_depth:
            direction = "BUY" if (anomaly_type == 'price_move' and anomaly_strength < 0) or \
                               (anomaly_type == 'flow_imbalance' and anomaly_strength > 0) else "SELL"
            confidence = min(0.75, reversion_prob)
            return confidence, f"{anomaly_type} with depth ({anomaly_strength:.1f}σ) rev {reversion_prob:.0%} ~{reversion_speed:.0f}m", f"{direction} MICRO"
        return 0.45, f"Weak {anomaly_type} — monitor", "MONITOR"


@dataclass
class MicrostructureAnalysis:
    """Analysis of microstructure trading opportunity."""
    market_name: str
    market_type: str
    anomaly_type: str
    anomaly_strength: float
    reversion_probability: float
    reversion_speed_minutes: float
    time_since_anomaly: int
    current_volume: float
    recent_avg_volume: float
    easy_trade_confidence: float
    rationale: str
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'market_name': self.market_name,
            'market_type': self.market_type,
            'anomaly_type': self.anomaly_type,
            'anomaly_strength': self.anomaly_strength,
            'reversion_probability': self.reversion_probability,
            'reversion_speed_minutes': self.reversion_speed_minutes,
            'time_since_anomaly': self.time_since_anomaly,
            'current_volume': self.current_volume,
            'recent_avg_volume': self.recent_avg_volume,
            'easy_trade_confidence': self.easy_trade_confidence,
            'rationale': self.rationale,
            'recommended_action': self.recommended_action
        }


class MicrostructureEngine:
    """
    Capability-honest microstructure analysis.

    Default capability: limited_quote_microstructure (Alpaca Basic / no consolidated L2).
    Canned profiles are diagnostic priors only — they never authorize "easy trades".
    """

    CAPABILITY_LIMITED = "limited_quote_microstructure"
    CAPABILITY_FULL_DEPTH = "full_depth_microstructure"

    def __init__(self, kalshi_engine: KalshiPredictionEngine, scenario_graph: ScenarioGraphEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph
        self.capability = self.CAPABILITY_LIMITED

        # Microstructure profile database (diagnostic priors only)
        self.microstructure_profiles: Dict[str, MicrostructureProfile] = {}

        # Analysis results
        self.microstructure_analyses: Dict[str, MicrostructureAnalysis] = {}

        # Data files
        self.profiles_file = engine_state_path("microstructure_profiles.json")
        self.analyses_file = engine_state_path("microstructure_analyses.json")

        # Initialize with known microstructure profiles
        self._initialize_microstructure_profiles()
        self._load_data()

    def assess_entry_permission(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return size_mult / block_aggressive based on real quotes, not canned profiles."""
        data = dict(market_data or {})
        data.setdefault("capability", self.capability)
        conf, rationale, action = MicrostructureProfile(
            market_name=str(data.get("symbol") or "UNKNOWN"),
            market_type=str(data.get("market_type") or "equity"),
        ).get_easy_microstructure_trade(data)
        block = action in ("BLOCK_AGGRESSIVE", "DEGRADE_OR_BLOCK") or conf < 0.25
        size_mult = 1.0
        if action == "DEGRADE_OR_BLOCK":
            size_mult = 0.35
        elif self.capability == self.CAPABILITY_LIMITED:
            size_mult = 0.7 if conf >= 0.3 else 0.4
        return {
            "capability": self.capability,
            "confidence": conf,
            "rationale": rationale,
            "action": action,
            "block_aggressive": block,
            "size_multiplier": size_mult,
            "claims_easy_trade": False,
        }
    def _initialize_microstructure_profiles(self):
        """Initialize with known market microstructure profiles."""

        profiles = [
            # High-volume equity markets
            MicrostructureProfile(
                market_name='SPY',
                market_type='equity',
                avg_daily_volume=85000000,
                avg_spread_bps=1.5,
                market_depth=0.95,
                bid_ask_imbalance_history=[0.02, -0.03, 0.01, 0.04, -0.02, 0.03, -0.01, 0.02],
                volume_spike_history=[1.2, 0.9, 1.5, 0.8, 1.3, 1.1, 0.7, 1.4],
                price_impact_history=[0.015, 0.008, 0.022, 0.012, 0.018, 0.009, 0.025, 0.014],
                volume_spike_threshold=0.4,
                price_move_threshold=2.5,
                imbalance_threshold=0.15,
                short_term_reversion=0.75,
                overreaction_tendency=0.7,
                institutional_impact=0.8,
                arbitrage_opportunities=0.15,
                latency_arbitrage=0.08,
                fragmentation_impact=0.05,
                microstructure_edge=0.12,
                volume_anomaly_edge=0.08,
                liquidity_edge=0.06
            ),

            # Crypto markets (high volatility, thin liquidity)
            MicrostructureProfile(
                market_name='BTC',
                market_type='crypto',
                avg_daily_volume=25000000,
                avg_spread_bps=25.0,
                market_depth=0.6,
                bid_ask_imbalance_history=[0.08, -0.12, 0.06, 0.15, -0.09, 0.11, -0.07, 0.13],
                volume_spike_history=[2.1, 1.8, 2.5, 1.6, 2.3, 1.9, 1.4, 2.7],
                price_impact_history=[0.045, 0.032, 0.058, 0.038, 0.052, 0.061, 0.029, 0.055],
                volume_spike_threshold=0.8,
                price_move_threshold=3.0,
                imbalance_threshold=0.25,
                short_term_reversion=0.55,
                overreaction_tendency=0.9,
                institutional_impact=0.4,
                arbitrage_opportunities=0.35,
                latency_arbitrage=0.22,
                fragmentation_impact=0.18,
                microstructure_edge=0.25,
                volume_anomaly_edge=0.18,
                liquidity_edge=0.12
            ),

            # Prediction markets (thin, emotional)
            MicrostructureProfile(
                market_name='KALSHI',
                market_type='prediction_market',
                avg_daily_volume=500000,
                avg_spread_bps=50.0,
                market_depth=0.3,
                bid_ask_imbalance_history=[0.15, -0.22, 0.12, 0.28, -0.18, 0.25, -0.14, 0.31],
                volume_spike_history=[3.2, 2.8, 3.8, 2.5, 3.5, 2.9, 2.2, 4.1],
                price_impact_history=[0.085, 0.062, 0.095, 0.072, 0.088, 0.078, 0.102, 0.081],
                volume_spike_threshold=1.2,
                price_move_threshold=2.0,
                imbalance_threshold=0.35,
                short_term_reversion=0.65,
                overreaction_tendency=0.95,
                institutional_impact=0.2,
                arbitrage_opportunities=0.45,
                latency_arbitrage=0.15,
                fragmentation_impact=0.28,
                microstructure_edge=0.32,
                volume_anomaly_edge=0.22,
                liquidity_edge=0.18
            ),

            # Forex (deep liquidity, algorithmic)
            MicrostructureProfile(
                market_name='EURUSD',
                market_type='forex',
                avg_daily_volume=1500000000,
                avg_spread_bps=0.8,
                market_depth=0.98,
                bid_ask_imbalance_history=[0.008, -0.012, 0.006, 0.014, -0.009, 0.011, -0.007, 0.013],
                volume_spike_history=[1.1, 0.95, 1.3, 0.9, 1.2, 1.05, 0.85, 1.4],
                price_impact_history=[0.012, 0.008, 0.015, 0.009, 0.011, 0.014, 0.007, 0.013],
                volume_spike_threshold=0.3,
                price_move_threshold=2.8,
                imbalance_threshold=0.08,
                short_term_reversion=0.8,
                overreaction_tendency=0.6,
                institutional_impact=0.9,
                arbitrage_opportunities=0.08,
                latency_arbitrage=0.12,
                fragmentation_impact=0.03,
                microstructure_edge=0.08,
                volume_anomaly_edge=0.05,
                liquidity_edge=0.04
            ),

            # Small cap stocks (thin liquidity)
            MicrostructureProfile(
                market_name='SMALL_CAP',
                market_type='equity',
                avg_daily_volume=250000,
                avg_spread_bps=45.0,
                market_depth=0.25,
                bid_ask_imbalance_history=[0.18, -0.25, 0.15, 0.32, -0.21, 0.28, -0.16, 0.35],
                volume_spike_history=[2.8, 2.4, 3.2, 2.1, 2.9, 2.5, 1.8, 3.5],
                price_impact_history=[0.075, 0.055, 0.085, 0.065, 0.078, 0.068, 0.092, 0.075],
                volume_spike_threshold=1.0,
                price_move_threshold=2.2,
                imbalance_threshold=0.30,
                short_term_reversion=0.6,
                overreaction_tendency=0.85,
                institutional_impact=0.3,
                arbitrage_opportunities=0.55,
                latency_arbitrage=0.18,
                fragmentation_impact=0.35,
                microstructure_edge=0.28,
                volume_anomaly_edge=0.20,
                liquidity_edge=0.15
            ),

            # Bond markets (institutional, low volatility)
            MicrostructureProfile(
                market_name='BONDS',
                market_type='fixed_income',
                avg_daily_volume=15000000,
                avg_spread_bps=8.0,
                market_depth=0.75,
                bid_ask_imbalance_history=[0.04, -0.06, 0.03, 0.07, -0.04, 0.05, -0.03, 0.06],
                volume_spike_history=[1.4, 1.2, 1.6, 1.1, 1.5, 1.3, 1.0, 1.7],
                price_impact_history=[0.020, 0.015, 0.025, 0.018, 0.022, 0.016, 0.027, 0.019],
                volume_spike_threshold=0.5,
                price_move_threshold=2.0,
                imbalance_threshold=0.12,
                short_term_reversion=0.7,
                overreaction_tendency=0.5,
                institutional_impact=0.95,
                arbitrage_opportunities=0.12,
                latency_arbitrage=0.06,
                fragmentation_impact=0.08,
                microstructure_edge=0.09,
                volume_anomaly_edge=0.06,
                liquidity_edge=0.05
            )
        ]

        for profile in profiles:
            self.microstructure_profiles[profile.market_name] = profile

    def _load_data(self):
        """Load existing microstructure data."""
        # Load profiles
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                print(f"📊 Loaded microstructure profiles: {len(data.get('profiles', {}))} markets")
            except Exception as e:
                print(f"⚠️ Error loading microstructure profiles: {e}")

        # Load analyses
        if os.path.exists(self.analyses_file):
            try:
                with open(self.analyses_file, 'r') as f:
                    data = json.load(f)
                print(f"📊 Loaded microstructure analyses: {len(data.get('analyses', {}))} opportunities")
            except Exception as e:
                print(f"⚠️ Error loading microstructure analyses: {e}")

    def analyze_microstructure_opportunity(self, market_data: Dict[str, Any]) -> Optional[MicrostructureAnalysis]:
        """Analyze microstructure trading opportunity."""

        market_name = market_data.get('market_name', '')
        market_type = market_data.get('market_type', 'equity')

        # Get microstructure profile
        profile = self.microstructure_profiles.get(market_name)
        if not profile:
            # Try to match by type if specific market not found
            profile = next((p for p in self.microstructure_profiles.values() if p.market_type == market_type), None)
            if not profile:
                return None

        # Perform AI analysis
        anomaly_type, anomaly_strength, reversion_prob, reversion_speed, easy_trade_confidence, rationale, action = self._perform_microstructure_analysis(
            profile, market_data
        )

        analysis = MicrostructureAnalysis(
            market_name=market_name,
            market_type=profile.market_type,
            anomaly_type=anomaly_type,
            anomaly_strength=anomaly_strength,
            reversion_probability=reversion_prob,
            reversion_speed_minutes=reversion_speed,
            time_since_anomaly=market_data.get('time_since_anomaly', 5),
            current_volume=market_data.get('current_volume', 0),
            recent_avg_volume=market_data.get('recent_avg_volume', 0),
            easy_trade_confidence=easy_trade_confidence,
            rationale=rationale,
            recommended_action=action
        )

        self.microstructure_analyses[f"{market_name}_{anomaly_type}"] = analysis
        self._save_analysis(analysis)

        return analysis

    def _perform_microstructure_analysis(self, profile: MicrostructureProfile, market_data: Dict[str, Any]) -> Tuple[str, float, float, float, float, str, str]:
        """Perform detailed microstructure analysis."""

        # Get easy trade assessment
        easy_confidence, trade_rationale, action = profile.get_easy_microstructure_trade(market_data)

        # Identify strongest anomaly
        current_vol = market_data.get('current_volume', 0)
        recent_avg_vol = market_data.get('recent_avg_volume', 0)
        vol_anomaly, vol_zscore = profile.detect_volume_anomaly(current_vol, recent_avg_vol)

        current_price = market_data.get('current_price', 0)
        recent_prices = market_data.get('recent_prices', [])
        price_anomaly, price_zscore = profile.detect_price_anomaly(current_price, recent_prices)

        bid_vol = market_data.get('bid_volume', 0)
        ask_vol = market_data.get('ask_volume', 0)
        flow_imbalance, imbalance_ratio = profile.detect_flow_imbalance(bid_vol, ask_vol)

        # Find strongest anomaly
        anomalies = [
            ('volume_spike', vol_zscore, vol_anomaly),
            ('price_move', price_zscore, price_anomaly),
            ('flow_imbalance', imbalance_ratio, flow_imbalance)
        ]

        valid_anomalies = [(t, s) for t, s, a in anomalies if a]
        if valid_anomalies:
            anomaly_type, anomaly_strength = max(valid_anomalies, key=lambda x: abs(x[1]))
        else:
            anomaly_type, anomaly_strength = 'none', 0.0

        # Predict reversion
        time_since = market_data.get('time_since_anomaly', 5)
        reversion_prob, reversion_speed = profile.predict_microstructure_reversion(
            anomaly_type, anomaly_strength, time_since
        )

        # Generate comprehensive rationale
        rationale_parts = [
            f"Market: {profile.market_name} ({profile.market_type})",
            f"Avg Daily Volume: {profile.avg_daily_volume:,.0f}",
            f"Market Depth: {profile.market_depth:.1%}",
            f"Short-term Reversion: {profile.short_term_reversion:.1%}",
            f"Overreaction Tendency: {profile.overreaction_tendency:.1%}",
            f"Institutional Impact: {profile.institutional_impact:.1%}",
            f"Detected Anomaly: {anomaly_type} (strength: {anomaly_strength:.1f}σ)" if anomaly_type != 'none' else "No anomalies detected",
            f"Reversion Probability: {reversion_prob:.1%} within {reversion_speed:.0f} minutes",
            trade_rationale
        ]

        if profile.market_depth < 0.5:
            rationale_parts.append("Thin market - anomalies more likely to persist")

        if profile.overreaction_tendency > 0.8:
            rationale_parts.append("Market prone to overreactions and quick reversions")

        rationale = " | ".join(rationale_parts)

        return anomaly_type, anomaly_strength, reversion_prob, reversion_speed, easy_confidence, rationale, action

    def get_easy_microstructure_trades(self, min_confidence: float = 0.75) -> List[Dict[str, Any]]:
        """Under limited_quote_microstructure, never emit canned-profile 'easy trades'."""
        if getattr(self, "capability", self.CAPABILITY_LIMITED) == self.CAPABILITY_LIMITED:
            return []  # No fake L2 edge from profile database

        easy_trades = []

        for market_key, analysis in self.microstructure_analyses.items():
            if analysis.easy_trade_confidence >= min_confidence:
                trade_info = {
                    'market': analysis.market_name,
                    'market_type': analysis.market_type,
                    'anomaly_type': analysis.anomaly_type,
                    'anomaly_strength': analysis.anomaly_strength,
                    'reversion_probability': analysis.reversion_probability,
                    'reversion_speed': analysis.reversion_speed_minutes,
                    'time_since_anomaly': analysis.time_since_anomaly,
                    'current_volume': analysis.current_volume,
                    'recent_avg_volume': analysis.recent_avg_volume,
                    'confidence': analysis.easy_trade_confidence,
                    'rationale': analysis.rationale,
                    'recommended_action': analysis.recommended_action
                }
                easy_trades.append(trade_info)

        # Sort by confidence
        easy_trades.sort(key=lambda x: x['confidence'], reverse=True)
        return easy_trades[:10]  # Top 10 easy microstructure trades

    def _save_analysis(self, analysis: MicrostructureAnalysis):
        """Save analysis to file."""
        analyses_data = {
            'analyses': {aid: a.to_dict() for aid, a in self.microstructure_analyses.items()},
            'last_updated': datetime.now().isoformat()
        }

        with open(self.analyses_file, 'w') as f:
            json.dump(analyses_data, f, indent=2)


# Test/demo functions
async def test_microstructure_engine():
    """Test the microstructure analysis engine."""
    print("📊 TESTING MICROSTRUCTURE ENGINE")
    print("=" * 45)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)

    engine = MicrostructureEngine(kalshi, scenario_graph)

    print(f"📊 Initialized with {len(engine.microstructure_profiles)} microstructure profiles")

    # Test microstructure opportunities
    test_opportunities = [
        {
            'market_name': 'SPY',
            'market_type': 'equity',
            'current_volume': 120000000,  # Volume spike
            'recent_avg_volume': 85000000,
            'current_price': 442.50,
            'recent_prices': [440.0, 441.0, 439.5, 442.0, 441.5],
            'bid_volume': 4500000,
            'ask_volume': 3800000,
            'time_since_anomaly': 3
        },
        {
            'market_name': 'BTC',
            'market_type': 'crypto',
            'current_volume': 45000000,  # Volume spike
            'recent_avg_volume': 25000000,
            'current_price': 48500.0,
            'recent_prices': [48000.0, 48200.0, 47800.0, 48400.0, 48100.0],
            'bid_volume': 1250000,
            'ask_volume': 1450000,
            'time_since_anomaly': 5
        },
        {
            'market_name': 'KALSHI',
            'market_type': 'prediction_market',
            'current_volume': 800000,  # Volume spike
            'recent_avg_volume': 500000,
            'current_price': 0.65,
            'recent_prices': [0.62, 0.63, 0.61, 0.64, 0.63],
            'bid_volume': 25000,
            'ask_volume': 18000,
            'time_since_anomaly': 8
        },
        {
            'market_name': 'SMALL_CAP',
            'market_type': 'equity',
            'current_volume': 800000,  # Volume spike
            'recent_avg_volume': 250000,
            'current_price': 45.20,
            'recent_prices': [44.8, 45.1, 44.6, 45.3, 44.9],
            'bid_volume': 15000,
            'ask_volume': 22000,
            'time_since_anomaly': 2
        }
    ]

    print("\n📊 ANALYZING MICROSTRUCTURE FOR SHORT-TERM EDGES:")
    for opportunity in test_opportunities:
        print(f"\n📊 MARKET: {opportunity['market_name']} ({opportunity['market_type']})")
        print(f"   Volume: {opportunity['current_volume']:,.0f} vs Avg: {opportunity['recent_avg_volume']:,.0f}")
        print(f"   Price: {opportunity['current_price']}")

        # Analyze the microstructure opportunity
        analysis = engine.analyze_microstructure_opportunity(opportunity)

        if analysis:
            print("   ✅ MICROSTRUCTURE ANALYSIS COMPLETE")
            print(f"   Anomaly: {analysis.anomaly_type} (strength: {analysis.anomaly_strength:.1f}σ)")
            print(f"   Reversion: {analysis.reversion_probability:.1%} within {analysis.reversion_speed_minutes:.0f} minutes")
            print(f"   Easy Trade Confidence: {analysis.easy_trade_confidence:.1%}")

            if analysis.easy_trade_confidence > 0.75:
                print("   🎯 EASY MICROSTRUCTURE TRADE OPPORTUNITY! 🎯")
                print(f"   Recommended: {analysis.recommended_action}")
            else:
                print("   ❓ Standard market conditions")

            print(f"   Rationale: {analysis.rationale}")
        else:
            print("   ❌ No microstructure profile for this market")

        print("-" * 70)

    # Show easy microstructure trades
    print("\n🎯 EASY MICROSTRUCTURE TRADES (75%+ confidence):")
    easy_trades = engine.get_easy_microstructure_trades()

    if easy_trades:
        for i, trade in enumerate(easy_trades, 1):
            print(f"{i}. {trade['market']} ({trade['market_type']}): {trade['confidence']:.1%} confidence")
            print(f"   Anomaly: {trade['anomaly_type']} ({trade['anomaly_strength']:.1f}σ)")
            print(f"   Reversion: {trade['reversion_probability']:.1%} in {trade['reversion_speed']:.0f} minutes")
            print(f"   {trade['recommended_action']}")
            print(f"   Rationale: {trade['rationale'][:100]}...")
            print()
    else:
        print("No easy microstructure trades found with current thresholds")

    print("\n✅ Microstructure Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_microstructure_engine())
