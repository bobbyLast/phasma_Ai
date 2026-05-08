"""
Backtesting Engine - Validate strategies with historical data
Tests entry/exit logic, position sizing, risk management across market conditions
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf

class BacktestEngine:
    """Comprehensive backtesting for trading strategies"""
    
    def __init__(self, initial_capital: float = 10000):
        """Initialize backtest engine"""
        self.initial_capital = initial_capital
        self.logger = logging.getLogger(__name__)
        
    def run_backtest(
        self,
        strategy,
        symbol: str,
        start_date: str,
        end_date: str,
        trade_params: Dict = None
    ) -> Dict:
        """
        Run complete backtest on historical data
        
        Args:
            strategy: Trading strategy object with generate_signals() method
            symbol: Stock/crypto ticker
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            trade_params: Strategy parameters
            
        Returns:
            Complete backtest results with metrics
        """
        try:
            self.logger.info(f"Running backtest: {symbol} from {start_date} to {end_date}")
            
            # Get historical data
            data = self._fetch_historical_data(symbol, start_date, end_date)
            
            if data.empty:
                return {'error': 'No historical data available'}
            
            # Initialize tracking
            capital = self.initial_capital
            positions = []
            trades = []
            equity_curve = [capital]
            
            # Simulate trading day by day
            for date in pd.date_range(start=start_date, end=end_date):
                if date not in data.index:
                    continue
                
                current_data = data.loc[:date]
                current_price = data.loc[date, 'Close']
                
                # Generate signals
                signals = strategy.generate_signals(current_data, trade_params)
                
                # Process signals
                for signal in signals:
                    if signal['action'] in ['BUY', 'BUY_CALL']:
                        # Enter position
                        trade = self._enter_position(
                            signal, date, current_price, capital
                        )
                        if trade:
                            positions.append(trade)
                            capital -= trade['cost']
                    
                    elif signal['action'] in ['SELL', 'EXIT']:
                        # Exit positions
                        for pos in positions[:]:
                            exit_result = self._exit_position(
                                pos, date, current_price
                            )
                            if exit_result:
                                trades.append(exit_result)
                                capital += exit_result['exit_value']
                                positions.remove(pos)
                
                # Update equity curve
                position_value = sum(
                    self._calculate_position_value(p, current_price)
                    for p in positions
                )
                total_equity = capital + position_value
                equity_curve.append(total_equity)
            
            # Calculate metrics
            metrics = self._calculate_metrics(trades, equity_curve)
            
            return {
                'symbol': symbol,
                'period': f'{start_date} to {end_date}',
                'initial_capital': self.initial_capital,
                'final_capital': equity_curve[-1],
                'trades': trades,
                'metrics': metrics,
                'equity_curve': equity_curve
            }
            
        except Exception as e:
            self.logger.error(f"Backtest error: {e}")
            return {'error': str(e)}
    
    def _fetch_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Fetch historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            return data
        except Exception as e:
            self.logger.error(f"Data fetch error: {e}")
            return pd.DataFrame()
    
    def _enter_position(
        self,
        signal: Dict,
        date,
        price: float,
        available_capital: float
    ) -> Optional[Dict]:
        """Enter a position based on signal"""
        try:
            position_size = signal.get('position_size', available_capital * 0.01)
            
            if position_size > available_capital:
                return None
            
            return {
                'symbol': signal['symbol'],
                'entry_date': date,
                'entry_price': price,
                'quantity': position_size / price,
                'cost': position_size,
                'trade_type': signal['action'],
                'stop_loss': signal.get('stop_loss'),
                'profit_target': signal.get('profit_target')
            }
        except Exception as e:
            return None
    
    def _exit_position(
        self,
        position: Dict,
        date,
        price: float
    ) -> Optional[Dict]:
        """Exit a position"""
        try:
            exit_value = position['quantity'] * price
            pnl = exit_value - position['cost']
            pnl_pct = pnl / position['cost']
            
            return {
                **position,
                'exit_date': date,
                'exit_price': price,
                'exit_value': exit_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'hold_days': (date - position['entry_date']).days
            }
        except Exception as e:
            return None
    
    def _calculate_position_value(
        self,
        position: Dict,
        current_price: float
    ) -> float:
        """Calculate current value of position"""
        return position['quantity'] * current_price
    
    def _calculate_metrics(
        self,
        trades: List[Dict],
        equity_curve: List[float]
    ) -> Dict:
        """Calculate backtest performance metrics"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_return': 0.0
            }
        
        # Basic metrics
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(trades)
        
        # P&L metrics
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        
        # Win/loss metrics
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t['pnl']) for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in winning_trades)
        gross_loss = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Drawdown
        max_dd = self._calculate_max_drawdown(equity_curve)
        
        # Sharpe ratio
        returns = np.diff(equity_curve) / equity_curve[:-1]
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_return': total_return,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_dd,
            'sharpe_ratio': sharpe,
            'avg_hold_days': np.mean([t['hold_days'] for t in trades])
        }
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown"""
        peak = equity_curve[0]
        max_dd = 0.0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (value - peak) / peak
            if dd < max_dd:
                max_dd = dd
        
        return max_dd
    
    def print_backtest_results(self, results: Dict):
        """Print formatted backtest results"""
        if 'error' in results:
            print(f"Error: {results['error']}")
            return
        
        metrics = results['metrics']
        
        print("\n" + "="*70)
        print("BACKTEST RESULTS")
        print("="*70)
        print(f"Symbol: {results['symbol']}")
        print(f"Period: {results['period']}")
        print(f"Initial Capital: ${results['initial_capital']:,.2f}")
        print(f"Final Capital: ${results['final_capital']:,.2f}")
        print(f"Total Return: {metrics['total_return']:.1%}")
        
        print("\nTRADE STATISTICS:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Winning Trades: {metrics['winning_trades']}")
        print(f"  Losing Trades: {metrics['losing_trades']}")
        print(f"  Win Rate: {metrics['win_rate']:.1%}")
        print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        
        print("\nPERFORMANCE METRICS:")
        print(f"  Total P&L: ${metrics['total_pnl']:,.2f}")
        print(f"  Avg Win: ${metrics['avg_win']:,.2f}")
        print(f"  Avg Loss: ${metrics['avg_loss']:,.2f}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.1%}")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Avg Hold: {metrics['avg_hold_days']:.1f} days")
        
        print("="*70 + "\n")
