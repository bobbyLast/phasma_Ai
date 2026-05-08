"""
Paper Trading Portfolio Manager - Tracks AI performance without real money

This module simulates trading with virtual money to track AI performance.
All trades are simulated but use real market data for execution prices.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import yfinance as yf
from engines.paper_trading_verifier import PaperTradingVerifier

class PaperTradingPortfolio:
    """Paper trading portfolio manager for tracking AI performance"""
    
    def __init__(self, config: dict = None, state_file: str = None):
        self.config = config or {}
        
        # Data files
        if state_file:
            self.portfolio_file = state_file
            self.trade_log_file = state_file.replace('paper_portfolio', 'paper_trades').replace('.json', '.json')
        else:
            self.portfolio_file = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'paper_portfolio', 'paper_portfolio_state.json'
            )
            self.trade_log_file = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'paper_portfolio', 'paper_trade_log.json'
            )
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.trade_log_file), exist_ok=True)
        
        # Initialize verifier
        self.verifier = PaperTradingVerifier()
        
        # Load or initialize state
        self.state = self._load_portfolio_state()
        self.trades = self._load_trade_log()
        
        # Initialize if new
        if not self.state:
            self.state = self._initialize_portfolio()
    
    def _load_portfolio_state(self) -> Dict:
        """Load portfolio state from file"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _load_trade_log(self) -> List[Dict]:
        """Load trade execution log"""
        if os.path.exists(self.trade_log_file):
            try:
                with open(self.trade_log_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _initialize_portfolio(self) -> Dict:
        """Initialize new paper trading portfolio"""
        starting_capital = self.config.get('paper_trading', {}).get('starting_capital', 10000)
        
        return {
            'starting_capital': starting_capital,
            'available_capital': starting_capital,
            'realized_pnl': 0.0,
            'unrealized_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'open_positions': {},
            'last_updated': datetime.now().isoformat(),
            'performance_metrics': {
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'current_drawdown': 0.0
            },
            'daily_pnl': [],  # Track daily P&L
            'monthly_returns': {}  # Track monthly returns
        }
    
    def execute_buy(self, symbol: str, quantity: int, price: float = None, 
                   signal_data: Dict = None, confidence: float = None) -> Dict:
        """
        Execute a simulated buy order
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            price: Optional price (if None, uses market price)
            signal_data: AI signal data that triggered the trade
            confidence: AI confidence score (0-100)
        
        Returns:
            Dict with execution details
        """
        # Get market price if not provided
        if price is None:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if len(hist) > 0:
                    price = float(hist['Close'].iloc[-1])
                else:
                    return {
                        'success': False,
                        'error': f'Could not get market price for {symbol}'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Error fetching price for {symbol}: {e}'
                }
        
        # Calculate cost
        cost = quantity * price
        
        # Check if enough capital
        if cost > self.state['available_capital']:
            return {
                'success': False,
                'error': f'Insufficient capital: need ${cost:.2f}, have ${self.state["available_capital"]:.2f}'
            }
        
        # Create position if doesn't exist
        if symbol not in self.state['open_positions']:
            self.state['open_positions'][symbol] = {
                'quantity': 0,
                'avg_cost': 0.0,
                'total_cost': 0.0,
                'entry_date': None,
                'signals': [],
                'first_buy_date': None
            }
        
        # Update position
        position = self.state['open_positions'][symbol]
        old_quantity = position['quantity']
        old_total_cost = position['total_cost']
        
        position['quantity'] += quantity
        position['total_cost'] += cost
        position['avg_cost'] = position['total_cost'] / position['quantity']
        
        if position['entry_date'] is None:
            position['entry_date'] = datetime.now().isoformat()
            position['first_buy_date'] = datetime.now().isoformat()
        
        # Update available capital
        self.state['available_capital'] -= cost
        
        # Record trade with AI decision data
        trade = {
            'id': len(self.trades) + 1,
            'timestamp': datetime.now().isoformat(),
            'action': 'BUY',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total_cost': cost,
            'signal_data': signal_data or {},
            'confidence': confidence,
            'position_after': {
                'quantity': position['quantity'],
                'avg_cost': position['avg_cost'],
                'total_cost': position['total_cost']
            },
            'paper_trade': True
        }
        self.trades.append(trade)
        
        # Verify the trade
        verification = self.verifier.verify_trade_execution(trade)
        trade['verified'] = verification['verified']
        trade['verification_hash'] = verification['hash']
        
        # Update state
        self.state['last_updated'] = datetime.now().isoformat()
        self._save_portfolio()
        self._save_trades()
        
        # Log the AI decision
        self._log_ai_decision(symbol, 'BUY', quantity, price, signal_data, confidence)
        
        return {
            'success': True,
            'trade_id': trade['id'],
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total_cost': cost,
            'remaining_capital': self.state['available_capital'],
            'paper_trade': True
        }
    
    def execute_sell(self, symbol: str, quantity: int = None, price: float = None, 
                    reason: str = None, signal_data: Dict = None) -> Dict:
        """
        Execute a simulated sell order
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares (if None, sells all)
            price: Optional price (if None, uses market price)
            reason: Reason for selling
            signal_data: AI signal data that triggered the sell
        
        Returns:
            Dict with execution details and P&L
        """
        # Get market price if not provided
        if price is None:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if len(hist) > 0:
                    price = float(hist['Close'].iloc[-1])
                else:
                    return {
                        'success': False,
                        'error': f'Could not get market price for {symbol}'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Error fetching price for {symbol}: {e}'
                }
        
        # Check if position exists
        if symbol not in self.state['open_positions']:
            return {
                'success': False,
                'error': f'No position in {symbol}'
            }
        
        position = self.state['open_positions'][symbol]
        
        # Default to selling all shares
        if quantity is None:
            quantity = position['quantity']
        
        # Check if enough shares
        if quantity > position['quantity']:
            return {
                'success': False,
                'error': f'Insufficient shares: have {position["quantity"]}, trying to sell {quantity}'
            }
        
        # Calculate proceeds and P&L
        proceeds = quantity * price
        cost_basis = quantity * position['avg_cost']
        realized_pnl = proceeds - cost_basis
        realized_pct = (realized_pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        # Update position
        position['quantity'] -= quantity
        
        # Remove position if fully closed
        if position['quantity'] == 0:
            del self.state['open_positions'][symbol]
        else:
            # Adjust total cost
            position['total_cost'] = position['quantity'] * position['avg_cost']
        
        # Update capital and P&L
        self.state['available_capital'] += proceeds
        self.state['realized_pnl'] += realized_pnl
        self.state['total_trades'] += 1
        
        if realized_pnl > 0:
            self.state['winning_trades'] += 1
        else:
            self.state['losing_trades'] += 1
        
        # Update performance metrics
        self._update_performance_metrics(realized_pnl)
        
        # Record trade
        trade = {
            'id': len(self.trades) + 1,
            'timestamp': datetime.now().isoformat(),
            'action': 'SELL',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total_proceeds': proceeds,
            'cost_basis': cost_basis,
            'realized_pnl': realized_pnl,
            'realized_pct': realized_pct,
            'reason': reason,
            'signal_data': signal_data or {},
            'position_before': {
                'quantity': position['quantity'] + quantity,
                'avg_cost': position['avg_cost']
            },
            'paper_trade': True
        }
        self.trades.append(trade)
        
        # Verify the trade
        verification = self.verifier.verify_trade_execution(trade)
        trade['verified'] = verification['verified']
        trade['verification_hash'] = verification['hash']
        
        # Calculate new unrealized P&L
        self._update_unrealized_pnl()
        
        # Update daily P&L
        self._update_daily_pnl()
        
        # Save state
        self.state['last_updated'] = datetime.now().isoformat()
        self._save_portfolio()
        self._save_trades()
        
        # Log the AI decision
        self._log_ai_decision(symbol, 'SELL', quantity, price, signal_data, None, realized_pnl)
        
        return {
            'success': True,
            'trade_id': trade['id'],
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'proceeds': proceeds,
            'realized_pnl': realized_pnl,
            'realized_pct': realized_pct,
            'total_realized_pnl': self.state['realized_pnl'],
            'available_capital': self.state['available_capital'],
            'paper_trade': True
        }
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary with detailed performance metrics"""
        # Update unrealized P&L
        self._update_unrealized_pnl()
        
        total_value = (self.state['available_capital'] + 
                      self.state['realized_pnl'] + 
                      self.state['unrealized_pnl'])
        
        # Calculate additional metrics
        total_return = total_value - self.state['starting_capital']
        total_return_pct = ((total_value - self.state['starting_capital']) / 
                           self.state['starting_capital'] * 100)
        
        # Calculate win rate
        win_rate = (self.state['winning_trades'] / 
                   max(1, self.state['total_trades']) * 100)
        
        # Calculate profit factor
        gross_profit = sum(t['realized_pnl'] for t in self.trades 
                          if t['action'] == 'SELL' and t['realized_pnl'] > 0)
        gross_loss = abs(sum(t['realized_pnl'] for t in self.trades 
                           if t['action'] == 'SELL' and t['realized_pnl'] < 0))
        profit_factor = gross_profit / max(gross_loss, 1)
        
        # Get verification status
        verification_status = self.verifier.check_integrity()
        
        return {
            'starting_capital': self.state['starting_capital'],
            'available_capital': self.state['available_capital'],
            'realized_pnl': self.state['realized_pnl'],
            'unrealized_pnl': self.state['unrealized_pnl'],
            'total_portfolio_value': total_value,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_trades': self.state['total_trades'],
            'winning_trades': self.state['winning_trades'],
            'losing_trades': self.state['losing_trades'],
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'open_positions_count': len(self.state['open_positions']),
            'open_positions': self._get_open_positions_details(),
            'performance_metrics': self.state['performance_metrics'],
            'daily_pnl': self.state['daily_pnl'][-30:],  # Last 30 days
            'ai_performance': self._get_ai_performance_stats(),
            'verification': verification_status
        }
    
    def _get_ai_performance_stats(self) -> Dict:
        """Analyze AI decision performance"""
        buy_trades = [t for t in self.trades if t['action'] == 'BUY' and 'confidence' in t]
        sell_trades = [t for t in self.trades if t['action'] == 'SELL']
        
        if not buy_trades or not sell_trades:
            return {
                'avg_confidence': 0,
                'confidence_vs_return_corr': 0,
                'high_confidence_win_rate': 0,
                'low_confidence_win_rate': 0
            }
        
        # Average confidence
        avg_confidence = sum(t['confidence'] for t in buy_trades) / len(buy_trades)
        
        # Correlation between confidence and returns
        confidence_returns = []
        for buy in buy_trades:
            # Find matching sell
            matching_sells = [s for s in sell_trades 
                            if s['symbol'] == buy['symbol'] and 
                            s['timestamp'] > buy['timestamp']]
            if matching_sells:
                confidence_returns.append((buy['confidence'], matching_sells[0]['realized_pct']))
        
        if confidence_returns:
            confidences, returns = zip(*confidence_returns)
            correlation = pd.Series(confidences).corr(pd.Series(returns))
        else:
            correlation = 0
        
        # Win rates by confidence level
        high_conf_wins = sum(1 for c, r in confidence_returns 
                           if c > 80 and r > 0)
        high_conf_total = sum(1 for c, r in confidence_returns if c > 80)
        high_conf_win_rate = (high_conf_wins / max(high_conf_total, 1)) * 100
        
        low_conf_wins = sum(1 for c, r in confidence_returns 
                          if c <= 60 and r > 0)
        low_conf_total = sum(1 for c, r in confidence_returns if c <= 60)
        low_conf_win_rate = (low_conf_wins / max(low_conf_total, 1)) * 100
        
        return {
            'avg_confidence': avg_confidence,
            'confidence_vs_return_corr': correlation,
            'high_confidence_win_rate': high_conf_win_rate,
            'low_confidence_win_rate': low_conf_win_rate,
            'total_analyzed_trades': len(confidence_returns)
        }
    
    def _get_open_positions_details(self) -> List[Dict]:
        """Get detailed info about open positions"""
        positions = []
        
        for symbol, pos in self.state['open_positions'].items():
            # Get current price
            try:
                ticker = yf.Ticker(symbol)
                current_price = ticker.history(period='1d')['Close'].iloc[-1]
            except:
                current_price = pos['avg_cost']  # Fallback to cost
            
            unrealized_pnl = (current_price - pos['avg_cost']) * pos['quantity']
            unrealized_pct = ((current_price - pos['avg_cost']) / 
                            pos['avg_cost'] * 100)
            
            days_held = 0
            if pos.get('first_buy_date'):
                days_held = (datetime.now() - datetime.fromisoformat(pos['first_buy_date'])).days
            
            positions.append({
                'symbol': symbol,
                'quantity': pos['quantity'],
                'avg_cost': pos['avg_cost'],
                'current_price': current_price,
                'market_value': current_price * pos['quantity'],
                'cost_basis': pos['total_cost'],
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pct': unrealized_pct,
                'entry_date': pos['entry_date'],
                'days_held': days_held
            })
        
        return positions
    
    def _update_unrealized_pnl(self):
        """Calculate current unrealized P&L on all open positions"""
        total_unrealized = 0.0
        
        for symbol, pos in self.state['open_positions'].items():
            try:
                ticker = yf.Ticker(symbol)
                current_price = ticker.history(period='1d')['Close'].iloc[-1]
                unrealized = (current_price - pos['avg_cost']) * pos['quantity']
                total_unrealized += unrealized
            except:
                # If can't get price, assume 0 unrealized
                pass
        
        self.state['unrealized_pnl'] = total_unrealized
    
    def _update_performance_metrics(self, pnl: float):
        """Update performance metrics after a trade"""
        metrics = self.state['performance_metrics']
        
        if pnl > 0:
            metrics['avg_win'] = ((metrics['avg_win'] * self.state['winning_trades'] + pnl) / 
                                (self.state['winning_trades'] + 1))
            metrics['largest_win'] = max(metrics['largest_win'], pnl)
        else:
            losing_trades = self.state['total_trades'] - self.state['winning_trades']
            if losing_trades > 0:
                metrics['avg_loss'] = ((metrics['avg_loss'] * losing_trades + pnl) / 
                                     (losing_trades + 1))
            metrics['largest_loss'] = min(metrics['largest_loss'], pnl)
        
        metrics['win_rate'] = (self.state['winning_trades'] / 
                              max(1, self.state['total_trades']) * 100)
    
    def _update_daily_pnl(self):
        """Update daily P&L tracking"""
        today = datetime.now().date().isoformat()
        
        # Find today's P&L
        today_pnl = 0
        for trade in self.trades[-10:]:  # Check last 10 trades
            if trade['timestamp'].startswith(today) and trade['action'] == 'SELL':
                today_pnl += trade.get('realized_pnl', 0)
        
        # Update or add today's P&L
        if self.state['daily_pnl'] and self.state['daily_pnl'][-1]['date'] == today:
            self.state['daily_pnl'][-1]['pnl'] = today_pnl
        else:
            self.state['daily_pnl'].append({
                'date': today,
                'pnl': today_pnl
            })
        
        # Keep only last 90 days
        self.state['daily_pnl'] = self.state['daily_pnl'][-90:]
    
    def _log_ai_decision(self, symbol: str, action: str, quantity: int, price: float,
                        signal_data: Dict, confidence: float = None, pnl: float = None):
        """Log AI decision for analysis"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'signal_data': signal_data,
            'confidence': confidence,
            'pnl': pnl  # Only for sells
        }
        
        # Save to AI decisions log
        decisions_file = os.path.join(
            os.path.dirname(self.portfolio_file), 'ai_decisions.json'
        )
        
        decisions = []
        if os.path.exists(decisions_file):
            try:
                with open(decisions_file, 'r') as f:
                    decisions = json.load(f)
            except:
                pass
        
        decisions.append(log_entry)
        
        # Keep last 1000 decisions
        decisions = decisions[-1000:]
        
        with open(decisions_file, 'w') as f:
            json.dump(decisions, f, indent=2)
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get recent trade history"""
        return self.trades[-limit:] if self.trades else []
    
    def get_performance_report(self) -> str:
        """Generate a formatted performance report"""
        summary = self.get_portfolio_summary()
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    PAPER TRADING PERFORMANCE                ║
╚══════════════════════════════════════════════════════════════╝

Starting Capital: ${summary['starting_capital']:,.2f}
Current Value:    ${summary['total_portfolio_value']:,.2f}
Total Return:      ${summary['total_return']:,.2f} ({summary['total_return_pct']:+.2f}%)

Realized P&L:      ${summary['realized_pnl']:,.2f}
Unrealized P&L:    ${summary['unrealized_pnl']:,.2f}
Available Cash:    ${summary['available_capital']:,.2f}

Trading Statistics:
─────────────────
Total Trades:      {summary['total_trades']}
Winning Trades:    {summary['winning_trades']}
Losing Trades:     {summary['losing_trades']}
Win Rate:          {summary['win_rate']:.1f}%
Profit Factor:     {summary['profit_factor']:.2f}

Open Positions:    {summary['open_positions_count']}

AI Performance:
─────────────────
Avg Confidence:    {summary['ai_performance']['avg_confidence']:.1f}%
Conf/Return Corr:  {summary['ai_performance']['confidence_vs_return_corr']:.2f}
High Conf Win Rate: {summary['ai_performance']['high_confidence_win_rate']:.1f}%
Low Conf Win Rate:  {summary['ai_performance']['low_confidence_win_rate']:.1f}%

Recent Trades:
─────────────────
"""
        
        recent_trades = self.get_trade_history(5)
        for trade in recent_trades:
            if trade['action'] == 'SELL':
                report += f"{trade['timestamp'][:10]} {trade['symbol']} {trade['action']} {trade['quantity']} @ ${trade['price']:.2f} P&L: ${trade['realized_pnl']:+.2f}\n"
        
        return report
    
    def _save_portfolio(self):
        """Save portfolio state to file"""
        try:
            with open(self.portfolio_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Error saving paper portfolio: {e}")
    
    def _save_trades(self):
        """Save trade log to file"""
        try:
            with open(self.trade_log_file, 'w') as f:
                json.dump(self.trades, f, indent=2)
        except Exception as e:
            print(f"Error saving paper trades: {e}")
    
    def reset_portfolio(self, new_capital: float = None):
        """Reset portfolio with new capital"""
        if new_capital:
            self.config['paper_trading']['starting_capital'] = new_capital
        
        self.state = self._initialize_portfolio()
        self.trades = []
        self._save_portfolio()
        self._save_trades()
        
        print(f"Paper trading portfolio reset with ${self.state['starting_capital']:,.2f}")

# Helper function to get paper trading portfolio
def get_paper_trading_portfolio(config: dict = None) -> PaperTradingPortfolio:
    """Get or create paper trading portfolio instance"""
    return PaperTradingPortfolio(config)
