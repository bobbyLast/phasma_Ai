"""
Real Portfolio Manager - Tracks actual trades and positions

Fixes the critical bug where unrealized P&L was counted as real bankroll.
Now properly separates:
- Realized P&L (actual closed trades)
- Unrealized P&L (open positions)
- Available capital (actual bankroll)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import yfinance as yf

class RealPortfolioManager:
    """Portfolio manager that tracks real trades, not paper profits"""
    
    def __init__(self, config: dict = None, test_mode: bool = False, state_file: str = None):
        self.config = config or {}
        self.test_mode = test_mode
        
        # Data files - use test files if in test mode
        if test_mode and state_file:
            self.portfolio_file = state_file
            self.trade_log_file = state_file.replace('portfolio_state', 'trade_log').replace('.json', '.json')
        else:
            self.portfolio_file = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'portfolio', 'real_portfolio_state.json'
            )
            self.trade_log_file = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'trade_log.json'
            )
        
        # Load portfolio state
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
        """Initialize new portfolio"""
        return {
            'starting_capital': 50.0,
            'available_capital': 50.0,  # Actual cash available
            'realized_pnl': 0.0,        # Actual profit/loss from closed trades
            'unrealized_pnl': 0.0,      # Paper profit/loss on open positions
            'total_trades': 0,
            'winning_trades': 0,
            'open_positions': {},
            'last_updated': datetime.now().isoformat(),
            'performance_metrics': {
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0
            }
        }
    
    def execute_buy(self, symbol: str, quantity: int, price: float, 
                   signal_data: Dict = None) -> Dict:
        """
        Execute a buy order and record it
        
        Returns:
            Dict with execution details
        """
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
                'signals': []
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
        
        # Update available capital
        self.state['available_capital'] -= cost
        
        # Record trade
        trade = {
            'id': len(self.trades) + 1,
            'timestamp': datetime.now().isoformat(),
            'action': 'BUY',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total_cost': cost,
            'signal_data': signal_data,
            'position_after': {
                'quantity': position['quantity'],
                'avg_cost': position['avg_cost'],
                'total_cost': position['total_cost']
            }
        }
        self.trades.append(trade)
        
        # Update state
        self.state['last_updated'] = datetime.now().isoformat()
        self._save_portfolio()
        self._save_trades()
        
        return {
            'success': True,
            'trade_id': trade['id'],
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total_cost': cost,
            'remaining_capital': self.state['available_capital']
        }
    
    def execute_sell(self, symbol: str, quantity: int, price: float, 
                    reason: str = None) -> Dict:
        """
        Execute a sell order and calculate realized P&L
        
        Returns:
            Dict with execution details and P&L
        """
        # VALIDATION: Only allow real market prices in production
        if not self.test_mode:
            # Fetch current market price to validate
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if len(hist) > 0:
                    market_price = float(hist['Close'].iloc[-1])
                    # Check if provided price is close to market price (within 1%)
                    price_diff_pct = abs(price - market_price) / market_price * 100
                    if price_diff_pct > 1.0:
                        return {
                            'success': False,
                            'error': f'Price validation failed. Provided ${price:.2f} differs from market ${market_price:.2f} by {price_diff_pct:.1f}%'
                        }
                    # Use actual market price instead of provided price
                    price = market_price
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Could not validate market price: {e}'
                }
        
        # Check if position exists
        if symbol not in self.state['open_positions']:
            return {
                'success': False,
                'error': f'No position in {symbol}'
            }
        
        position = self.state['open_positions'][symbol]
        
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
            'reason': reason,
            'position_before': {
                'quantity': position['quantity'] + quantity,
                'avg_cost': position['avg_cost']
            }
        }
        self.trades.append(trade)
        
        # Calculate new unrealized P&L
        self._update_unrealized_pnl()
        
        # Save state
        self.state['last_updated'] = datetime.now().isoformat()
        self._save_portfolio()
        self._save_trades()
        
        return {
            'success': True,
            'trade_id': trade['id'],
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'proceeds': proceeds,
            'realized_pnl': realized_pnl,
            'total_realized_pnl': self.state['realized_pnl'],
            'available_capital': self.state['available_capital']
        }
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary with proper P&L separation"""
        # Update unrealized P&L
        self._update_unrealized_pnl()
        
        total_value = (self.state['available_capital'] + 
                      self.state['realized_pnl'] + 
                      self.state['unrealized_pnl'])
        
        return {
            'starting_capital': self.state['starting_capital'],
            'available_capital': self.state['available_capital'],
            'realized_pnl': self.state['realized_pnl'],
            'unrealized_pnl': self.state['unrealized_pnl'],
            'total_portfolio_value': total_value,
            'total_return': total_value - self.state['starting_capital'],
            'total_return_pct': ((total_value - self.state['starting_capital']) / 
                               self.state['starting_capital'] * 100),
            'total_trades': self.state['total_trades'],
            'winning_trades': self.state['winning_trades'],
            'win_rate': (self.state['winning_trades'] / 
                        max(1, self.state['total_trades']) * 100),
            'open_positions_count': len(self.state['open_positions']),
            'open_positions': self._get_open_positions_details(),
            'performance_metrics': self.state['performance_metrics']
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
                'days_held': (datetime.now() - datetime.fromisoformat(pos['entry_date'])).days
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
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get recent trade history"""
        return self.trades[-limit:] if self.trades else []
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get details of a specific position"""
        if symbol not in self.state['open_positions']:
            return None
        
        pos = self.state['open_positions'][symbol]
        
        try:
            ticker = yf.Ticker(symbol)
            current_price = ticker.history(period='1d')['Close'].iloc[-1]
        except:
            current_price = pos['avg_cost']
        
        return {
            'symbol': symbol,
            'quantity': pos['quantity'],
            'avg_cost': pos['avg_cost'],
            'current_price': current_price,
            'unrealized_pnl': (current_price - pos['avg_cost']) * pos['quantity'],
            'unrealized_pct': ((current_price - pos['avg_cost']) / 
                              pos['avg_cost'] * 100),
            'entry_date': pos['entry_date']
        }
    
    def _save_portfolio(self):
        """Save portfolio state to file"""
        try:
            with open(self.portfolio_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Error saving portfolio: {e}")
    
    def _save_trades(self):
        """Save trade log to file"""
        try:
            with open(self.trade_log_file, 'w') as f:
                json.dump(self.trades, f, indent=2)
        except Exception as e:
            print(f"Error saving trades: {e}")
    
    def print_portfolio_status(self):
        """Print clear portfolio status"""
        summary = self.get_portfolio_summary()
        
        print("\n" + "="*60)
        print("PORTFOLIO STATUS")
        print("="*60)
        print(f"Starting Capital: ${summary['starting_capital']:.2f}")
        print(f"Available Cash: ${summary['available_capital']:.2f}")
        print(f"Realized P&L: ${summary['realized_pnl']:.2f} (actual closed trades)")
        print(f"Unrealized P&L: ${summary['unrealized_pnl']:.2f} (open positions)")
        print(f"Total Portfolio Value: ${summary['total_portfolio_value']:.2f}")
        print(f"Total Return: ${summary['total_return']:.2f} ({summary['total_return_pct']:.1f}%)")
        print(f"\nTrading Performance:")
        print(f"  Total Trades: {summary['total_trades']}")
        print(f"  Winning Trades: {summary['winning_trades']}")
        print(f"  Win Rate: {summary['win_rate']:.1f}%")
        print(f"\nOpen Positions: {summary['open_positions_count']}")
        
        if summary['open_positions']:
            print("\nOpen Positions:")
            for pos in summary['open_positions']:
                print(f"  {pos['symbol']}: {pos['quantity']} shares @ ${pos['avg_cost']:.2f}")
                print(f"    Current: ${pos['current_price']:.2f} | "
                      f"P&L: ${pos['unrealized_pnl']:.2f} ({pos['unrealized_pct']:.1f}%)")
        
        print("="*60)
