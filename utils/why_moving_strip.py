"""
Why It's Moving - Insight strips explaining price action
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import yfinance as yf

class WhyItsMovingStrip:
    """
    Generates explanatory context for why stocks are moving
    """
    def __init__(self):
        self.cache = {}

    def generate_insight_strip(self, signal_data: Dict) -> str:
        """
        Generate contextual insight strip for the signal
        """
        symbol = signal_data.get('symbol')
        if not symbol:
            return "No symbol provided"

        insights = []

        # Recent news context
        news_context = self._get_news_context(signal_data)
        if news_context:
            insights.append(news_context)

        # Volume context
        volume_context = self._get_volume_context(signal_data)
        if volume_context:
            insights.append(volume_context)

        # Technical context
        technical_context = self._get_technical_context(signal_data)
        if technical_context:
            insights.append(technical_context)

        # Options context
        options_context = self._get_options_context(signal_data)
        if options_context:
            insights.append(options_context)

        # Institutional context
        institutional_context = self._get_institutional_context(signal_data)
        if institutional_context:
            insights.append(institutional_context)

        # Social sentiment
        social_context = self._get_social_context(signal_data)
        if social_context:
            insights.append(social_context)

        # Format the strip
        if insights:
            return " | ".join(insights)
        else:
            return "Standard price action - monitoring for catalysts"

    def _get_news_context(self, signal_data: Dict) -> Optional[str]:
        """Get news-related context"""
        news_headline = signal_data.get('recent_news')
        catalyst_type = signal_data.get('catalyst_type')

        if news_headline:
            return f"News: {news_headline[:40]}..."
        elif catalyst_type:
            return f"Catalyst: {catalyst_type}"
        return None

    def _get_volume_context(self, signal_data: Dict) -> Optional[str]:
        """Get volume-related context"""
        volume_surge = signal_data.get('volume_surge')
        relative_volume = signal_data.get('relative_volume')

        if volume_surge and volume_surge > 2:
            return f"Volume: {volume_surge:.1f}x avg"
        elif relative_volume and relative_volume > 1.5:
            return f"RVOL: {relative_volume:.1f}"
        return None

    def _get_technical_context(self, signal_data: Dict) -> Optional[str]:
        """Get technical analysis context"""
        rsi = signal_data.get('rsi')
        trend = signal_data.get('trend')
        support_resistance = signal_data.get('support_resistance')

        parts = []

        if rsi:
            if rsi < 30:
                parts.append("Oversold")
            elif rsi > 70:
                parts.append("Overbought")

        if trend:
            parts.append(f"{trend} trend")

        if support_resistance:
            parts.append(f"at {support_resistance}")

        return " | ".join(parts) if parts else None

    def _get_options_context(self, signal_data: Dict) -> Optional[str]:
        """Get options market context"""
        iv = signal_data.get('implied_volatility')
        put_call_ratio = signal_data.get('put_call_ratio')
        options_volume = signal_data.get('options_volume')

        parts = []

        if iv and iv > 0.5:
            parts.append(f"IV: {iv:.0%}")

        if put_call_ratio:
            if put_call_ratio > 1.2:
                parts.append("Bearish PCR")
            elif put_call_ratio < 0.8:
                parts.append("Bullish PCR")

        if options_volume and options_volume > 100000:
            parts.append("High options vol")

        return " | ".join(parts) if parts else None

    def _get_institutional_context(self, signal_data: Dict) -> Optional[str]:
        """Get institutional activity context"""
        block_trades = signal_data.get('block_trades_detected')
        insider_buying = signal_data.get('insider_buying')
        institutional_ownership = signal_data.get('institutional_ownership')

        parts = []

        if block_trades:
            parts.append("Block trades")

        if insider_buying:
            parts.append("Insider buying")

        if institutional_ownership:
            if institutional_ownership > 0.7:
                parts.append("High inst ownership")
            elif institutional_ownership < 0.3:
                parts.append("Low inst ownership")

        return " | ".join(parts) if parts else None

    def _get_social_context(self, signal_data: Dict) -> Optional[str]:
        """Get social sentiment context"""
        social_mentions = signal_data.get('social_mentions')
        sentiment_score = signal_data.get('sentiment_score')
        reddit_mentions = signal_data.get('reddit_mentions')

        parts = []

        if social_mentions and social_mentions > 100:
            direction = "bullish" if sentiment_score and sentiment_score > 0.1 else "bearish"
            parts.append(f"Social: {direction} ({social_mentions})")

        if reddit_mentions and reddit_mentions > 10:
            parts.append(f"Reddit: {reddit_mentions} mentions")

        return " | ".join(parts) if parts else None

    def get_movement_explanation(self, symbol: str, current_price: float, change_pct: float) -> str:
        """
        Generate explanation for recent price movement
        """
        direction = "up" if change_pct > 0 else "down"
        magnitude = "sharply" if abs(change_pct) > 5 else "moderately"

        explanation = f"{symbol} moved {magnitude} {direction} {abs(change_pct):.1f}% "

        # Add context based on cached data
        if symbol in self.cache:
            cached_data = self.cache[symbol]
            last_update = datetime.fromisoformat(cached_data.get('timestamp', datetime.now().isoformat()))

            if (datetime.now() - last_update).seconds < 3600:  # Within last hour
                volume_ratio = cached_data.get('volume_ratio', 1)
                if volume_ratio > 2:
                    explanation += "on heavy volume "
                elif volume_ratio < 0.5:
                    explanation += "on light volume "

        explanation += "- monitoring for continuation or reversal"

        return explanation

    def update_cache(self, symbol: str, data: Dict) -> None:
        """Update cached data for symbol"""
        self.cache[symbol] = {
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

# Global instance
_why_moving_strip = None

def get_why_moving_strip() -> WhyItsMovingStrip:
    """Get singleton why it's moving strip generator"""
    global _why_moving_strip
    if _why_moving_strip is None:
        _why_moving_strip = WhyItsMovingStrip()
    return _why_moving_strip
