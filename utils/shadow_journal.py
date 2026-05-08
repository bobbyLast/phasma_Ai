#!/usr/bin/env python3
"""
PHASMA AI - Shadow Journal
Tracks confidence levels and trade outcomes for adaptive threshold optimization
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import os

logger = logging.getLogger(__name__)

class ShadowJournal:
    """Tracks and analyzes confidence vs trade outcomes"""
    
    def __init__(self, journal_file: str = "logs/shadow_journal.json"):
        self.journal_file = journal_file
        self.trades = []
        self.confidence_buckets = defaultdict(list)
        self.source_performance = defaultdict(list)
        self.recent_trades = deque(maxlen=1000)  # Last 1000 trades
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(journal_file), exist_ok=True)
        
        # Load existing journal
        self._load_journal()
    
    def record_trade_signal(self, signal: Dict[str, Any]) -> None:
        """Record a trade signal before execution"""
        trade_entry = {
            'id': f"{signal.get('symbol', '')}_{datetime.now().timestamp()}",
            'symbol': signal.get('symbol', ''),
            'action': signal.get('action', ''),
            'confidence': signal.get('confidence', 0),
            'source': signal.get('source', ''),
            'position_size': signal.get('position_size', 0),
            'entry_price': signal.get('entry_price', signal.get('current_price', 0)),
            'timestamp': datetime.now().isoformat(),
            'status': 'PENDING',
            'outcome': None,
            'pnl': None,
            'pnl_percent': None,
            'hold_days': None,
            'exit_reason': None
        }
        
        self.trades.append(trade_entry)
        self.recent_trades.append(trade_entry)
        self._save_journal()
        
        logger.info(f"Recorded trade signal: {trade_entry['symbol']} @ {trade_entry['confidence']:.1%} confidence")
    
    def record_trade_outcome(self, trade_id: str, outcome: Dict[str, Any]) -> None:
        """Record the outcome of a trade"""
        # Find the trade
        trade = None
        for t in self.trades:
            if t['id'] == trade_id:
                trade = t
                break
        
        if not trade:
            logger.warning(f"Trade {trade_id} not found in journal")
            return
        
        # Update trade with outcome
        trade['status'] = outcome.get('status', 'CLOSED')
        trade['outcome'] = outcome.get('outcome', 'UNKNOWN')  # WIN, LOSS, BREAKEVEN
        trade['pnl'] = outcome.get('pnl', 0)
        trade['pnl_percent'] = outcome.get('pnl_percent', 0)
        trade['hold_days'] = outcome.get('hold_days', 0)
        trade['exit_reason'] = outcome.get('exit_reason', '')
        trade['exit_timestamp'] = datetime.now().isoformat()
        
        # Update confidence bucket
        confidence_range = self._get_confidence_bucket(trade['confidence'])
        self.confidence_buckets[confidence_range].append(trade)
        
        # Update source performance
        source = trade['source']
        self.source_performance[source].append(trade)
        
        # Save
        self._save_journal()
        
        logger.info(f"Recorded trade outcome: {trade['symbol']} {trade['outcome']} ({trade['pnl_percent']:+.1%})")
    
    def get_confidence_analysis(self, min_trades: int = 10) -> Dict[str, Any]:
        """Analyze win rates by confidence level"""
        analysis = {}
        
        for confidence_range, trades in self.confidence_buckets.items():
            if len(trades) < min_trades:
                continue
            
            wins = sum(1 for t in trades if t['outcome'] == 'WIN')
            total = len(trades)
            win_rate = wins / total
            
            # Average P&L
            pnls = [t['pnl_percent'] for t in trades if t['pnl_percent'] is not None]
            avg_pnl = statistics.mean(pnls) if pnls else 0
            
            analysis[confidence_range] = {
                'total_trades': total,
                'wins': wins,
                'losses': total - wins,
                'win_rate': win_rate,
                'avg_pnl_percent': avg_pnl,
                'confidence_range': confidence_range
            }
        
        return analysis
    
    def get_optimal_confidence_threshold(self) -> float:
        """Calculate optimal confidence threshold based on historical performance"""
        analysis = self.get_confidence_analysis()
        
        if not analysis:
            return 0.7  # Default 70%
        
        # Find confidence range with best risk-adjusted returns
        best_score = -float('inf')
        best_threshold = 0.7
        
        for confidence_range, stats in analysis.items():
            # Calculate score: win_rate * avg_pnl * trade_frequency
            frequency = stats['total_trades'] / max(len(self.recent_trades), 1)
            score = stats['win_rate'] * stats['avg_pnl_percent'] * frequency
            
            if score > best_score:
                best_score = score
                # Convert range to threshold (use lower bound of range)
                best_threshold = float(confidence_range.split('-')[0]) / 100
        
        return max(min(best_threshold, 0.95), 0.2)  # Clamp between 20% and 95%
    
    def get_source_performance(self) -> Dict[str, Any]:
        """Analyze performance by signal source"""
        performance = {}
        
        for source, trades in self.source_performance.items():
            if not trades:
                continue
            
            wins = sum(1 for t in trades if t['outcome'] == 'WIN')
            total = len(trades)
            win_rate = wins / total if total > 0 else 0
            
            # Average confidence and P&L
            confidences = [t['confidence'] for t in trades]
            pnls = [t['pnl_percent'] for t in trades if t['pnl_percent'] is not None]
            
            performance[source] = {
                'total_trades': total,
                'win_rate': win_rate,
                'avg_confidence': statistics.mean(confidences) if confidences else 0,
                'avg_pnl_percent': statistics.mean(pnls) if pnls else 0,
                'recent_trades': len([t for t in trades if self._is_recent(t['timestamp'])])
            }
        
        return performance
    
    def should_adjust_threshold(self, current_threshold: float) -> Tuple[bool, float, str]:
        """Determine if threshold should be adjusted"""
        optimal = self.get_optimal_confidence_threshold()
        
        # Only adjust if difference is significant (>5%)
        if abs(optimal - current_threshold) > 0.05:
            # Get recent performance at current threshold
            recent_trades = [
                t for t in self.recent_trades 
                if t['confidence'] >= current_threshold and self._is_recent(t['timestamp'])
            ]
            
            if len(recent_trades) >= 20:  # Have enough data
                recent_win_rate = sum(1 for t in recent_trades if t['outcome'] == 'WIN') / len(recent_trades)
                
                # Adjust if recent performance is poor
                if recent_win_rate < 0.4:  # Less than 40% win rate
                    reason = f"Recent win rate {recent_win_rate:.1%} below 40% at {current_threshold:.1%}"
                    return True, optimal, reason
                elif recent_win_rate > 0.7 and optimal > current_threshold:
                    # We can be more aggressive
                    reason = f"High win rate {recent_win_rate:.1%} allows increase to {optimal:.1%}"
                    return True, optimal, reason
        
        return False, current_threshold, ""
    
    def get_learning_insights(self) -> List[str]:
        """Generate insights from the shadow journal"""
        insights = []
        
        # Confidence analysis
        conf_analysis = self.get_confidence_analysis()
        if conf_analysis:
            best_range = max(conf_analysis.items(), key=lambda x: x[1]['win_rate'])
            insights.append(
                f"Best confidence range: {best_range[0]} with {best_range[1]['win_rate']:.1%} win rate"
            )
            
            # Check if higher confidence = better performance
            high_conf = [r for r in ['80-100', '70-80'] if r in conf_analysis]
            low_conf = [r for r in ['50-60', '60-70'] if r in conf_analysis]
            
            if high_conf and low_conf:
                high_win = statistics.mean([conf_analysis[r]['win_rate'] for r in high_conf])
                low_win = statistics.mean([conf_analysis[r]['win_rate'] for r in low_conf])
                
                if high_win > low_win + 0.1:
                    insights.append("Higher confidence signals significantly outperform lower ones")
                elif high_win < low_win - 0.1:
                    insights.append("Lower confidence signals performing better - consider strategy review")
        
        # Source analysis
        source_perf = self.get_source_performance()
        if source_perf:
            best_source = max(source_perf.items(), key=lambda x: x[1]['win_rate'])
            insights.append(
                f"Best signal source: {best_source[0]} with {best_source[1]['win_rate']:.1%} win rate"
            )
        
        # Recent trends
        recent_trades = [t for t in self.recent_trades if self._is_recent(t['timestamp'])]
        if len(recent_trades) >= 10:
            recent_win_rate = sum(1 for t in recent_trades if t['outcome'] == 'WIN') / len(recent_trades)
            if recent_win_rate < 0.3:
                insights.append("⚠️ Recent win rate below 30% - consider reducing position sizes")
            elif recent_win_rate > 0.7:
                insights.append("🔥 Recent win rate above 70% - strategy performing well")
        
        return insights
    
    def _get_confidence_bucket(self, confidence: float) -> str:
        """Group confidence into buckets"""
        conf_int = int(confidence * 100)
        
        if conf_int >= 90:
            return '90-100'
        elif conf_int >= 80:
            return '80-90'
        elif conf_int >= 70:
            return '70-80'
        elif conf_int >= 60:
            return '60-70'
        elif conf_int >= 50:
            return '50-60'
        else:
            return '0-50'
    
    def _is_recent(self, timestamp: str, days: int = 30) -> bool:
        """Check if trade is recent"""
        try:
            trade_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return datetime.now() - trade_date < timedelta(days=days)
        except:
            return False
    
    def _load_journal(self) -> None:
        """Load existing journal from file"""
        try:
            if os.path.exists(self.journal_file):
                with open(self.journal_file, 'r') as f:
                    data = json.load(f)
                    self.trades = data.get('trades', [])
                    
                    # Rebuild indices
                    for trade in self.trades:
                        self.recent_trades.append(trade)
                        
                        confidence_range = self._get_confidence_bucket(trade['confidence'])
                        self.confidence_buckets[confidence_range].append(trade)
                        
                        source = trade.get('source', 'unknown')
                        self.source_performance[source].append(trade)
                    
                logger.info(f"Loaded {len(self.trades)} trades from shadow journal")
        except Exception as e:
            logger.error(f"Error loading shadow journal: {e}")
    
    def _save_journal(self) -> None:
        """Save journal to file"""
        try:
            data = {
                'trades': self.trades,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.journal_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving shadow journal: {e}")
    
    def generate_report(self) -> str:
        """Generate a comprehensive report"""
        report = []
        report.append("=" * 60)
        report.append("PHASMA AI - SHADOW JOURNAL REPORT")
        report.append("=" * 60)
        report.append(f"Total Trades: {len(self.trades)}")
        report.append(f"Recent Trades (30d): {len([t for t in self.trades if self._is_recent(t['timestamp'])])}")
        report.append("")
        
        # Confidence analysis
        report.append("CONFIDENCE ANALYSIS:")
        conf_analysis = self.get_confidence_analysis()
        for range_name, stats in sorted(conf_analysis.items()):
            report.append(
                f"  {range_name}%: {stats['win_rate']:.1%} win rate "
                f"({stats['wins']}/{stats['total_trades']}) "
                f"Avg P&L: {stats['avg_pnl_percent']:+.1%}"
            )
        report.append("")
        
        # Optimal threshold
        optimal = self.get_optimal_confidence_threshold()
        report.append(f"OPTIMAL CONFIDENCE THRESHOLD: {optimal:.1%}")
        report.append("")
        
        # Source performance
        report.append("SOURCE PERFORMANCE:")
        source_perf = self.get_source_performance()
        for source, stats in sorted(source_perf.items(), key=lambda x: x[1]['win_rate'], reverse=True):
            report.append(
                f"  {source}: {stats['win_rate']:.1%} win rate "
                f"({stats['total_trades']} trades) "
                f"Avg conf: {stats['avg_confidence']:.1%}"
            )
        report.append("")
        
        # Insights
        report.append("LEARNING INSIGHTS:")
        for insight in self.get_learning_insights():
            report.append(f"  • {insight}")
        
        return "\n".join(report)

# Global journal instance
shadow_journal = ShadowJournal()
