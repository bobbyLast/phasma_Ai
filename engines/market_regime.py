"""
Phasma Market Regime Detection Engine
Detects market conditions (bull/bear/sideways) and adapts trading strategies
"""

import yfinance as yf
import numpy as np
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
import requests

try:
    from utils.market_data_cache import MarketDataCache
except ImportError:
    MarketDataCache = None

class PhasmaMarketRegimeDetector:
    """Detects market regime and adapts trading strategies accordingly"""

    def __init__(self, config, market_cache: Any = None):
        self.config = config
        self.market_cache = market_cache

        # VIX thresholds for regime detection
        self.vix_thresholds = {
            'low': 15,      # Low volatility regime
            'normal': 20,   # Normal volatility regime
            'high': 30      # High volatility regime
        }

        # Market index for trend analysis
        self.market_indices = ['SPY', 'QQQ', 'IWM']  # S&P 500, Nasdaq, Russell 2000

        # Regime detection parameters
        self.lookback_days = 20  # Days to analyze for regime detection
        self.volatility_window = 20  # Days for volatility calculation

        self.logger = logging.getLogger("PhasmaMarketRegime")

    def detect_current_regime(self) -> str:
        """Detect current market regime based on VIX and market trends"""
        try:
            # Get VIX data
            vix = self._get_current_vix()

            # Get market trend data
            market_trend = self._get_market_trend()

            # Get realized volatility
            realized_vol = self._get_realized_volatility()

            # Determine regime based on multiple factors
            regime = self._classify_regime(vix, market_trend, realized_vol)

            self.logger.info(f"Market regime detected: {regime} (VIX: {vix:.1f}, "
                           f"Trend: {market_trend:.1%}, Realized Vol: {realized_vol:.1%})")

            return regime

        except Exception as e:
            self.logger.error(f"Error detecting market regime: {e}")
            return 'normal'  # Default to normal regime

    def _cached_macro(self) -> Optional[Dict]:
        if self.market_cache and MarketDataCache:
            return self.market_cache.fetch_macro_data()
        return None

    def _get_current_vix(self) -> float:
        """Get current VIX level"""
        macro = self._cached_macro()
        if macro:
            vix_current = macro.get('vix', {}).get('current')
            if vix_current is not None and vix_current > 0:
                return float(vix_current)

        try:
            vix = yf.Ticker('^VIX')
            vix_data = vix.history(period='5d')
            closes = vix_data['Close'].dropna()
            if len(closes) > 0:
                return closes.iloc[-1]
        except Exception as e:
            self.logger.warning(f"Could not get VIX data: {e}")
        chart_closes = self._get_yahoo_chart_closes('^VIX')
        if chart_closes:
            return chart_closes[-1]
        return 20.0  # Default normal level

    def _get_market_trend(self) -> float:
        """Get overall market trend (positive = bullish, negative = bearish)"""
        if self.market_cache and MarketDataCache:
            try:
                hist = self.market_cache.fetch_history('SPY', '1mo')
                if hist is not None and len(hist) >= 2:
                    start_price = hist['Close'].iloc[0]
                    end_price = hist['Close'].iloc[-1]
                    return (end_price - start_price) / start_price
            except Exception as e:
                self.logger.debug(f"SPY trend from market cache failed: {e}")

        try:
            total_return = 0.0
            valid_indices = 0

            for index in self.market_indices:
                try:
                    ticker = yf.Ticker(index)
                    data = ticker.history(period='1mo')  # 1 month lookback

                    if len(data) >= 2:
                        start_price = data['Close'].iloc[0]
                        end_price = data['Close'].iloc[-1]
                        monthly_return = (end_price - start_price) / start_price
                        total_return += monthly_return
                        valid_indices += 1
                    else:
                        closes = self._get_yahoo_chart_closes(index)
                        if len(closes) >= 2:
                            start_price = closes[0]
                            end_price = closes[-1]
                            monthly_return = (end_price - start_price) / start_price
                            total_return += monthly_return
                            valid_indices += 1

                except Exception as e:
                    self.logger.warning(f"Could not get data for {index}: {e}")
                    closes = self._get_yahoo_chart_closes(index)
                    if len(closes) >= 2:
                        start_price = closes[0]
                        end_price = closes[-1]
                        monthly_return = (end_price - start_price) / start_price
                        total_return += monthly_return
                        valid_indices += 1
                    continue

            if valid_indices == 0:
                return 0.0  # Neutral if no data

            return total_return / valid_indices

        except Exception as e:
            self.logger.error(f"Error calculating market trend: {e}")
            return 0.0

    def _get_realized_volatility(self) -> float:
        """Calculate realized volatility of SPY"""
        if self.market_cache and MarketDataCache:
            try:
                data = self.market_cache.fetch_history('SPY', '3mo')
                if data is not None and len(data) >= 20:
                    daily_returns = data['Close'].pct_change().dropna()
                    return daily_returns.std() * np.sqrt(252)
            except Exception as e:
                self.logger.debug(f"SPY volatility from market cache failed: {e}")

        try:
            spy = yf.Ticker('SPY')
            data = spy.history(period='3mo')  # 3 months data

            if len(data) < 20:
                return 0.20  # Default 20% volatility

            # Calculate daily returns
            daily_returns = data['Close'].pct_change().dropna()

            # Annualized volatility
            realized_vol = daily_returns.std() * np.sqrt(252)

            return realized_vol

        except Exception as e:
            self.logger.error(f"Error calculating realized volatility: {e}")
            return 0.20  # Default

    def _get_yahoo_chart_closes(self, symbol: str) -> list:
        """Fetch recent closes from Yahoo chart API when yfinance is unavailable."""
        try:
            encoded_symbol = symbol.replace("^", "%5E")
            response = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded_symbol}",
                params={"range": "1mo", "interval": "1d"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            data = response.json()
            result = (data.get("chart", {}).get("result") or [None])[0]
            closes = ((result or {}).get("indicators", {}).get("quote") or [{}])[0].get("close") or []
            return [float(close) for close in closes if close is not None]
        except Exception:
            return []

    def _classify_regime(self, vix: float, market_trend: float, realized_vol: float) -> str:
        """Classify market regime based on indicators"""

        # Primary classification based on VIX
        if vix < self.vix_thresholds['low']:
            base_regime = 'low_vol'
        elif vix > self.vix_thresholds['high']:
            base_regime = 'high_vol'
        else:
            base_regime = 'normal'

        # Adjust based on market trend
        if abs(market_trend) > 0.05:  # Significant trend
            if market_trend > 0:
                trend_direction = 'bull'
            else:
                trend_direction = 'bear'
        else:
            trend_direction = 'sideways'

        # Combine VIX regime with trend
        if base_regime == 'low_vol' and trend_direction == 'sideways':
            return 'low_vol_sideways'  # Best for selling premium
        elif base_regime == 'low_vol' and trend_direction == 'bull':
            return 'low_vol_bull'  # Good for covered calls
        elif base_regime == 'high_vol' and realized_vol > 0.25:
            return 'high_vol_bear'  # Crisis regime
        elif base_regime == 'high_vol':
            return 'high_vol'  # General high volatility
        else:
            return 'normal'  # Standard regime

    def get_regime_recommendations(self, regime: str) -> Dict:
        """Get trading recommendations for specific regime"""

        recommendations = {
            'low_vol_sideways': {
                'preferred_strategy': 'credit_spreads',
                'position_multiplier': 0.8,  # Smaller positions
                'max_dte': 45,  # Longer expirations for theta decay
                'preferred_delta': (0.1, 0.3),  # Further OTM for premium collection
                'risk_level': 'LOW',
                'description': 'Low volatility sideways market - ideal for selling premium'
            },

            'low_vol_bull': {
                'preferred_strategy': 'covered_calls',
                'position_multiplier': 1.0,
                'max_dte': 30,
                'preferred_delta': (0.2, 0.4),
                'risk_level': 'LOW',
                'description': 'Low volatility bull market - good for covered calls'
            },

            'normal': {
                'preferred_strategy': 'vertical_spreads',
                'position_multiplier': 1.0,
                'max_dte': 30,
                'preferred_delta': (0.3, 0.6),
                'risk_level': 'MEDIUM',
                'description': 'Normal market conditions - balanced approach'
            },

            'high_vol': {
                'preferred_strategy': 'debit_spreads',
                'position_multiplier': 1.2,  # Larger positions in high vol
                'max_dte': 21,  # Shorter expirations
                'preferred_delta': (0.4, 0.7),
                'risk_level': 'HIGH',
                'description': 'High volatility - buy premium strategies'
            },

            'high_vol_bear': {
                'preferred_strategy': 'protective_puts',
                'position_multiplier': 0.7,  # Smaller positions in crisis
                'max_dte': 14,  # Very short term
                'preferred_delta': (0.5, 0.8),
                'risk_level': 'VERY_HIGH',
                'description': 'High volatility bear market - defensive strategies'
            }
        }

        return recommendations.get(regime, recommendations['normal'])

    def should_adjust_strategy(self, current_strategy: str, regime: str) -> bool:
        """Check if strategy should be adjusted for current regime"""
        recommendations = self.get_regime_recommendations(regime)
        preferred_strategy = recommendations['preferred_strategy']

        # Major strategy mismatches
        strategy_mismatches = {
            'low_vol_sideways': ['debit_spreads', 'long_calls', 'long_puts'],
            'high_vol': ['credit_spreads', 'iron_condors'],
            'high_vol_bear': ['naked_options', 'credit_spreads']
        }

        if regime in strategy_mismatches:
            return current_strategy in strategy_mismatches[regime]

        return False

    def get_position_adjustments(self, regime: str) -> Dict:
        """Get position size and risk adjustments for regime"""
        recommendations = self.get_regime_recommendations(regime)

        return {
            'position_multiplier': recommendations['position_multiplier'],
            'max_dte': recommendations['max_dte'],
            'preferred_delta_range': recommendations['preferred_delta'],
            'risk_level': recommendations['risk_level'],
            'should_reduce_exposure': recommendations['risk_level'] in ['HIGH', 'VERY_HIGH']
        }

    def is_favorable_regime(self, strategy: str) -> bool:
        """Check if current regime is favorable for given strategy"""
        regime = self.detect_current_regime()
        recommendations = self.get_regime_recommendations(regime)

        # Check if strategy matches regime preference
        if strategy == recommendations['preferred_strategy']:
            return True

        # Additional checks for strategy compatibility
        strategy_compatibility = {
            'vertical_spreads': ['normal', 'high_vol'],
            'credit_spreads': ['low_vol_sideways', 'low_vol_bull'],
            'debit_spreads': ['high_vol', 'normal'],
            'long_options': ['high_vol']
        }

        current_regime_type = regime.split('_')[0]  # Get base regime (low_vol, high_vol, etc.)

        if strategy in strategy_compatibility:
            return current_regime_type in strategy_compatibility[strategy]

        return False

    def get_regime_summary(self) -> Dict:
        """Get comprehensive regime analysis"""
        regime = self.detect_current_regime()
        vix = self._get_current_vix()
        market_trend = self._get_market_trend()
        realized_vol = self._get_realized_volatility()

        return {
            'current_regime': regime,
            'vix_level': vix,
            'vix_category': self._get_vix_category(vix),
            'market_trend': market_trend,
            'realized_volatility': realized_vol,
            'recommendations': self.get_regime_recommendations(regime),
            'timestamp': datetime.now().isoformat()
        }

    def _get_vix_category(self, vix: float) -> str:
        """Get VIX category description"""
        if vix < self.vix_thresholds['low']:
            return 'Low (Complacent)'
        elif vix < self.vix_thresholds['normal']:
            return 'Normal'
        elif vix < self.vix_thresholds['high']:
            return 'Elevated'
        else:
            return 'High (Fear)'
