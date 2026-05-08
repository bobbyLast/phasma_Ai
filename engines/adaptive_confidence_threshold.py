import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

class AdaptiveConfidenceThreshold:
    """
    Dynamically adjusts confidence threshold based on historical performance
    at different confidence levels.
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or 'config.json'
        self.performance_data = defaultdict(lambda: {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'avg_pnl': 0.0,
            'sharpe_ratio': 0.0
        })
        self.current_threshold = 55.0  # Start at 55%
        self.min_threshold = 50.0
        self.max_threshold = 75.0
        self.adjustment_period = 20  # Adjust after every 20 trades per level
        self.last_adjustment = datetime.now()
        
        # Load historical data
        self.load_performance_data()
        
    def load_performance_data(self):
        """Load historical performance data"""
        data_file = 'adaptive_threshold_performance.json'
        try:
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    for level, stats in data.items():
                        self.performance_data[float(level)] = stats
                print(f"📊 Loaded performance data for {len(data)} confidence levels")
        except Exception as e:
            print(f"⚠️ Could not load performance data: {e}")
    
    def save_performance_data(self):
        """Save performance data to file"""
        data_file = 'adaptive_threshold_performance.json'
        try:
            # Convert to regular dict for JSON serialization
            data = {str(k): v for k, v in self.performance_data.items()}
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save performance data: {e}")
    
    def record_trade_outcome(self, confidence: float, pnl: float, is_win: bool):
        """Record the outcome of a trade at a specific confidence level"""
        # Round confidence to nearest integer for grouping
        conf_level = round(confidence)
        
        stats = self.performance_data[conf_level]
        stats['trades'] += 1
        stats['total_pnl'] += pnl
        
        if is_win:
            stats['wins'] += 1
        else:
            stats['losses'] += 1
        
        # Update metrics
        if stats['trades'] > 0:
            stats['win_rate'] = stats['wins'] / stats['trades']
            stats['avg_pnl'] = stats['total_pnl'] / stats['trades']
            
            # Simple Sharpe ratio calculation (assuming 0% risk-free rate)
            if stats['trades'] > 1:
                returns = [pnl / 100.0 for pnl in [stats['total_pnl'] / stats['trades']]]  # Simplified
                if len(returns) > 1:
                    avg_return = sum(returns) / len(returns)
                    variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                    stats['sharpe_ratio'] = avg_return / (variance ** 0.5) if variance > 0 else 0
        
        print(f"📊 Recorded trade at {conf_level}% confidence: P&L ${pnl:.2f} ({'WIN' if is_win else 'LOSS'})")
        
        # Check if we should adjust threshold
        self.check_and_adjust_threshold()
    
    def check_and_adjust_threshold(self):
        """Check if we have enough data to adjust the threshold"""
        days_since_last = (datetime.now() - self.last_adjustment).days
        
        # Only adjust if we have enough trades and it's been at least 1 day
        if days_since_last < 1:
            return
        
        # Find confidence levels with sufficient trades
        valid_levels = []
        for level, stats in self.performance_data.items():
            if stats['trades'] >= self.adjustment_period:
                valid_levels.append((level, stats))
        
        if len(valid_levels) >= 2:  # Need at least 2 levels to compare
            self.adjust_threshold(valid_levels)
    
    def adjust_threshold(self, valid_levels: List[tuple]):
        """Adjust threshold based on performance"""
        print("\n🔧 ANALYZING PERFORMANCE FOR THRESHOLD ADJUSTMENT")
        print("=" * 60)
        
        # Sort by performance score (combination of win rate and avg P&L)
        def performance_score(stats):
            # Weight win rate (40%) and average P&L (60%)
            return (stats['win_rate'] * 0.4) + (min(stats['avg_pnl'] / 100, 1) * 0.6)
        
        # Sort by performance score
        sorted_levels = sorted(valid_levels, key=lambda x: performance_score(x[1]), reverse=True)
        
        print("📊 Performance by Confidence Level:")
        for level, stats in sorted_levels[:5]:  # Show top 5
            score = performance_score(stats)
            print(f"   {level}%: {stats['trades']} trades, "
                  f"Win Rate: {stats['win_rate']:.1%}, "
                  f"Avg P&L: ${stats['avg_pnl']:.2f}, "
                  f"Score: {score:.3f}")
        
        # Find the best performing level
        best_level, best_stats = sorted_levels[0]
        
        # Only adjust if significantly better than current
        current_performance = self.get_level_performance(self.current_threshold)
        best_performance = performance_score(best_stats)
        
        if best_performance > current_performance + 0.05:  # 5% improvement threshold
            old_threshold = self.current_threshold
            self.current_threshold = best_level
            self.last_adjustment = datetime.now()
            
            print(f"\n✅ ADJUSTING THRESHOLD: {old_threshold}% → {self.current_threshold}%")
            print(f"   Reason: {self.current_threshold}% shows better performance")
            
            # Update config file
            self.update_config_threshold()
            
            # Save performance data
            self.save_performance_data()
        else:
            print(f"\n✅ KEEPING CURRENT THRESHOLD: {self.current_threshold}%")
            print(f"   No significant improvement found")
    
    def get_level_performance(self, level: float) -> float:
        """Get performance score for a specific level"""
        level_rounded = round(level)
        stats = self.performance_data[level_rounded]
        
        if stats['trades'] == 0:
            return 0.0
        
        # Same scoring as in adjust_threshold
        return (stats['win_rate'] * 0.4) + (min(stats['avg_pnl'] / 100, 1) * 0.6)
    
    def update_config_threshold(self):
        """Update the threshold in config.json"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            config['paper_trading']['min_confidence_threshold'] = int(self.current_threshold)
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"💾 Updated config.json with new threshold: {self.current_threshold}%")
        except Exception as e:
            print(f"⚠️ Could not update config: {e}")
    
    def get_current_threshold(self) -> float:
        """Get the current confidence threshold"""
        return self.current_threshold
    
    def should_execute_trade(self, confidence: float) -> bool:
        """Check if a trade should be executed based on current threshold"""
        return confidence >= self.current_threshold
    
    def get_performance_summary(self) -> Dict:
        """Get a summary of performance across all levels"""
        summary = {
            'current_threshold': self.current_threshold,
            'total_trades': sum(stats['trades'] for stats in self.performance_data.values()),
            'levels_analyzed': len([s for s in self.performance_data.values() if s['trades'] > 0]),
            'best_level': None,
            'best_win_rate': 0,
            'best_avg_pnl': float('-inf')
        }
        
        for level, stats in self.performance_data.items():
            if stats['trades'] > 0:
                if stats['win_rate'] > summary['best_win_rate']:
                    summary['best_win_rate'] = stats['win_rate']
                    summary['best_level'] = level
                if stats['avg_pnl'] > summary['best_avg_pnl']:
                    summary['best_avg_pnl'] = stats['avg_pnl']
        
        return summary
    
    def print_status(self):
        """Print current status and performance"""
        print("\n📊 ADAPTIVE CONFIDENCE THRESHOLD STATUS")
        print("=" * 50)
        print(f"Current Threshold: {self.current_threshold}%")
        print(f"Last Adjustment: {self.last_adjustment.strftime('%Y-%m-%d %H:%M:%S')}")
        
        summary = self.get_performance_summary()
        print(f"Total Trades Analyzed: {summary['total_trades']}")
        print(f"Confidence Levels with Data: {summary['levels_analyzed']}")
        
        if summary['best_level']:
            print(f"Best Performing Level: {summary['best_level']}% "
                  f"(Win Rate: {summary['best_win_rate']:.1%}, "
                  f"Avg P&L: ${summary['best_avg_pnl']:.2f})")
