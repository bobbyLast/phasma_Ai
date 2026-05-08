"""
🎯 DYNAMIC STRIKE & EXPIRY SELECTOR

Advanced options positioning engine that automatically selects optimal:
- Strike prices based on directional bias and expected move
- Expiration dates based on catalyst timing and theta decay
- Position sizing based on edge strength and risk parameters

Considers:
- Catalyst timing and strength
- Implied volatility levels and skew
- Bid-ask spreads and liquidity
- Expected move magnitude
- Risk/reward profile
- Theta vs directional edge balance

This is the "secret sauce" of options trading - wrong strike/expiry = guaranteed losses.
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
from dateutil.relativedelta import relativedelta

try:
    from engines.volatility_edge_engine import ImpliedRealizedVolatilityEdgeEngine, VolatilityData
    from engines.kalshi_engine import KalshiPredictionEngine
except ImportError:
    # Mocks for testing
    class ImpliedRealizedVolatilityEdgeEngine:
        def __init__(self, *args, **kwargs):
            pass
        def get_ticker_volatility_analysis(self, ticker: str) -> Optional[Dict[str, Any]]:
            return {'implied_volatility': 0.3, 'volatility_regime': 'neutral'}
    class VolatilityData:
        pass
    class KalshiPredictionEngine:
        def __init__(self, *args, **kwargs):
            pass


@dataclass
class CatalystInfo:
    """Information about the catalyst driving the options trade."""
    catalyst_type: str  # 'earnings', 'fed_meeting', 'product_launch', 'macro_event', etc.
    timing: str  # 'immediate', 'short_term', 'medium_term', 'long_term'
    strength: float  # 0.0 to 1.0 - how strong/predictable is the catalyst
    expected_move_pct: float  # Expected price move percentage
    confidence: float  # 0.0 to 1.0 - confidence in catalyst prediction
    time_to_catalyst: int  # Days until catalyst occurs
    directional_bias: str  # 'bullish', 'bearish', 'neutral'

    def get_optimal_dte_range(self) -> Tuple[int, int]:
        """Get optimal days-to-expiry range for this catalyst."""
        if self.timing == 'immediate' or self.time_to_catalyst <= 7:
            return (1, 21)  # Very short-term options
        elif self.timing == 'short_term' or self.time_to_catalyst <= 30:
            return (7, 45)  # Short-term options
        elif self.timing == 'medium_term' or self.time_to_catalyst <= 90:
            return (30, 90)  # Medium-term options
        else:  # long_term
            return (60, 180)  # Longer-dated options


@dataclass
class OptionsChainData:
    """Simplified options chain data structure."""
    ticker: str
    spot_price: float
    options: List[Dict[str, Any]] = field(default_factory=list)  # List of option contracts

    def get_options_by_expiry(self, expiry_date: str) -> List[Dict[str, Any]]:
        """Get options for a specific expiry date."""
        return [opt for opt in self.options if opt.get('expiry') == expiry_date]

    def get_strikes_for_expiry(self, expiry_date: str) -> List[float]:
        """Get available strikes for an expiry."""
        options = self.get_options_by_expiry(expiry_date)
        strikes = set()
        for opt in options:
            strikes.add(opt.get('strike', 0))
        return sorted(list(strikes))

    def get_option_by_strike_expiry(self, strike: float, expiry: str, option_type: str) -> Optional[Dict[str, Any]]:
        """Get specific option contract."""
        for opt in self.options:
            if (opt.get('strike') == strike and
                opt.get('expiry') == expiry and
                opt.get('type') == option_type):
                return opt
        return None


@dataclass
class StrikeExpiryRecommendation:
    """Recommended strike and expiry for an options trade."""
    ticker: str
    option_type: str  # 'call', 'put'
    strike_price: float
    expiry_date: str
    days_to_expiry: int
    delta: float
    premium: float
    bid_ask_spread_pct: float
    liquidity_score: float  # 0.0 to 1.0
    edge_score: float  # 0.0 to 1.0 - how good this choice is
    rationale: str
    risk_reward_ratio: float
    breakeven_price: float
    max_loss: float
    max_profit: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ticker': self.ticker,
            'option_type': self.option_type,
            'strike_price': self.strike_price,
            'expiry_date': self.expiry_date,
            'days_to_expiry': self.days_to_expiry,
            'delta': self.delta,
            'premium': self.premium,
            'bid_ask_spread_pct': self.bid_ask_spread_pct,
            'liquidity_score': self.liquidity_score,
            'edge_score': self.edge_score,
            'rationale': self.rationale,
            'risk_reward_ratio': self.risk_reward_ratio,
            'breakeven_price': self.breakeven_price,
            'max_loss': self.max_loss,
            'max_profit': self.max_profit
        }


class DynamicStrikeExpirySelector:
    """
    🎯 Dynamic Strike & Expiry Selector

    The critical "secret sauce" of options trading - automatically finds the optimal
    strike and expiration for maximum edge given the catalyst, volatility, and market conditions.
    """

    def __init__(self, volatility_engine: ImpliedRealizedVolatilityEdgeEngine,
                 kalshi_engine: KalshiPredictionEngine):
        self.volatility_engine = volatility_engine
        self.kalshi = kalshi_engine

        # Standard expiration dates (would be pulled from broker API in production)
        self.standard_expiries = self._generate_standard_expiries()

        self.recommendations_file = "strike_expiry_recommendations.json"
        self._load_data()

    def _generate_standard_expiries(self) -> List[Tuple[str, int]]:
        """Generate standard options expiry dates with DTE."""
        expiries = []
        today = datetime.now()

        # Weekly expiries (Fridays)
        for weeks in range(1, 5):
            expiry = today + timedelta(days=(4 - today.weekday() + 7 * weeks) % 7)
            dte = (expiry - today).days
            expiries.append((expiry.strftime('%Y-%m-%d'), dte))

        # Monthly expiries
        for months in range(1, 7):
            expiry = today + relativedelta(months=months)
            # Find Friday closest to month end
            last_day = expiry.replace(day=1) + relativedelta(months=1, days=-1)
            expiry = last_day - timedelta(days=(last_day.weekday() - 4) % 7)
            dte = (expiry - today).days
            expiries.append((expiry.strftime('%Y-%m-%d'), dte))

        return expiries

    def _load_data(self):
        """Load existing recommendation data."""
        if os.path.exists(self.recommendations_file):
            try:
                with open(self.recommendations_file, 'r') as f:
                    data = json.load(f)
                print(f"📊 Loaded strike/expiry recommendations: {len(data.get('recommendations', {}))} entries")
            except Exception as e:
                print(f"⚠️ Error loading recommendations: {e}")

    def select_optimal_strike_expiry(self, ticker: str, catalyst: CatalystInfo,
                                   directional_bias: str, position_size: float = 1000) -> Optional[StrikeExpiryRecommendation]:
        """
        Select the optimal strike and expiry for an options trade.

        Args:
            ticker: Stock ticker
            catalyst: Information about the driving catalyst
            directional_bias: 'bullish', 'bearish', or 'neutral'
            position_size: Desired position size in dollars

        Returns:
            Optimal strike/expiry recommendation
        """

        # Get volatility analysis
        vol_analysis = self.volatility_engine.get_ticker_volatility_analysis(ticker)
        if not vol_analysis:
            return None

        current_iv = vol_analysis.get('implied_volatility', 0.3)
        spot_price = self._get_current_price(ticker)  # Mock in testing

        # Determine optimal DTE range
        min_dte, max_dte = catalyst.get_optimal_dte_range()

        # Filter available expiries
        suitable_expiries = [(exp, dte) for exp, dte in self.standard_expiries
                           if min_dte <= dte <= max_dte]

        if not suitable_expiries:
            return None

        # Score each expiry + strike combination
        best_score = -1
        best_recommendation = None

        for expiry_date, dte in suitable_expiries:
            strikes = self._generate_strike_ladder(ticker, spot_price, catalyst, directional_bias)

            for strike in strikes:
                recommendation = self._evaluate_strike_expiry_combination(
                    ticker, strike, expiry_date, dte, catalyst, directional_bias,
                    current_iv, spot_price, position_size
                )

                if recommendation and recommendation.edge_score > best_score:
                    best_score = recommendation.edge_score
                    best_recommendation = recommendation

        return best_recommendation

    def _generate_strike_ladder(self, ticker: str, spot_price: float, catalyst: CatalystInfo,
                               directional_bias: str) -> List[float]:
        """Generate appropriate strike prices to consider."""
        strikes = []

        # Base strikes around current price
        base_strikes = [spot_price * (1 + pct/100) for pct in range(-50, 51, 5)]

        # Adjust based on catalyst expected move
        expected_move_pct = catalyst.expected_move_pct

        if directional_bias == 'bullish':
            # Focus on OTM calls with some ITM protection
            min_strike = spot_price * (1 - expected_move_pct * 0.5)
            max_strike = spot_price * (1 + expected_move_pct * 2)
        elif directional_bias == 'bearish':
            # Focus on OTM puts with some ITM protection
            min_strike = spot_price * (1 - expected_move_pct * 2)
            max_strike = spot_price * (1 + expected_move_pct * 0.5)
        else:  # neutral
            # ATM and close strikes for theta strategies
            min_strike = spot_price * 0.9
            max_strike = spot_price * 1.1

        # Filter to reasonable range
        filtered_strikes = [s for s in base_strikes if min_strike <= s <= max_strike]

        # Add some standard strikes
        for strike in [round(spot_price * (1 + i/20), 2) for i in range(-10, 11)]:
            if strike not in filtered_strikes:
                filtered_strikes.append(strike)

        return sorted(filtered_strikes)

    def _evaluate_strike_expiry_combination(self, ticker: str, strike: float, expiry: str, dte: int,
                                          catalyst: CatalystInfo, directional_bias: str,
                                          current_iv: float, spot_price: float, position_size: float) -> Optional[StrikeExpiryRecommendation]:
        """Evaluate a specific strike/expiry combination."""

        # Determine option type
        if directional_bias == 'bullish':
            option_type = 'call'
        elif directional_bias == 'bearish':
            option_type = 'put'
        else:
            # For neutral strategies, use calls for simplicity
            option_type = 'call'

        # Estimate option metrics (simplified Black-Scholes approximation)
        time_to_expiry = dte / 365.0
        risk_free_rate = 0.05  # Assume 5%

        # Simplified option pricing and Greeks
        option_metrics = self._calculate_option_metrics(
            spot_price, strike, time_to_expiry, current_iv, risk_free_rate, option_type
        )

        if not option_metrics:
            return None

        premium = option_metrics['premium']
        delta = option_metrics['delta']
        bid_ask_spread_pct = option_metrics['spread_pct']
        liquidity_score = option_metrics['liquidity']

        # Calculate edge score
        edge_score = self._calculate_edge_score(
            strike, spot_price, premium, dte, catalyst, directional_bias,
            current_iv, bid_ask_spread_pct, liquidity_score, delta
        )

        # Calculate risk/reward
        if option_type == 'call':
            if directional_bias == 'bullish':
                max_loss = premium * position_size / 100  # Assuming 100 shares per contract
                max_profit = float('inf') if catalyst.expected_move_pct > 0.1 else (spot_price * (1 + catalyst.expected_move_pct) - strike - premium) * position_size / 100
                breakeven = strike + premium
            else:  # neutral/bearish call (selling)
                max_loss = float('inf')
                max_profit = premium * position_size / 100
                breakeven = strike + premium
        else:  # put
            if directional_bias == 'bearish':
                max_loss = premium * position_size / 100
                max_profit = float('inf') if catalyst.expected_move_pct > 0.1 else (strike - spot_price * (1 - catalyst.expected_move_pct) - premium) * position_size / 100
                breakeven = strike - premium
            else:  # neutral/bullish put (selling)
                max_loss = float('inf')
                max_profit = premium * position_size / 100
                breakeven = strike - premium

        risk_reward_ratio = max_profit / max_loss if max_loss > 0 else float('inf')

        # Generate rationale
        rationale = self._generate_recommendation_rationale(
            ticker, strike, expiry, dte, catalyst, directional_bias, edge_score
        )

        recommendation = StrikeExpiryRecommendation(
            ticker=ticker,
            option_type=option_type,
            strike_price=strike,
            expiry_date=expiry,
            days_to_expiry=dte,
            delta=delta,
            premium=premium,
            bid_ask_spread_pct=bid_ask_spread_pct,
            liquidity_score=liquidity_score,
            edge_score=edge_score,
            rationale=rationale,
            risk_reward_ratio=risk_reward_ratio,
            breakeven_price=breakeven,
            max_loss=max_loss,
            max_profit=max_profit if max_profit != float('inf') else 999999
        )

        return recommendation

    def _calculate_option_metrics(self, spot: float, strike: float, time: float,
                                iv: float, rate: float, option_type: str) -> Optional[Dict[str, Any]]:
        """Calculate simplified option metrics."""
        # Simplified option pricing (would use proper Black-Scholes in production)

        # Basic intrinsic value
        if option_type == 'call':
            intrinsic = max(0, spot - strike)
        else:
            intrinsic = max(0, strike - spot)

        # Time value (simplified)
        moneyness = abs(spot - strike) / spot
        time_value = spot * iv * math.sqrt(time) * (1 - moneyness)

        premium = intrinsic + time_value

        # Simplified delta
        if option_type == 'call':
            delta = min(1.0, max(0.0, (spot - strike) / (spot * iv * math.sqrt(time) * 2) + 0.5))
        else:
            delta = min(1.0, max(0.0, (strike - spot) / (spot * iv * math.sqrt(time) * 2) + 0.5))

        # Mock other metrics
        spread_pct = 0.05 + (moneyness * 0.1)  # Wider spreads for OTM options
        liquidity = max(0.1, 1.0 - moneyness - spread_pct)  # Better liquidity for ATM

        return {
            'premium': premium,
            'delta': delta,
            'spread_pct': spread_pct,
            'liquidity': liquidity
        }

    def _calculate_edge_score(self, strike: float, spot: float, premium: float, dte: int,
                            catalyst: CatalystInfo, directional_bias: str, current_iv: float,
                            spread_pct: float, liquidity: float, delta: float) -> float:
        """Calculate overall edge score for this strike/expiry combination."""

        score_components = []

        # Catalyst alignment (how well does this match the expected move?)
        expected_move_price = spot * (1 + catalyst.expected_move_pct if directional_bias == 'bullish'
                                    else 1 - catalyst.expected_move_pct)
        strike_distance_pct = abs(strike - expected_move_price) / spot

        if directional_bias in ['bullish', 'bearish']:
            catalyst_alignment = max(0, 1 - strike_distance_pct * 2)  # Prefer strikes near expected move
        else:
            catalyst_alignment = max(0, 1 - abs(strike - spot) / spot)  # Prefer ATM for neutral

        score_components.append(('catalyst_alignment', catalyst_alignment, 0.3))

        # Time alignment (does DTE match catalyst timing?)
        optimal_dte_min, optimal_dte_max = catalyst.get_optimal_dte_range()
        if optimal_dte_min <= dte <= optimal_dte_max:
            time_alignment = 1.0
        elif dte < optimal_dte_min:
            time_alignment = max(0, 1 - (optimal_dte_min - dte) / optimal_dte_min)
        else:
            time_alignment = max(0, 1 - (dte - optimal_dte_max) / optimal_dte_max)

        score_components.append(('time_alignment', time_alignment, 0.25))

        # Cost efficiency (premium vs expected edge)
        # Lower premium relative to potential payoff is better
        cost_efficiency = min(1.0, 1 / (1 + premium / spot * 10))  # Penalize high premium
        score_components.append(('cost_efficiency', cost_efficiency, 0.15))

        # Liquidity & execution quality
        execution_quality = (1 - spread_pct) * liquidity  # Better spreads and liquidity
        score_components.append(('execution_quality', execution_quality, 0.15))

        # Delta appropriateness (prefer reasonable delta based on strategy)
        if directional_bias in ['bullish', 'bearish']:
            # For directional trades, prefer delta 0.3-0.7
            delta_score = 1 - abs(delta - 0.5) * 2
        else:
            # For neutral trades, prefer delta 0.4-0.6
            delta_score = 1 - abs(delta - 0.5) * 4

        delta_score = max(0, delta_score)
        score_components.append(('delta_appropriateness', delta_score, 0.15))

        # Calculate weighted total
        total_score = sum(score * weight for _, score, weight in score_components)

        # Boost for high-confidence catalysts
        confidence_boost = catalyst.confidence * 0.1
        total_score = min(1.0, total_score + confidence_boost)

        return total_score

    def _generate_recommendation_rationale(self, ticker: str, strike: float, expiry: str, dte: int,
                                         catalyst: CatalystInfo, directional_bias: str, edge_score: float) -> str:
        """Generate rationale for the strike/expiry recommendation."""

        rationale_parts = []

        # Strike positioning
        spot = self._get_current_price(ticker)
        strike_pct = (strike - spot) / spot * 100

        if directional_bias == 'bullish':
            if strike_pct > catalyst.expected_move_pct * 100:
                rationale_parts.append(f"OTM call positioned above expected move ({strike_pct:.1f}% OTM)")
            else:
                rationale_parts.append(f"ITM/ATM call for conservative positioning ({strike_pct:.1f}% from spot)")
        elif directional_bias == 'bearish':
            if strike_pct < -catalyst.expected_move_pct * 100:
                rationale_parts.append(f"OTM put positioned below expected move ({strike_pct:.1f}% OTM)")
            else:
                rationale_parts.append(f"ITM/ATM put for conservative positioning ({strike_pct:.1f}% from spot)")
        else:
            rationale_parts.append(f"ATM positioning for theta strategy ({strike_pct:.1f}% from spot)")

        # Time positioning
        if dte <= 7:
            rationale_parts.append(f"Very short-term expiry ({dte} DTE) to capture immediate catalyst")
        elif dte <= 30:
            rationale_parts.append(f"Short-term expiry ({dte} DTE) balancing time decay and directional edge")
        elif dte <= 60:
            rationale_parts.append(f"Medium-term expiry ({dte} DTE) for sustained momentum")
        else:
            rationale_parts.append(f"Longer-term expiry ({dte} DTE) for thesis-driven positioning")

        # Edge justification
        if edge_score > 0.8:
            rationale_parts.append("Excellent edge alignment across catalyst, timing, and execution factors")
        elif edge_score > 0.6:
            rationale_parts.append("Good edge alignment with strong catalyst and timing fit")
        elif edge_score > 0.4:
            rationale_parts.append("Moderate edge with reasonable positioning")
        else:
            rationale_parts.append("Conservative positioning prioritizing risk management")

        return ". ".join(rationale_parts)

    def _get_current_price(self, ticker: str) -> float:
        """Get current price for ticker (mock implementation)."""
        # Mock prices - would integrate with real-time data feed
        mock_prices = {
            'SPY': 450.0, 'QQQ': 380.0, 'TSLA': 220.0, 'AAPL': 180.0,
            'NVDA': 850.0, 'MSFT': 380.0, 'AMZN': 145.0, 'META': 320.0,
            'TSM': 120.0, 'GOOGL': 140.0, 'NFLX': 450.0, 'AMD': 180.0
        }
        return mock_prices.get(ticker, 100.0)

    def get_multi_scenario_analysis(self, ticker: str, scenarios: List[CatalystInfo]) -> List[StrikeExpiryRecommendation]:
        """Analyze multiple catalyst scenarios for the same ticker."""

        recommendations = []
        for scenario in scenarios:
            for direction in ['bullish', 'bearish', 'neutral']:
                rec = self.select_optimal_strike_expiry(ticker, scenario, direction)
                if rec:
                    recommendations.append(rec)

        # Sort by edge score
        recommendations.sort(key=lambda x: x.edge_score, reverse=True)
        return recommendations[:5]  # Top 5 recommendations


# Test/demo functions
async def test_strike_expiry_selector():
    """Test the dynamic strike & expiry selector."""
    print("🎯 TESTING DYNAMIC STRIKE & EXPIRY SELECTOR")
    print("=" * 50)

    # Mock engines
    volatility_engine = ImpliedRealizedVolatilityEdgeEngine(None)
    kalshi = KalshiPredictionEngine()
    selector = DynamicStrikeExpirySelector(volatility_engine, kalshi)

    print(f"🎯 Initialized selector with {len(selector.standard_expiries)} expiry dates")

    # Test scenarios
    test_scenarios = [
        CatalystInfo(
            catalyst_type='earnings',
            timing='immediate',
            strength=0.8,
            expected_move_pct=0.08,  # 8% expected move
            confidence=0.75,
            time_to_catalyst=2,  # 2 days away
            directional_bias='bullish'
        ),
        CatalystInfo(
            catalyst_type='fed_meeting',
            timing='short_term',
            strength=0.9,
            expected_move_pct=0.05,  # 5% expected move
            confidence=0.8,
            time_to_catalyst=5,  # 5 days away
            directional_bias='neutral'
        ),
        CatalystInfo(
            catalyst_type='macro_event',
            timing='medium_term',
            strength=0.7,
            expected_move_pct=0.12,  # 12% expected move
            confidence=0.6,
            time_to_catalyst=30,  # 30 days away
            directional_bias='bearish'
        )
    ]

    print("\n📊 TESTING SCENARIO ANALYSIS:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🎭 Scenario {i}: {scenario.catalyst_type.upper()} - {scenario.directional_bias.upper()}")
        print(f"   Strength: {scenario.strength:.1%} | Expected Move: {scenario.expected_move_pct:.1%} | Time: {scenario.time_to_catalyst} days")

        # Test for different tickers
        for ticker in ['TSLA', 'NVDA', 'SPY']:
            recommendation = selector.select_optimal_strike_expiry(ticker, scenario, scenario.directional_bias)

            if recommendation:
                print(f"   ✅ {ticker}: ${recommendation.strike_price:.2f} {recommendation.option_type.upper()} expiring {recommendation.expiry_date} ({recommendation.days_to_expiry} DTE)")
                print(".2f")
                print(f"      → {recommendation.rationale}")
            else:
                print(f"   ❌ {ticker}: No suitable recommendation found")

    # Test multi-scenario analysis
    print("\n🔄 MULTI-SCENARIO ANALYSIS FOR NVDA:")
    multi_rec = selector.get_multi_scenario_analysis('NVDA', test_scenarios[:2])

    print("🏆 Top recommendations across scenarios:")
    for i, rec in enumerate(multi_rec, 1):
        print(f"   {i}. {rec.option_type.upper()} ${rec.strike_price:.2f} ({rec.days_to_expiry} DTE) - Edge: {rec.edge_score:.3f}")

    print("\n✅ Dynamic Strike & Expiry Selector test complete!")


if __name__ == "__main__":
    asyncio.run(test_strike_expiry_selector())
