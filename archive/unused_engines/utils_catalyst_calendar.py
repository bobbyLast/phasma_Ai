"""
Smart Catalyst Calendar - Tracks and notifies about upcoming catalysts
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils.timeframe_calculator import calculate_optimal_timeframe

class SmartCatalystCalendar:
    """
    Tracks catalysts and provides calendar integration
    """
    def __init__(self):
        self.calendar_file = os.path.join(os.path.dirname(__file__), 'catalyst_calendar.json')
        self.calendar = self._load_calendar()

    def _load_calendar(self) -> Dict:
        """Load existing calendar"""
        try:
            if os.path.exists(self.calendar_file):
                with open(self.calendar_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Calendar load error: {e}")
        return {'events': [], 'last_updated': None}

    def _save_calendar(self) -> None:
        """Save calendar to file"""
        try:
            with open(self.calendar_file, 'w') as f:
                json.dump(self.calendar, f, indent=2)
        except Exception as e:
            print(f"Calendar save error: {e}")

    def add_catalyst_event(self, signal_data: Dict) -> None:
        """
        Add a catalyst event to the calendar
        """
        symbol = signal_data.get('symbol')
        catalyst_type = signal_data.get('catalyst_type', 'Unknown')
        days_to_expiry = signal_data.get('days_to_expiry', 7)

        # Calculate event date
        event_date = datetime.now() + timedelta(days=days_to_expiry)

        event = {
            'symbol': symbol,
            'catalyst_type': catalyst_type,
            'event_date': event_date.isoformat(),
            'days_remaining': days_to_expiry,
            'status': 'active',
            'pop_at_entry': signal_data.get('pop', 0),
            'expected_move': signal_data.get('expected_move_pct', 0),
            'created_at': datetime.now().isoformat(),
            'notes': signal_data.get('catalyst_notes', '')
        }

        # Check for duplicates
        existing = next((e for e in self.calendar['events']
                        if e['symbol'] == symbol and e['status'] == 'active'), None)

        if existing:
            # Update existing
            existing.update(event)
        else:
            # Add new
            self.calendar['events'].append(event)

        self.calendar['last_updated'] = datetime.now().isoformat()
        self._save_calendar()

    def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming catalyst events"""
        cutoff_date = datetime.now() + timedelta(days=days_ahead)

        upcoming = []
        for event in self.calendar['events']:
            if event['status'] == 'active':
                event_date = datetime.fromisoformat(event['event_date'])
                if event_date <= cutoff_date:
                    # Update days remaining
                    event['days_remaining'] = (event_date - datetime.now()).days
                    upcoming.append(event)

        # Sort by date
        upcoming.sort(key=lambda x: x['event_date'])

        return upcoming

    def get_today_events(self) -> List[Dict]:
        """Get events happening today"""
        today = datetime.now().date()
        today_events = []

        for event in self.calendar['events']:
            if event['status'] == 'active':
                event_date = datetime.fromisoformat(event['event_date']).date()
                if event_date == today:
                    today_events.append(event)

        return today_events

    def update_event_status(self, symbol: str, status: str, notes: str = "") -> None:
        """Update event status (completed, failed, etc.)"""
        for event in self.calendar['events']:
            if event['symbol'] == symbol and event['status'] == 'active':
                event['status'] = status
                event['completion_notes'] = notes
                event['completed_at'] = datetime.now().isoformat()
                break

        self._save_calendar()

    def cleanup_old_events(self, days_to_keep: int = 30) -> None:
        """Remove old completed events"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        original_count = len(self.calendar['events'])
        self.calendar['events'] = [
            e for e in self.calendar['events']
            if e['status'] == 'active' or
               datetime.fromisoformat(e.get('completed_at', e['created_at'])) > cutoff_date
        ]

        if len(self.calendar['events']) != original_count:
            self._save_calendar()
            print(f"🧹 Cleaned {original_count - len(self.calendar['events'])} old calendar events")

    def format_calendar_message(self, events: List[Dict], title: str = "CATALYST CALENDAR") -> str:
        """Format calendar events for display"""
        if not events:
            return f"📅 **{title}**\n\nNo upcoming catalysts"

        message = f"📅 **{title}** 📅\n\n"

        for event in events:
            status_emoji = "⏰" if event['days_remaining'] > 0 else "🎯"

            message += f"{status_emoji} **{event['symbol']}**\n"
            message += f"📊 {event['catalyst_type']} | {event['days_remaining']}d remaining\n"

            if event.get('pop_at_entry'):
                message += f"🎯 POP: {event['pop_at_entry']:.1f}%\n"

            if event.get('notes'):
                message += f"📝 {event['notes'][:50]}...\n"

            message += "\n"

        return message

    def get_catalyst_summary(self) -> Dict:
        """Get summary statistics"""
        events = self.calendar['events']
        active_events = [e for e in events if e['status'] == 'active']
        completed_events = [e for e in events if e['status'] != 'active']

        return {
            'total_events': len(events),
            'active_events': len(active_events),
            'completed_events': len(completed_events),
            'upcoming_this_week': len(self.get_upcoming_events(7)),
            'due_today': len(self.get_today_events())
        }

# Global instance
_catalyst_calendar = None

def get_catalyst_calendar() -> SmartCatalystCalendar:
    """Get singleton catalyst calendar"""
    global _catalyst_calendar
    if _catalyst_calendar is None:
        _catalyst_calendar = SmartCatalystCalendar()
    return _catalyst_calendar
