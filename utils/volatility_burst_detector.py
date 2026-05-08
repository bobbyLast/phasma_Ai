"""
Volatility Burst Detector - Identifies sudden volatility spikes
"""
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio

class VolatilityBurstDetector:
    """
    Detects volatility bursts using ATR expansion and relative volume
    """
    def __init__(self):
        self.cache = {}
        self.burst_threshold = 2.0  # 2x normal volatility
        self.volume_threshold = 1.5  # 1.5x average volume

    async def check_volatility_burst(self, symbol: str) -> Optional[Dict]:
        """
        Check if symbol is experiencing a volatility burst
        Returns burst data if detected, None otherwise
        """
        try:
            # Get recent data
            data = await self._get_recent_data(symbol)
            if not data:
                return None

            # Calculate metrics
            atr_current = self._calculate_atr(data)
            volume_ratio = self._calculate_volume_ratio(data)
            iv_change = self._calculate_iv_change(symbol)

            # Check for burst conditions
            atr_burst = atr_current > (self.cache.get(f"{symbol}_atr_avg", atr_current) * self.burst_threshold)
            volume_burst = volume_ratio > self.volume_threshold

            if atr_burst and volume_burst:
                burst_data = {
                    'symbol': symbol,
                    'atr_current': atr_current,
                    'volume_ratio': volume_ratio,
                    'iv_change': iv_change,
                    'timestamp': datetime.now().isoformat(),
                    'burst_strength': min(atr_current * volume_ratio, 10.0)  # Cap at 10
                }

                # Update cache
                self.cache[f"{symbol}_atr_avg"] = atr_current

                return burst_data

        except Exception as e:
            print(f"Volatility burst check error for {symbol}: {e}")

        return None

    async def _get_recent_data(self, symbol: str, days: int = 5) -> Optional[Dict]:
        """Get recent price data for analysis"""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)

            data = yf.download(
                symbol,
                start=start,
                end=end,
                progress=False,
                interval='1d'
            )

            if len(data) < 3:  # Need minimum data
                return None

            return {
                'high': data['High'].values,
                'low': data['Low'].values,
                'close': data['Close'].values,
                'volume': data['Volume'].values
            }

        except Exception as e:
            print(f"Data fetch error for {symbol}: {e}")
            return None

    def _calculate_atr(self, data: Dict, period: int = 14) -> float:
        """Calculate Average True Range"""
        high = data['high']
        low = data['low']
        close = data['close']

        # True Range
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        # ATR
        atr = np.mean(tr[-period:]) if len(tr) >= period else np.mean(tr)
        return atr

    def _calculate_volume_ratio(self, data: Dict) -> float:
        """Calculate current volume vs average"""
        volumes = data['volume']
        if len(volumes) < 2:
            return 1.0

        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[:-1])  # Exclude current day

        return current_volume / avg_volume if avg_volume > 0 else 1.0

    def _calculate_iv_change(self, symbol: str) -> Optional[float]:
        """Calculate implied volatility change (placeholder for options data)"""
        # Would integrate with options API
        # For now, return None or mock data
        return None

    def get_burst_alert_message(self, burst_data: Dict) -> str:
        """Format volatility burst alert message"""
        symbol = burst_data['symbol']
        atr = burst_data['atr_current']
        vol_ratio = burst_data['volume_ratio']
        strength = burst_data['burst_strength']

        strength_desc = "EXTREME" if strength > 5 else "HIGH" if strength > 3 else "MODERATE"

        message = f"VOLATILITY BURST ⚡ {symbol}\n"
        message += f"ATR: ${atr:.2f}\n"
        message += f"Volume Ratio: {vol_ratio:.1f}x\n"
        message += f"Strength: {strength_desc} ({strength:.1f})\n"
        message += "🚨 Review chart immediately - potential breakout"

        return message

# Global instance
_vol_burst_detector = None

def get_vol_burst_detector() -> VolatilityBurstDetector:
    """Get singleton volatility burst detector"""
    global _vol_burst_detector
    if _vol_burst_detector is None:
        _vol_burst_detector = VolatilityBurstDetector()
    return _vol_burst_detector
