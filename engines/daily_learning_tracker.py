#!/usr/bin/env python3
"""
Daily Learning Tracker - AI learns from all trades and reports ROI at market close
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

class DailyLearningTracker:
    """Track all trades, learn from wins/losses, and report daily ROI"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Storage paths
        self.data_dir = 'phasma_core_memory/daily_learning'
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Daily tracking
        self.today_trades = []
        self.today_signals = []
        self.today_tickers_found = set()
        self.today_start_balance = 0
        self.today_current_balance = 0
        
        # Learning memory
        self.learning_memory = self._load_learning_memory()
        
        print("📚 Daily Learning Tracker Initialized")
    
    def _load_learning_memory(self) -> Dict:
        """Load historical learning data"""
        memory_file = os.path.join(self.data_dir, 'learning_memory.json')
        try:
            if os.path.exists(memory_file):
                with open(memory_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading learning memory: {e}")
        
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0,
            'total_loss': 0,
            'best_trade': None,
            'worst_trade': None,
            'patterns': {
                'winning_confidence_avg': 0,
                'losing_confidence_avg': 0,
                'best_sources': {},
                'worst_sources': {}
            }
        }
    
    def _save_learning_memory(self):
        """Save learning memory to disk"""
        memory_file = os.path.join(self.data_dir, 'learning_memory.json')
        try:
            with open(memory_file, 'w') as f:
                json.dump(self.learning_memory, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving learning memory: {e}")
    
    def start_trading_day(self, starting_balance: float):
        """Start a new trading day"""
        self.today_trades = []
        self.today_signals = []
        self.today_tickers_found = set()
        self.today_start_balance = starting_balance
        self.today_current_balance = starting_balance
        
        print(f"\n📅 TRADING DAY STARTED")
        print(f"   Date: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"   Starting Balance: ${starting_balance:,.2f}")
    
    def record_ticker_found(self, symbol: str, source: str, confidence: float):
        """Record a ticker that was found/analyzed"""
        self.today_tickers_found.add(symbol)
        self.today_signals.append({
            'symbol': symbol,
            'source': source,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        })
    
    def record_trade(self, trade_data: Dict):
        """Record a trade execution"""
        trade_record = {
            'symbol': trade_data.get('symbol'),
            'action': trade_data.get('action'),
            'quantity': trade_data.get('quantity'),
            'entry_price': trade_data.get('entry_price'),
            'confidence': trade_data.get('confidence'),
            'source': trade_data.get('source', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'exit_price': None,
            'pnl': None,
            'pnl_percent': None,
            'status': 'OPEN'
        }
        
        self.today_trades.append(trade_record)
        print(f"📝 TRADE RECORDED: {trade_record['symbol']} {trade_record['action']} @ ${trade_record['entry_price']:.2f}")
    
    def record_trade_exit(self, symbol: str, exit_price: float, exit_reason: str):
        """Record a trade exit and learn from it"""
        for trade in self.today_trades:
            if trade['symbol'] == symbol and trade['status'] == 'OPEN':
                trade['exit_price'] = exit_price
                trade['exit_reason'] = exit_reason
                trade['status'] = 'CLOSED'
                
                # Calculate P&L
                entry_cost = trade['entry_price'] * trade['quantity']
                exit_value = exit_price * trade['quantity']
                
                if trade['action'] == 'BUY':
                    trade['pnl'] = exit_value - entry_cost
                else:
                    trade['pnl'] = entry_cost - exit_value
                
                trade['pnl_percent'] = (trade['pnl'] / entry_cost) * 100
                
                # Learn from this trade
                self._learn_from_trade(trade)
                
                print(f"📊 TRADE CLOSED: {symbol}")
                print(f"   P&L: ${trade['pnl']:+.2f} ({trade['pnl_percent']:+.2f}%)")
                
                return trade
        return None
    
    def _learn_from_trade(self, trade: Dict):
        """Learn from a completed trade"""
        is_win = trade['pnl'] > 0
        
        # Update totals
        self.learning_memory['total_trades'] += 1
        
        if is_win:
            self.learning_memory['winning_trades'] += 1
            self.learning_memory['total_profit'] += trade['pnl']
        else:
            self.learning_memory['losing_trades'] += 1
            self.learning_memory['total_loss'] += abs(trade['pnl'])
        
        # Save learning
        self._save_learning_memory()
        print(f"🧠 AI LEARNED: {'WIN' if is_win else 'LOSS'} pattern recorded")
    
    def get_daily_roi_summary(self, current_balance: float) -> Dict:
        """Generate end-of-day ROI summary"""
        self.today_current_balance = current_balance
        
        # Calculate daily P&L
        daily_pnl = current_balance - self.today_start_balance
        daily_roi_percent = (daily_pnl / self.today_start_balance) * 100 if self.today_start_balance > 0 else 0
        
        # Count open trades
        open_trades = [t for t in self.today_trades if t['status'] == 'OPEN']
        closed_trades = [t for t in self.today_trades if t['status'] == 'CLOSED']
        
        # Count wins/losses
        wins = [t for t in closed_trades if t['pnl'] > 0]
        losses = [t for t in closed_trades if t['pnl'] <= 0]
        
        summary = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'starting_balance': self.today_start_balance,
            'ending_balance': current_balance,
            'daily_pnl': daily_pnl,
            'daily_roi_percent': daily_roi_percent,
            'total_tickers_found': len(self.today_tickers_found),
            'total_signals': len(self.today_signals),
            'total_trades': len(self.today_trades),
            'open_trades': len(open_trades),
            'closed_trades': len(closed_trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins) / len(closed_trades) * 100) if closed_trades else 0
        }
        
        return summary
    
    def print_daily_roi_report(self, current_balance: float):
        """Print end-of-day ROI report"""
        summary = self.get_daily_roi_summary(current_balance)
        
        print("\n" + "="*60)
        print("📊 END OF DAY ROI REPORT")
        print("="*60)
        print(f"📅 Date: {summary['date']}")
        print(f"💰 Starting Balance: ${summary['starting_balance']:,.2f}")
        print(f"💰 Ending Balance: ${summary['ending_balance']:,.2f}")
        print(f"📈 Daily P&L: ${summary['daily_pnl']:+,.2f}")
        print(f"📊 Daily ROI: {summary['daily_roi_percent']:+.2f}%")
        print(f"\n🎯 Trading Activity:")
        print(f"   Tickers Found: {summary['total_tickers_found']}")
        print(f"   Signals Generated: {summary['total_signals']}")
        print(f"   Total Trades: {summary['total_trades']}")
        print(f"   Open Trades: {summary['open_trades']}")
        print(f"   Closed Trades: {summary['closed_trades']}")
        print(f"\n🏆 Performance:")
        print(f"   Wins: {summary['wins']}")
        print(f"   Losses: {summary['losses']}")
        print(f"   Win Rate: {summary['win_rate']:.1f}%")
        print("="*60)
        
        # Save daily report
        report_file = os.path.join(self.data_dir, f"daily_report_{summary['date']}.json")
        try:
            with open(report_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            print(f"📁 Report saved: {report_file}")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")
        
        # Update learning memory
        self.learning_memory['daily_history'].append(summary)
        self._save_learning_memory()
    
    def get_confidence_adjustment(self, source: str) -> float:
        """Get AI-learned confidence adjustment"""
        # Simple adjustment based on historical performance
        if source in self.learning_memory['patterns'].get('best_sources', {}):
            return 5.0  # Boost confidence for good sources
        elif source in self.learning_memory['patterns'].get('worst_sources', {}):
            return -5.0  # Reduce confidence for bad sources
        return 0.0
