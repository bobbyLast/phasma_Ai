"""
🎯 IMPLIED VS REALIZED VOLATILITY EDGE ENGINE

Core options trading edge detection system that continuously compares:
- Implied Volatility (IV) from options prices
- Realized Volatility (RV) from actual price movements

Identifies when options are overpriced/underpriced relative to actual market movement,
providing the foundation for all options trading strategies.

Features:
- Real-time IV vs RV comparison per ticker
- Historical IV/RV ratio tracking
- Edge signals for premium buying/selling
- Volatility regime detection
- Options strategy recommendations based on IV/RV discrepancies
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
import numpy as np

from core.runtime_paths import engine_state_path

try:
    from engines.kalshi_engine import KalshiPredictionEngine
except ImportError:
    class KalshiPredictionEngine:
        pass


@dataclass
class VolatilityData:
    """Tracks volatility data for a ticker."""
    ticker: str
    implied_volatility: float = 0.0
    realized_volatility: float = 0.0
    iv_rv_ratio: float = 1.0
    historical_iv: List[float] = field(default_factory=list)
    historical_rv: List[float] = field(default_factory=list)
    historical_ratios: List[float] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)

    def update_iv(self, iv: float):
        """Update implied volatility."""
        self.implied_volatility = iv
        self._update_ratio()
        self._add_to_history('iv', iv)
        self.last_updated = datetime.now()

    def update_rv(self, rv: float):
        """Update realized volatility."""
        self.realized_volatility = rv
        self._update_ratio()
        self._add_to_history('rv', rv)
        self.last_updated = datetime.now()

    def _update_ratio(self):
        """Update IV/RV ratio."""
        if self.realized_volatility > 0:
            self.iv_rv_ratio = self.implied_volatility / self.realized_volatility
        else:
            self.iv_rv_ratio = 1.0

    def _add_to_history(self, vol_type: str, value: float):
        """Add value to historical data."""
        if vol_type == 'iv':
            self.historical_iv.append(value)
            # Keep last 100 data points
            if len(self.historical_iv) > 100:
                self.historical_iv.pop(0)
        elif vol_type == 'rv':
            self.historical_rv.append(value)
            if len(self.historical_rv) > 100:
                self.historical_rv.pop(0)

        # Update ratio history
        if len(self.historical_iv) > 0 and len(self.historical_rv) > 0:
            # Use most recent values for ratio
            recent_iv = self.historical_iv[-1]
            recent_rv = self.historical_rv[-1]
            if recent_rv > 0:
                ratio = recent_iv / recent_rv
                self.historical_ratios.append(ratio)
                if len(self.historical_ratios) > 100:
                    self.historical_ratios.pop(0)

    def get_iv_rv_percentile(self) -> float:
        """Get current IV/RV ratio percentile vs history."""
        if not self.historical_ratios:
            return 0.5

        current_ratio = self.iv_rv_ratio
        ratios_sorted = sorted(self.historical_ratios)

        # Find percentile
        for i, ratio in enumerate(ratios_sorted):
            if current_ratio <= ratio:
                return i / len(ratios_sorted)

        return 1.0

    def get_volatility_regime(self) -> str:
        """Determine current volatility regime."""
        percentile = self.get_iv_rv_percentile()

        if percentile > 0.8:
            return "high_iv_premium"  # IV much higher than RV - sell premium
        elif percentile > 0.6:
            return "elevated_iv"  # IV higher than normal - consider spreads
        elif percentile < 0.2:
            return "low_iv_discount"  # IV much lower than RV - buy premium
        elif percentile < 0.4:
            return "low_iv"  # IV lower than normal - consider outright positions
        else:
            return "neutral_iv"  # IV around historical average

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ticker': self.ticker,
            'implied_volatility': self.implied_volatility,
            'realized_volatility': self.realized_volatility,
            'iv_rv_ratio': self.iv_rv_ratio,
            'iv_rv_percentile': self.get_iv_rv_percentile(),
            'volatility_regime': self.get_volatility_regime(),
            'historical_data_points': len(self.historical_iv),
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class VolatilityEdgeSignal:
    """Signal for volatility edge opportunity."""
    ticker: str
    signal_type: str  # 'buy_premium', 'sell_premium', 'neutral'
    confidence: float  # 0.0 to 1.0
    iv_rv_ratio: float
    percentile: float
    regime: str
    recommended_strategy: str
    rationale: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ticker': self.ticker,
            'signal_type': self.signal_type,
            'confidence': self.confidence,
            'iv_rv_ratio': self.iv_rv_ratio,
            'percentile': self.percentile,
            'regime': self.regime,
            'recommended_strategy': self.recommended_strategy,
            'rationale': self.rationale,
            'timestamp': self.timestamp.isoformat()
        }


class ImpliedRealizedVolatilityEdgeEngine:
    """
    🎯 Implied vs Realized Volatility Edge Engine

    The foundation of options trading success - continuously monitors when options
    are overpriced or underpriced relative to actual market volatility.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine):
        self.kalshi = kalshi_engine
        self.volatility_data: Dict[str, VolatilityData] = {}
        self.edge_signals: List[VolatilityEdgeSignal] = []

        self.data_file = engine_state_path("volatility_edge_data.json")
        self.signals_file = engine_state_path("volatility_edge_signals.json")

        # Default tickers to monitor (expandable)
        self.monitored_tickers = {
            'SPY', 'QQQ', 'TSLA', 'AAPL', 'NVDA', 'MSFT', 'AMZN', 'META',
            'TSM', 'GOOGL', 'NFLX', 'AMD', 'INTC', 'BA', 'XOM', 'JPM'
        }

        # Initialize data for monitored tickers
        for ticker in self.monitored_tickers:
            self.volatility_data[ticker] = VolatilityData(ticker=ticker)

        self._load_data()

    def _load_data(self):
        """Load existing volatility data."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                for ticker_data in data.get('volatility_data', []):
                    ticker = ticker_data['ticker']
                    if ticker in self.monitored_tickers:
                        vol_data = self.volatility_data[ticker]
                        vol_data.implied_volatility = ticker_data.get('implied_volatility', 0.0)
                        vol_data.realized_volatility = ticker_data.get('realized_volatility', 0.0)
                        vol_data.historical_iv = ticker_data.get('historical_iv', [])
                        vol_data.historical_rv = ticker_data.get('historical_rv', [])
                        vol_data.last_updated = datetime.fromisoformat(ticker_data.get('last_updated', datetime.now().isoformat()))
                        vol_data._update_ratio()
                print(f"📊 Loaded volatility data for {len(self.volatility_data)} tickers")
            except Exception as e:
                print(f"⚠️ Error loading volatility data: {e}")

    def _save_data(self):
        """Save current volatility data."""
        data = {
            'volatility_data': [vol_data.to_dict() for vol_data in self.volatility_data.values()],
            'last_updated': datetime.now().isoformat()
        }

        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def update_implied_volatility(self, ticker: str, iv: float):
        """Update implied volatility for a ticker."""
        if ticker not in self.volatility_data:
            self.volatility_data[ticker] = VolatilityData(ticker=ticker)

        self.volatility_data[ticker].update_iv(iv)
        self._save_data()

        # Check for edge signal
        self._check_for_edge_signal(ticker)

    def update_realized_volatility(self, ticker: str, rv: float):
        """Update realized volatility for a ticker."""
        if ticker not in self.volatility_data:
            self.volatility_data[ticker] = VolatilityData(ticker=ticker)

        self.volatility_data[ticker].update_rv(rv)
        self._save_data()

        # Check for edge signal
        self._check_for_edge_signal(ticker)

    def _check_for_edge_signal(self, ticker: str):
        """Check if current volatility data creates an edge signal."""
        if ticker not in self.volatility_data:
            return

        vol_data = self.volatility_data[ticker]

        # Need some historical data for meaningful signals
        if len(vol_data.historical_ratios) < 10:
            return

        percentile = vol_data.get_iv_rv_percentile()
        regime = vol_data.get_volatility_regime()

        # Generate signal based on percentile and regime
        signal_type = 'neutral'
        confidence = 0.5
        recommended_strategy = 'monitor'

        if percentile > 0.85:  # Very high IV vs RV
            signal_type = 'sell_premium'
            confidence = min((percentile - 0.85) * 5, 0.9)  # Scale confidence
            recommended_strategy = self._get_sell_premium_strategy(ticker, vol_data.implied_volatility)

        elif percentile < 0.15:  # Very low IV vs RV
            signal_type = 'buy_premium'
            confidence = min((0.15 - percentile) * 5, 0.9)  # Scale confidence
            recommended_strategy = self._get_buy_premium_strategy(ticker, vol_data.implied_volatility)

        elif percentile > 0.7:  # Moderately high IV
            signal_type = 'sell_premium'
            confidence = 0.6
            recommended_strategy = self._get_sell_premium_strategy(ticker, vol_data.implied_volatility)

        elif percentile < 0.3:  # Moderately low IV
            signal_type = 'buy_premium'
            confidence = 0.6
            recommended_strategy = self._get_buy_premium_strategy(ticker, vol_data.implied_volatility)

        # Create signal if confidence is meaningful
        if confidence > 0.5:
            signal = VolatilityEdgeSignal(
                ticker=ticker,
                signal_type=signal_type,
                confidence=confidence,
                iv_rv_ratio=vol_data.iv_rv_ratio,
                percentile=percentile,
                regime=regime,
                recommended_strategy=recommended_strategy,
                rationale=self._generate_signal_rationale(signal_type, percentile, vol_data)
            )

            self.edge_signals.append(signal)

            # Keep only recent signals (last 100)
            if len(self.edge_signals) > 100:
                self.edge_signals.pop(0)

            self._save_signals()

    def _get_sell_premium_strategy(self, ticker: str, iv: float) -> str:
        """Get recommended strategy when IV is high (sell premium)."""
        if iv > 0.8:  # Very high IV
            return f"Sell cash-secured puts or covered calls on {ticker}"
        elif iv > 0.5:  # Moderately high IV
            return f"Sell credit spreads or iron condors on {ticker}"
        else:
            return f"Sell short-term options on {ticker}"

    def _get_buy_premium_strategy(self, ticker: str, iv: float) -> str:
        """Get recommended strategy when IV is low (buy premium)."""
        if iv < 0.2:  # Very low IV
            return f"Buy long-term calls/puts or buy premium on {ticker}"
        else:  # Moderately low IV
            return f"Buy debit spreads or consider outright positions on {ticker}"

    def _generate_signal_rationale(self, signal_type: str, percentile: float, vol_data: VolatilityData) -> str:
        """Generate rationale for the volatility edge signal."""
        if signal_type == 'sell_premium':
            if percentile > 0.85:
                return f"Extremely high IV ({vol_data.implied_volatility:.1%}) vs RV ({vol_data.realized_volatility:.1%}) - options significantly overpriced"
            else:
                return f"IV ({vol_data.implied_volatility:.1%}) elevated vs historical norms - favorable risk/reward for premium selling"
        elif signal_type == 'buy_premium':
            if percentile < 0.15:
                return f"Extremely low IV ({vol_data.implied_volatility:.1%}) vs RV ({vol_data.realized_volatility:.1%}) - options significantly underpriced"
            else:
                return f"IV ({vol_data.implied_volatility:.1%}) below historical norms - favorable risk/reward for premium buying"
        else:
            return f"IV/RV ratio near historical average - monitor for changes"

    def get_current_edge_signals(self, min_confidence: float = 0.6) -> List[VolatilityEdgeSignal]:
        """Get current edge signals above minimum confidence."""
        return [signal for signal in self.edge_signals[-20:]  # Last 20 signals
                if signal.confidence >= min_confidence]

    def get_ticker_volatility_analysis(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive volatility analysis for a ticker."""
        if ticker not in self.volatility_data:
            return None

        vol_data = self.volatility_data[ticker]
        analysis = vol_data.to_dict()

        # Add additional analysis
        analysis.update({
            'avg_historical_iv': statistics.mean(vol_data.historical_iv) if vol_data.historical_iv else 0,
            'avg_historical_rv': statistics.mean(vol_data.historical_rv) if vol_data.historical_rv else 0,
            'iv_volatility': statistics.stdev(vol_data.historical_iv) if len(vol_data.historical_iv) > 1 else 0,
            'rv_volatility': statistics.stdev(vol_data.historical_rv) if len(vol_data.historical_rv) > 1 else 0,
            'edge_signals_count': len([s for s in self.edge_signals if s.ticker == ticker])
        })

        return analysis

    def get_market_volatility_regime(self) -> Dict[str, Any]:
        """Get overall market volatility regime across all tickers."""
        if not self.volatility_data:
            return {'regime': 'unknown', 'description': 'No data available'}

        # Aggregate across major indices and stocks
        major_tickers = {'SPY', 'QQQ'}
        major_data = [self.volatility_data[t] for t in major_tickers if t in self.volatility_data]

        if not major_data:
            return {'regime': 'unknown', 'description': 'No major ticker data'}

        # Calculate market-level metrics
        avg_iv_percentile = statistics.mean([d.get_iv_rv_percentile() for d in major_data])
        avg_iv = statistics.mean([d.implied_volatility for d in major_data])

        if avg_iv_percentile > 0.8:
            regime = 'high_volatility_premium_sell'
            description = f'Market IV significantly elevated ({avg_iv:.1%}) - strong environment for premium selling'
        elif avg_iv_percentile > 0.6:
            regime = 'elevated_volatility'
            description = f'Market IV above average ({avg_iv:.1%}) - favorable for defined-risk strategies'
        elif avg_iv_percentile < 0.2:
            regime = 'low_volatility_premium_buy'
            description = f'Market IV significantly depressed - potential for premium buying opportunities'
        elif avg_iv_percentile < 0.4:
            regime = 'low_volatility'
            description = f'Market IV below average - consider outright directional positions'
        else:
            regime = 'neutral_volatility'
            description = f'Market IV near historical average ({avg_iv:.1%})'

        return {
            'regime': regime,
            'description': description,
            'average_iv_percentile': avg_iv_percentile,
            'average_iv': avg_iv,
            'tickers_analyzed': len(major_data)
        }

    def generate_volatility_edge_report(self) -> str:
        """Generate a comprehensive volatility edge report."""
        report_parts = []

        report_parts.append("🎯 VOLATILITY EDGE ENGINE REPORT")
        report_parts.append("=" * 50)
        report_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_parts.append("")

        # Market regime
        market_regime = self.get_market_volatility_regime()
        report_parts.append("🌍 MARKET VOLATILITY REGIME:")
        report_parts.append(f"Regime: {market_regime['regime'].replace('_', ' ').title()}")
        report_parts.append(f"Description: {market_regime['description']}")
        report_parts.append(f"Average IV: {market_regime['average_iv']:.1%}")
        report_parts.append("")

        # Current edge signals
        current_signals = self.get_current_edge_signals(min_confidence=0.6)
        if current_signals:
            report_parts.append("🎯 CURRENT VOLATILITY EDGE SIGNALS:")
            for signal in current_signals[-5:]:  # Show last 5
                report_parts.append(f"• {signal.ticker}: {signal.signal_type.upper()} ({signal.confidence:.1%} confidence)")
                report_parts.append(f"  Strategy: {signal.recommended_strategy}")
                report_parts.append(f"  Rationale: {signal.rationale}")
                report_parts.append("")
        else:
            report_parts.append("🎯 No high-confidence edge signals currently")
            report_parts.append("")

        # Top tickers by edge opportunity
        ticker_analysis = []
        for ticker in self.monitored_tickers:
            analysis = self.get_ticker_volatility_analysis(ticker)
            if analysis and len(analysis.get('historical_ratios', [])) >= 10:
                edge_score = abs(analysis['iv_rv_percentile'] - 0.5) * 2  # 0-1 scale
                ticker_analysis.append((ticker, edge_score, analysis))

        ticker_analysis.sort(key=lambda x: x[1], reverse=True)

        if ticker_analysis:
            report_parts.append("🏆 TOP TICKERS BY EDGE OPPORTUNITY:")
            for ticker, score, analysis in ticker_analysis[:5]:
                regime = analysis['volatility_regime'].replace('_', ' ').title()
                report_parts.append(f"• {ticker}: {regime} (IV/RV: {analysis['iv_rv_ratio']:.2f})")
            report_parts.append("")

        report_parts.append("🤖 Volatility Edge Engine - Finding Options Mispricings")

        return "\n".join(report_parts)

    def _save_signals(self):
        """Save edge signals to file."""
        signals_data = {
            'signals': [signal.to_dict() for signal in self.edge_signals],
            'last_updated': datetime.now().isoformat()
        }

        with open(self.signals_file, 'w') as f:
            json.dump(signals_data, f, indent=2)


