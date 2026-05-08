"""
Alert Outcome Learning Loop - Tracks and learns from alert performance
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
import statistics

class AlertOutcomeLearningLoop:
    """
    Tracks alert outcomes and continuously improves the system
    """
    def __init__(self):
        self.learning_file = os.path.join(os.path.dirname(__file__), 'alert_learning.json')
        self.learning_data = self._load_learning_data()

    def _bucket_pop(self, pop_value) -> str:
        """Bucket POP into coarse ranges for analytics"""
        try:
            pop = float(pop_value)
        except (TypeError, ValueError):
            return "unknown"

        if pop < 30:
            return "<30"
        if pop < 40:
            return "30-40"
        if pop < 50:
            return "40-50"
        if pop < 60:
            return "50-60"
        return "60+"

    def _bucket_iv_rank(self, iv_rank) -> str:
        """Bucket IV rank into coarse regimes"""
        if iv_rank is None:
            return "unknown"
        try:
            iv = float(iv_rank)
        except (TypeError, ValueError):
            return "unknown"

        if iv < 30:
            return "<30"
        if iv < 50:
            return "30-50"
        if iv < 70:
            return "50-70"
        return "70+"

    def _load_learning_data(self) -> Dict:
        """Load existing learning data"""
        try:
            if os.path.exists(self.learning_file):
                with open(self.learning_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Learning data load error: {e}")
        return {
            'alert_history': [],
            'performance_stats': {},
            'threshold_adjustments': {},
            'last_updated': None
        }

    def _make_json_safe(self, obj):
        """Convert nested structures to JSON-serializable types"""
        # Primitive types are already safe
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj

        # Try to normalize common numeric-like objects (e.g. numpy scalars)
        try:
            import numpy as np  # type: ignore
            if isinstance(obj, (np.integer, np.floating)):
                return obj.item()
        except Exception:
            pass

        # Containers
        if isinstance(obj, dict):
            return {self._make_json_safe(k): self._make_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._make_json_safe(v) for v in obj]
        if isinstance(obj, tuple):
            return [self._make_json_safe(v) for v in obj]

        # Fallback: string representation
        return str(obj)

    def _save_learning_data(self) -> None:
        """Save learning data to file"""
        try:
            with open(self.learning_file, 'w') as f:
                safe_data = self._make_json_safe(self.learning_data)
                json.dump(safe_data, f, indent=2)
        except Exception as e:
            print(f"Learning data save error: {e}")

    def record_alert_outcome(self, alert_data: Dict, outcome: str, outcome_details: Dict = None) -> None:
        """
        Record the outcome of an alert for learning
        outcome: 'success', 'failure', 'partial', 'no_action'
        """
        # Handle priority enum conversion
        priority = alert_data.get('priority', 'INFO')
        if hasattr(priority, 'value'):  # If it's an enum, get its value
            priority = priority.value

        pop_at_alert = alert_data.get('pop', 0)
        iv_rank = alert_data.get('iv_rank')
        suggested_strategy = alert_data.get('suggested_strategy')
        win_rate = alert_data.get('win_rate')
        market_regime = alert_data.get('market_regime', 'normal')

        alert_record = {
            'alert_id': alert_data.get('alert_id'),
            'symbol': alert_data.get('symbol'),
            'alert_type': alert_data.get('type', 'signal'),
            'priority': priority,
            'trigger_reason': alert_data.get('trigger_reason'),
            'pop_at_alert': pop_at_alert,
            'pop_bucket': self._bucket_pop(pop_at_alert),
            'iv_rank': iv_rank,
            'iv_bucket': self._bucket_iv_rank(iv_rank),
            'suggested_strategy': suggested_strategy,
            'win_rate_at_alert': win_rate,
            'market_regime': market_regime,
            'outcome': outcome,
            'outcome_details': outcome_details or {},
            'timestamp': datetime.now().isoformat(),
            'week_of': datetime.now().strftime('%Y-%W')
        }

        self.learning_data['alert_history'].append(alert_record)
        self.learning_data['last_updated'] = datetime.now().isoformat()

        # Update performance stats
        self._update_performance_stats()

        # Trigger learning adjustments
        self._apply_learning_adjustments()

        self._save_learning_data()

    def _update_performance_stats(self) -> None:
        """Update overall performance statistics"""
        history = self.learning_data['alert_history']
        if not history:
            return

        # Calculate success rates
        outcomes = defaultdict(int)
        for alert in history:
            outcomes[alert['outcome']] += 1

        total_alerts = len(history)
        success_rate = outcomes['success'] / total_alerts if total_alerts > 0 else 0
        partial_rate = outcomes['partial'] / total_alerts if total_alerts > 0 else 0

        # Calculate by alert type
        type_performance = defaultdict(lambda: {'total': 0, 'success': 0})
        for alert in history:
            alert_type = alert['alert_type']
            type_performance[alert_type]['total'] += 1
            if alert['outcome'] == 'success':
                type_performance[alert_type]['success'] += 1

        # Calculate by priority
        priority_performance = defaultdict(lambda: {'total': 0, 'success': 0})

        # New: performance by strategy, POP bucket, and IV bucket
        strategy_performance = defaultdict(lambda: {'total': 0, 'success': 0})
        pop_bucket_performance = defaultdict(lambda: {'total': 0, 'success': 0})
        iv_bucket_performance = defaultdict(lambda: {'total': 0, 'success': 0})

        for alert in history:
            priority = alert['priority']
            # Handle enum conversion if needed
            if hasattr(priority, 'value'):
                priority = priority.value
            outcome_label = alert.get('outcome')

            # Priority stats
            priority_performance[priority]['total'] += 1
            if outcome_label == 'success':
                priority_performance[priority]['success'] += 1

            # Strategy stats
            strategy = alert.get('suggested_strategy', 'UNKNOWN') or 'UNKNOWN'
            strategy_performance[strategy]['total'] += 1
            if outcome_label == 'success':
                strategy_performance[strategy]['success'] += 1

            # POP bucket stats
            pop_bucket = alert.get('pop_bucket', 'unknown')
            pop_bucket_performance[pop_bucket]['total'] += 1
            if outcome_label == 'success':
                pop_bucket_performance[pop_bucket]['success'] += 1

            # IV bucket stats
            iv_bucket = alert.get('iv_bucket', 'unknown')
            iv_bucket_performance[iv_bucket]['total'] += 1
            if outcome_label == 'success':
                iv_bucket_performance[iv_bucket]['success'] += 1

        self.learning_data['performance_stats'] = {
            'total_alerts': total_alerts,
            'success_rate': success_rate,
            'partial_success_rate': partial_rate,
            'failure_rate': outcomes['failure'] / total_alerts if total_alerts > 0 else 0,
            'no_action_rate': outcomes['no_action'] / total_alerts if total_alerts > 0 else 0,
            'type_performance': dict(type_performance),
            'priority_performance': dict(priority_performance),
            'strategy_performance': dict(strategy_performance),
            'pop_bucket_performance': dict(pop_bucket_performance),
            'iv_bucket_performance': dict(iv_bucket_performance),
            'last_updated': datetime.now().isoformat()
        }

    def _apply_learning_adjustments(self) -> None:
        """Apply learning-based adjustments to thresholds"""
        stats = self.learning_data['performance_stats']

        # Adjust POP thresholds based on success rates
        if stats.get('success_rate', 0) > 0.7:  # Too conservative
            self.learning_data['threshold_adjustments']['pop_threshold'] = 'decrease'
        elif stats.get('success_rate', 0) < 0.3:  # Too aggressive
            self.learning_data['threshold_adjustments']['pop_threshold'] = 'increase'

        # Adjust alert frequency based on no_action rate
        no_action_rate = stats.get('no_action_rate', 0)
        if no_action_rate > 0.5:  # Too many ignored alerts
            self.learning_data['threshold_adjustments']['alert_frequency'] = 'decrease'
        elif no_action_rate < 0.1:  # Too few alerts
            self.learning_data['threshold_adjustments']['alert_frequency'] = 'increase'

    def get_learning_recommendations(self) -> List[str]:
        """Get recommendations based on learning data"""
        recommendations = []
        adjustments = self.learning_data.get('threshold_adjustments', {})

        if adjustments.get('pop_threshold') == 'decrease':
            recommendations.append("Consider lowering POP threshold - current success rate suggests we're being too conservative")

        if adjustments.get('pop_threshold') == 'increase':
            recommendations.append("Consider raising POP threshold - current failure rate suggests we're being too aggressive")

        if adjustments.get('alert_frequency') == 'decrease':
            recommendations.append("Reduce alert frequency - too many alerts are being ignored")

        if adjustments.get('alert_frequency') == 'increase':
            recommendations.append("Increase alert frequency - current alerts are highly actionable")

        # Type-specific recommendations
        type_perf = self.learning_data['performance_stats'].get('type_performance', {})
        for alert_type, perf in type_perf.items():
            if perf['total'] > 5:  # Enough data
                success_rate = perf['success'] / perf['total']
                if success_rate < 0.3:
                    recommendations.append(f"Review {alert_type} alerts - low success rate ({success_rate:.1%})")
                elif success_rate > 0.8:
                    recommendations.append(f"Consider more {alert_type} alerts - high success rate ({success_rate:.1%})")

        # Strategy-specific recommendations
        strat_perf = self.learning_data['performance_stats'].get('strategy_performance', {})
        for strat, perf in strat_perf.items():
            if perf['total'] < 10:
                continue
            success_rate = perf['success'] / perf['total'] if perf['total'] > 0 else 0
            if success_rate < 0.35:
                recommendations.append(f"Review {strat} strategy - low success rate ({success_rate:.1%})")
            elif success_rate > 0.6:
                recommendations.append(f"Lean into {strat} setups - strong success rate ({success_rate:.1%})")

        return recommendations

    def get_performance_summary(self) -> Dict:
        """Get current performance summary"""
        stats = self.learning_data.get('performance_stats', {})

        summary = {
            'total_alerts': stats.get('total_alerts', 0),
            'success_rate': stats.get('success_rate', 0),
            'recommendations': self.get_learning_recommendations(),
            'last_updated': self.learning_data.get('last_updated'),
            'strategy_performance': stats.get('strategy_performance', {}),
            'pop_bucket_performance': stats.get('pop_bucket_performance', {}),
            'iv_bucket_performance': stats.get('iv_bucket_performance', {})
        }

        # Add weekly performance
        weekly_perf = self._get_weekly_performance()
        summary['weekly_performance'] = weekly_perf

        return summary

    def _get_weekly_performance(self) -> Dict:
        """Get performance breakdown by week"""
        history = self.learning_data['alert_history']
        weekly_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'partial': 0, 'failure': 0})

        for alert in history:
            week = alert.get('week_of', 'unknown')
            weekly_stats[week]['total'] += 1
            outcome = alert.get('outcome', 'unknown')
            if outcome in weekly_stats[week]:
                weekly_stats[week][outcome] += 1

        # Convert to success rates
        weekly_rates = {}
        for week, stats in weekly_stats.items():
            total = stats['total']
            if total > 0:
                success_rate = (stats['success'] + stats['partial'] * 0.5) / total
                weekly_rates[week] = round(success_rate, 3)

        return dict(weekly_rates)

    def format_learning_report(self, summary: Dict) -> str:
        """Format learning summary for display"""
        message = "🧠 **ALERT LEARNING REPORT** 🧠\n\n"

        message += f"📊 **Overall Performance:**\n"
        message += f"Total Alerts: {summary['total_alerts']}\n"
        message += f"Success Rate: {summary['success_rate']:.1f}%\n"

        if summary.get('weekly_performance'):
            message += f"📈 **Weekly Success Rates:**\n"
            for week, rate in summary['weekly_performance'].items():
                message += f"Week {week}: {rate:.1f}%\n"

        if summary.get('recommendations'):
            message += f"💡 **AI Recommendations:**\n"
            for rec in summary['recommendations'][:3]:  # Top 3
                message += f"• {rec}\n"

        return message

    def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """Clean up old learning data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        original_count = len(self.learning_data['alert_history'])
        self.learning_data['alert_history'] = [
            alert for alert in self.learning_data['alert_history']
            if datetime.fromisoformat(alert['timestamp']) > cutoff_date
        ]

        if len(self.learning_data['alert_history']) != original_count:
            self._update_performance_stats()
            self._save_learning_data()
            print(f"🧹 Cleaned {original_count - len(self.learning_data['alert_history'])} old alert records")

# Global instance
_learning_loop = None

def get_alert_learning_loop() -> AlertOutcomeLearningLoop:
    """Get singleton alert learning loop"""
    global _learning_loop
    if _learning_loop is None:
        _learning_loop = AlertOutcomeLearningLoop()
    return _learning_loop
