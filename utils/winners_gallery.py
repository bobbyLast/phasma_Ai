"""
Winner's Gallery - Automatic showcase of successful trades
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
import io

class WinnersGallery:
    """
    Tracks and showcases successful trades automatically
    """
    def __init__(self):
        self.gallery_file = os.path.join(os.path.dirname(__file__), 'winners_gallery.json')
        self.min_gain_threshold = 0.05  # 5% minimum gain
        self.max_winners = 5  # Show top 5 winners
        self.gallery = self._load_gallery()

    def _load_gallery(self) -> Dict:
        """Load existing gallery"""
        try:
            if os.path.exists(self.gallery_file):
                with open(self.gallery_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Gallery load error: {e}")
        return {'winners': [], 'last_updated': None}

    def _save_gallery(self) -> None:
        """Save gallery to file"""
        try:
            with open(self.gallery_file, 'w') as f:
                json.dump(self.gallery, f, indent=2)
        except Exception as e:
            print(f"Gallery save error: {e}")

    def add_winner(self, trade_data: Dict) -> bool:
        """
        Add a successful trade to the gallery
        Returns True if added, False otherwise
        """
        realized_gain = trade_data.get('realized_pnl_pct', 0)

        if realized_gain < self.min_gain_threshold:
            return False

        winner = {
            'symbol': trade_data.get('symbol'),
            'entry_date': trade_data.get('entry_date'),
            'exit_date': trade_data.get('exit_date'),
            'realized_gain_pct': realized_gain,
            'peak_gain_pct': trade_data.get('peak_gain_pct', realized_gain),
            'holding_period_days': trade_data.get('holding_period_days', 1),
            'catalyst_type': trade_data.get('catalyst_type', 'Unknown'),
            'engines_used': trade_data.get('engines_used', []),
            'key_factors': trade_data.get('key_factors', []),
            'added_date': datetime.now().isoformat()
        }

        # Add to gallery
        self.gallery['winners'].append(winner)

        # Sort by gain and keep top winners
        self.gallery['winners'].sort(key=lambda x: x['realized_gain_pct'], reverse=True)
        self.gallery['winners'] = self.gallery['winners'][:self.max_winners]

        # Update timestamp
        self.gallery['last_updated'] = datetime.now().isoformat()

        # Save
        self._save_gallery()

        return True

    def generate_gallery_report(self) -> Dict:
        """Generate current gallery report"""
        if not self.gallery['winners']:
            return {'message': 'No winners yet this period', 'winners': []}

        # Calculate stats
        total_winners = len(self.gallery['winners'])
        avg_gain = sum(w['realized_gain_pct'] for w in self.gallery['winners']) / total_winners
        best_performer = max(self.gallery['winners'], key=lambda x: x['realized_gain_pct'])

        report = {
            'total_winners': total_winners,
            'average_gain_pct': avg_gain,
            'best_performer': {
                'symbol': best_performer['symbol'],
                'gain_pct': best_performer['realized_gain_pct'],
                'catalyst': best_performer['catalyst_type']
            },
            'winners': self.gallery['winners'],
            'last_updated': self.gallery['last_updated']
        }

        return report

    def format_gallery_message(self, report: Dict) -> str:
        """Format gallery for display"""
        if not report.get('winners'):
            return "🏆 **WINNER'S GALLERY** 🏆\n\nNo winners yet - stay tuned!"

        avg_gain = report.get('average_gain_pct', 0)
        message = "🏆 **WINNER'S GALLERY** 🏆\n"
        message += f"Last {len(report['winners'])} Big Winners\n\n"

        for i, winner in enumerate(report['winners'], 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "🏅")

            message += f"{medal} **{winner['symbol']}** +{winner['realized_gain_pct']:.1%}\n"
            message += f"📅 {winner['holding_period_days']}d | ⚡ {winner['catalyst_type']}\n"

            if winner['engines_used']:
                message += f"🤖 Engines: {', '.join(winner['engines_used'][:2])}\n"

            message += "\n"

        message += f"Average Gain: {avg_gain:.1f}%\n"
        message += f"💎 Best: {report['best_performer']['symbol']} (+{report['best_performer']['gain_pct']:.1%})"

        return message

    def cleanup_old_winners(self, days_to_keep: int = 30) -> None:
        """Remove winners older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        original_count = len(self.gallery['winners'])
        self.gallery['winners'] = [
            w for w in self.gallery['winners']
            if datetime.fromisoformat(w['added_date']) > cutoff_date
        ]

        if len(self.gallery['winners']) != original_count:
            self._save_gallery()
            print(f"🧹 Cleaned {original_count - len(self.gallery['winners'])} old winners")

    def get_win_streak_info(self) -> Dict:
        """Get information about recent win streaks"""
        winners = self.gallery['winners']
        if not winners:
            return {'current_streak': 0, 'best_streak': 0}

        # Sort by date
        sorted_winners = sorted(winners, key=lambda x: x['added_date'])

        current_streak = 0
        best_streak = 0
        temp_streak = 0

        # Calculate streaks (simplified - assumes all are wins)
        for winner in sorted_winners:
            temp_streak += 1
            best_streak = max(best_streak, temp_streak)

        current_streak = temp_streak  # All recent are considered current

        return {
            'current_streak': current_streak,
            'best_streak': best_streak,
            'total_wins': len(winners)
        }

# Global instance
_winners_gallery = None

def get_winners_gallery() -> WinnersGallery:
    """Get singleton winners gallery"""
    global _winners_gallery
    if _winners_gallery is None:
        _winners_gallery = WinnersGallery()
    return _winners_gallery
