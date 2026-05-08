"""
Performance Tracker - Win Rate and Trading Metrics
Implements AI Feedback: Performance tracking and analytics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics

class PerformanceTracker:
    """Track trading performance metrics and win rates"""
    
    def __init__(self, trade_db=None):
        """Initialize performance tracker"""
        self.trade_db = trade_db
        self.logger = logging.getLogger(__name__)
        
    def calculate_win_rate(self, period_days: int = 30) -> float:
        """
        Calculate win rate over specified period
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            Win rate as decimal (0.0 to 1.0)
        """
        if not self.trade_db:
            self.logger.warning("No trade database available")
            return 0.0
            
        try:
            trades = self.trade_db.get_trades_last_n_days(period_days)
            
            if not trades:
                return 0.0
                
            wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
            return wins / len(trades)
            
        except Exception as e:
            self.logger.error(f"Error calculating win rate: {e}")
            return 0.0
    
    def calculate_profit_factor(self, period_days: int = 30) -> float:
        """
        Calculate profit factor (gross profit / gross loss)
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            Profit factor (>1.0 is profitable)
        """
        if not self.trade_db:
            return 0.0
            
        try:
            trades = self.trade_db.get_trades_last_n_days(period_days)
            
            if not trades:
                return 0.0
                
            gross_profit = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
            gross_loss = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))
            
            if gross_loss == 0:
                return float('inf') if gross_profit > 0 else 0.0
                
            return gross_profit / gross_loss
            
        except Exception as e:
            self.logger.error(f"Error calculating profit factor: {e}")
            return 0.0
    
    def calculate_avg_win_loss_ratio(self, period_days: int = 30) -> float:
        """
        Calculate average win to average loss ratio
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            Win/loss ratio
        """
        if not self.trade_db:
            return 0.0
            
        try:
            trades = self.trade_db.get_trades_last_n_days(period_days)
            
            if not trades:
                return 0.0
                
            wins = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0]
            losses = [abs(t.get('pnl', 0)) for t in trades if t.get('pnl', 0) < 0]
            
            if not wins or not losses:
                return 0.0
                
            avg_win = statistics.mean(wins)
            avg_loss = statistics.mean(losses)
            
            return avg_win / avg_loss if avg_loss > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating win/loss ratio: {e}")
            return 0.0
    
    def calculate_sharpe_ratio(self, period_days: int = 30, risk_free_rate: float = 0.04) -> float:
        """
        Calculate Sharpe ratio
        
        Args:
            period_days: Number of days to analyze
            risk_free_rate: Annual risk-free rate (default 4%)
            
        Returns:
            Sharpe ratio
        """
        if not self.trade_db:
            return 0.0
            
        try:
            trades = self.trade_db.get_trades_last_n_days(period_days)
            
            if not trades or len(trades) < 2:
                return 0.0
                
            returns = [t.get('return_pct', 0) for t in trades if 'return_pct' in t]
            
            if not returns:
                return 0.0
                
            avg_return = statistics.mean(returns)
            std_return = statistics.stdev(returns) if len(returns) > 1 else 0.0
            
            if std_return == 0:
                return 0.0
                
            # Annualize
            daily_rf = risk_free_rate / 252
            sharpe = (avg_return - daily_rf) / std_return
            
            return sharpe * (252 ** 0.5)  # Annualized
            
        except Exception as e:
            self.logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0
    
    def calculate_max_drawdown(self, period_days: int = 30) -> float:
        """
        Calculate maximum drawdown
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            Max drawdown as decimal (negative value)
        """
        if not self.trade_db:
            return 0.0
            
        try:
            trades = self.trade_db.get_trades_last_n_days(period_days)
            
            if not trades:
                return 0.0
                
            # Calculate cumulative equity
            equity = [10000]  # Starting capital
            for trade in sorted(trades, key=lambda x: x.get('timestamp', datetime.now())):
                equity.append(equity[-1] + trade.get('pnl', 0))
            
            # Find max drawdown
            peak = equity[0]
            max_dd = 0.0
            
            for value in equity:
                if value > peak:
                    peak = value
                dd = (value - peak) / peak
                if dd < max_dd:
                    max_dd = dd
                    
            return max_dd
            
        except Exception as e:
            self.logger.error(f"Error calculating max drawdown: {e}")
            return 0.0
    
    def get_performance_report(self, period_days: int = 30) -> Dict:
        """
        Get comprehensive performance report
        
        Args:
            period_days: Number of days to analyze
            
        Returns:
            Dictionary with all performance metrics
        """
        report = {
            'period_days': period_days,
            'win_rate': self.calculate_win_rate(period_days),
            'profit_factor': self.calculate_profit_factor(period_days),
            'avg_win_loss_ratio': self.calculate_avg_win_loss_ratio(period_days),
            'sharpe_ratio': self.calculate_sharpe_ratio(period_days),
            'max_drawdown': self.calculate_max_drawdown(period_days),
            'timestamp': datetime.now().isoformat()
        }
        
        # Calculate total PnL
        if self.trade_db:
            try:
                trades = self.trade_db.get_trades_last_n_days(period_days)
                report['total_trades'] = len(trades)
                report['total_pnl'] = sum(t.get('pnl', 0) for t in trades)
                report['winning_trades'] = sum(1 for t in trades if t.get('pnl', 0) > 0)
                report['losing_trades'] = sum(1 for t in trades if t.get('pnl', 0) < 0)
            except Exception as e:
                self.logger.error(f"Error calculating additional metrics: {e}")
        
        return report
    
    def print_performance_report(self, period_days: int = 30):
        """Print formatted performance report"""
        report = self.get_performance_report(period_days)
        
        print("\n" + "="*60)
        print(f"PERFORMANCE REPORT - Last {period_days} Days")
        print("="*60)
        print(f"Total Trades: {report.get('total_trades', 0)}")
        print(f"Winning Trades: {report.get('winning_trades', 0)}")
        print(f"Losing Trades: {report.get('losing_trades', 0)}")
        print(f"\nWin Rate: {report['win_rate']:.1%}")
        print(f"Profit Factor: {report['profit_factor']:.2f}")
        print(f"Avg Win/Loss Ratio: {report['avg_win_loss_ratio']:.2f}")
        print(f"Sharpe Ratio: {report['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {report['max_drawdown']:.1%}")
        print(f"Total P&L: ${report.get('total_pnl', 0):.2f}")
        print("="*60 + "\n")