# Test/demo functions
async def test_volatility_edge_engine():
    """Test the implied vs realized volatility edge engine."""
    print("🎯 TESTING IMPLIED VS REALIZED VOLATILITY EDGE ENGINE")
    print("=" * 60)

    # Mock kalshi engine
    kalshi = KalshiPredictionEngine()
    engine = ImpliedRealizedVolatilityEdgeEngine(kalshi)

    print(f"🎯 Initialized with {len(engine.volatility_data)} monitored tickers")

    # Simulate some volatility data and signals
    test_data = [
        # High IV scenario (sell premium opportunity)
        ("SPY", 0.25, 0.15),  # IV=25%, RV=15% - overpriced
        ("QQQ", 0.30, 0.18),  # IV=30%, RV=18% - overpriced
        ("TSLA", 0.80, 0.45),  # IV=80%, RV=45% - very overpriced

        # Low IV scenario (buy premium opportunity)
        ("AAPL", 0.18, 0.25),  # IV=18%, RV=25% - underpriced
        ("MSFT", 0.15, 0.22),  # IV=15%, RV=22% - underpriced

        # Neutral scenario
        ("NVDA", 0.35, 0.32),  # IV=35%, RV=32% - close to fair
    ]

    print("\n📊 SIMULATING VOLATILITY DATA:")
    for ticker, iv, rv in test_data:
        # Add some historical data first
        for _ in range(20):
            engine.update_implied_volatility(ticker, iv * (0.8 + 0.4 * np.random.random()))
            engine.update_realized_volatility(ticker, rv * (0.8 + 0.4 * np.random.random()))

        # Set current values
        engine.update_implied_volatility(ticker, iv)
        engine.update_realized_volatility(ticker, rv)

        vol_data = engine.volatility_data[ticker]
        print(f"✅ {ticker}: IV={iv:.1%}, RV={rv:.1%}, Ratio={vol_data.iv_rv_ratio:.2f}, Regime={vol_data.get_volatility_regime()}")

    # Check for edge signals
    print("\n🎯 GENERATED EDGE SIGNALS:")
    signals = engine.get_current_edge_signals(min_confidence=0.5)
    for signal in signals:
        print(f"🎯 {signal.ticker}: {signal.signal_type.upper()} ({signal.confidence:.1%})")
        print(f"   Strategy: {signal.recommended_strategy}")
        print(f"   Rationale: {signal.rationale}")
        print()

    # Market regime
    print("🌍 MARKET VOLATILITY REGIME:")
    regime = engine.get_market_volatility_regime()
    print(f"Regime: {regime['regime']}")
    print(f"Description: {regime['description']}")
    print()

    # Generate report
    print("📋 COMPREHENSIVE VOLATILITY EDGE REPORT:")
    print("-" * 45)
    report = engine.generate_volatility_edge_report()
    print(report)

    print("\n✅ Implied vs Realized Volatility Edge Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_volatility_edge_engine())
