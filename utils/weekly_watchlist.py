"""
Weekly High-Volatility Watchlist Generator
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
import json

class WeeklyWatchlistGenerator:
    """
    Generates curated weekly watchlist of high-volatility opportunities
    """
    def __init__(self):
        self.watchlist_file = os.path.join(os.path.dirname(__file__), 'weekly_watchlist.json')
        self.min_pop_threshold = 35.0  # Minimum POP for inclusion
        self.max_items = 5  # Max items per watchlist

    def generate_watchlist(self, recent_signals: List[Dict]) -> Dict:
        """
        Generate weekly watchlist from recent high-quality signals
        """
        # Filter for high-POP signals
        qualified_signals = [
            signal for signal in recent_signals
            if signal.get('pop', 0) >= self.min_pop_threshold
        ]

        # Sort by POP and volatility
        qualified_signals.sort(
            key=lambda x: (x.get('pop', 0), x.get('volatility', 0)),
            reverse=True
        )

        # Take top items
        watchlist_items = qualified_signals[:self.max_items]

        # Format watchlist
        watchlist = {
            'week_of': datetime.now().strftime('%Y-%W'),
            'generated_at': datetime.now().isoformat(),
            'items': []
        }

        for signal in watchlist_items:
            item = {
                'symbol': signal.get('symbol'),
                'pop': signal.get('pop', 0),
                'volatility': signal.get('volatility', 0),
                'catalyst': signal.get('catalyst_type', 'Unknown'),
                'timeframe': signal.get('timeframe_days', 7),
                'expected_move': signal.get('expected_move_pct', 0),
                'confidence_tier': self._calculate_tier(signal),
                'key_factors': self._extract_key_factors(signal)
            }
            watchlist['items'].append(item)

        # Save to file
        self._save_watchlist(watchlist)

        return watchlist

    def _calculate_tier(self, signal: Dict) -> str:
        """Calculate confidence tier (Gold/Silver/Bronze)"""
        pop = signal.get('pop', 0)
        volatility = signal.get('volatility', 0)

        score = (pop * 0.7) + (volatility * 10 * 0.3)  # Weighted score

        if score >= 70:
            return "GOLD"
        elif score >= 50:
            return "SILVER"
        else:
            return "BRONZE"

    def _extract_key_factors(self, signal: Dict) -> List[str]:
        """Extract key supporting factors"""
        factors = []

        if signal.get('volume_surge'):
            factors.append(f"Volume {signal['volume_surge']}x avg")

        if signal.get('float_tight'):
            factors.append("Tight float")

        if signal.get('news_catalyst'):
            factors.append(f"News: {signal['news_catalyst'][:30]}...")

        if signal.get('options_flow'):
            factors.append("Options interest")

        if signal.get('insider_activity'):
            factors.append("Insider activity")

        return factors[:3]  # Max 3 factors

    def _save_watchlist(self, watchlist: Dict) -> None:
        """Save watchlist to JSON file"""
        try:
            with open(self.watchlist_file, 'w') as f:
                json.dump(watchlist, f, indent=2)
        except Exception as e:
            print(f"Watchlist save error: {e}")

    def load_current_watchlist(self) -> Optional[Dict]:
        """Load current week's watchlist"""
        try:
            if os.path.exists(self.watchlist_file):
                with open(self.watchlist_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Watchlist load error: {e}")
        return None

    def format_watchlist_message(self, watchlist: Dict) -> str:
        """Format watchlist for Telegram/email"""
        message = f"📈 **WEEKLY HIGH-VOL WATCHLIST** 📈\n"
        message += f"Week of {watchlist['week_of']}\n\n"

        for item in watchlist['items']:
            tier_emoji = {
                "GOLD": "🥇",
                "SILVER": "🥈",
                "BRONZE": "🥉"
            }.get(item['confidence_tier'], "📊")

            message += f"{tier_emoji} **{item['symbol']}** ({item['confidence_tier']})\n"
            message += f"🎯 POP: {item['pop']:.1f}% | Vol: {item['volatility']:.1%}\n"
            message += f"⚡ {item['catalyst']} | {item['timeframe']}d window\n"

            if item['key_factors']:
                message += f"🔑 {', '.join(item['key_factors'])}\n"

            message += "\n"

        message += "📅 Monitor these for breakout opportunities!\n"
        return message

# Global instance
_weekly_watchlist = None

def get_weekly_watchlist_generator() -> WeeklyWatchlistGenerator:
    """Get singleton watchlist generator"""
    global _weekly_watchlist
    if _weekly_watchlist is None:
        _weekly_watchlist = WeeklyWatchlistGenerator()
    return _weekly_watchlist
