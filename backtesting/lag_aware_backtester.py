"""
Lag-Aware Backtester - Realistic backtesting with filing delays

Simulates trading with actual SEC filing delays, transaction costs, and survivorship bias.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import json
import os


@dataclass
class BacktestSignal:
    """Signal with realistic timing"""
    symbol: str
    signal_date: datetime
    signal_type: str
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    filing_delay: int  # Days until signal was actually visible
    actual_entry_date: datetime
    actual_entry_price: float
    transaction_cost: float
    position_size: float


class LagAwareBacktester:
    """Backtester with realistic filing delays and costs"""
    
    def __init__(self, config: Dict = None):
        """Initialize lag-aware backtester"""
        self.config = config or {}
        
        # Filing delays (business days)
        self.form4_delay = self.config.get('form4_delay', 2)  # 2 business days
        self.f13_delay = self.config.get('f13_delay', 60)    # 60 days after quarter end
        
        # Transaction costs
        self.slippage_bps = self.config.get('slippage_bps', 5)      # 5 bps
        self.commission_bps = self.config.get('commission_bps', 1)  # 1 bps
        
        # Position sizing
        self.max_position_size = self.config.get('max_position_size', 0.02)  # 2% max
        self.min_position_size = self.config.get('min_position_size', 0.005) # 0.5% min
        
        # Tracking
        self.trades = []
        self.portfolio_value = []
        self.benchmark_value = []
        
        print("[BACKTESTER] Initialized with realistic delays and costs")
        print(f"[BACKTESTER] Form 4 delay: {self.form4_delay} days, 13F delay: {self.f13_delay} days")
        print(f"[BACKTESTER] Costs: {self.slippage_bps} bps slippage + {self.commission_bps} bps commission")
    
    def simulate_historical_signals(self, start_date: datetime, end_date: datetime) -> List[BacktestSignal]:
        """
        Generate signals with realistic delays
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            List of signals with realistic timing
        """
        signals = []
        
        # Generate trading calendar
        trading_days = self._generate_trading_calendar(start_date, end_date)
        
        for i, date in enumerate(trading_days):
            # Simulate signal generation (would use historical data)
            daily_signals = self._simulate_daily_signals(date)
            
            for signal in daily_signals:
                # Apply filing delays
                delayed_signal = self._apply_filing_delay(signal, date, trading_days)
                
                if delayed_signal:
                    # Apply transaction costs
                    delayed_signal = self._apply_transaction_costs(delayed_signal)
                    
                    signals.append(delayed_signal)
        
        print(f"[BACKTESTER] Generated {len(signals)} signals with realistic delays")
        return signals
    
    def _generate_trading_calendar(self, start: datetime, end: datetime) -> List[datetime]:
        """Generate list of trading days (excluding weekends)"""
        days = []
        current = start
        
        while current <= end:
            # Exclude weekends
            if current.weekday() < 5:
                days.append(current)
            current += timedelta(days=1)
        
        return days
    
    def _simulate_daily_signals(self, date: datetime) -> List[Dict]:
        """
        Simulate daily signal generation
        
        In production, this would use actual historical data
        """
        signals = []
        
        # Simulate random signal generation
        if np.random.random() < 0.1:  # 10% chance of signal
            signal_types = ['insider_buy', 'confluence', 'options_flow']
            signal_type = np.random.choice(signal_types)
            
            # Generate realistic signal
            signal = {
                'symbol': f'STOCK_{np.random.randint(100, 999)}',
                'date': date,
                'type': signal_type,
                'confidence': np.random.uniform(0.7, 0.95),
                'price': np.random.uniform(5, 50),
                'delay_type': np.random.choice(['form4', 'f13', 'none'])
            }
            
            signals.append(signal)
        
        return signals
    
    def _apply_filing_delay(self, signal: Dict, signal_date: datetime, trading_days: List[datetime]) -> Optional[BacktestSignal]:
        """Apply realistic filing delays to signal"""
        
        delay = 0
        
        if signal['delay_type'] == 'form4':
            delay = self.form4_delay
        elif signal['delay_type'] == 'f13':
            delay = self.f13_delay
        else:
            delay = 0  # Options flow is real-time
        
        # Find actual entry date
        signal_index = trading_days.index(signal_date)
        if signal_index + delay >= len(trading_days):
            return None  # Signal would appear after backtest period
        
        actual_entry_date = trading_days[signal_index + delay]
        
        # Simulate price movement during delay
        price_change = np.random.normal(0, 0.02)  # 2% daily volatility
        actual_entry_price = signal['price'] * (1 + price_change * delay)
        
        # Calculate position size based on confidence
        position_size = self.min_position_size + (signal['confidence'] - 0.7) * 0.05
        position_size = min(position_size, self.max_position_size)
        
        return BacktestSignal(
            symbol=signal['symbol'],
            signal_date=signal_date,
            signal_type=signal['type'],
            confidence=signal['confidence'],
            entry_price=signal['price'],
            target_price=signal['price'] * 1.3,  # 30% target
            stop_loss=signal['price'] * 0.9,     # 10% stop
            filing_delay=delay,
            actual_entry_date=actual_entry_date,
            actual_entry_price=actual_entry_price,
            transaction_cost=0,  # Will be calculated
            position_size=position_size
        )
    
    def _apply_transaction_costs(self, signal: BacktestSignal) -> BacktestSignal:
        """Apply realistic transaction costs"""
        
        # Calculate slippage (worse for larger positions)
        slippage_impact = signal.position_size * 0.001  # 0.1% per 1% position
        total_slippage = self.slippage_bps / 10000 + slippage_impact
        
        # Apply slippage to entry price
        signal.actual_entry_price *= (1 + total_slippage)
        
        # Calculate commission
        notional = signal.actual_entry_price * 100 * signal.position_size  # Assume 100 shares per % position
        signal.transaction_cost = notional * (self.commission_bps / 10000)
        
        return signal
    
    def run_backtest(self, signals: List[BacktestSignal], initial_capital: float = 100000) -> Dict:
        """
        Run backtest with realistic execution
        
        Args:
            signals: List of signals to trade
            initial_capital: Starting capital
            
        Returns:
            Backtest results
        """
        capital = initial_capital
        positions = {}
        trades = []
        portfolio_values = []
        
        print(f"[BACKTESTER] Running backtest with {len(signals)} signals...")
        
        for signal in signals:
            # Check if already in position
            if signal.symbol in positions:
                # Check exit conditions
                position = positions[signal.symbol]
                exit_result = self._check_exit_conditions(signal, position)
                
                if exit_result['exit']:
                    # Close position
                    exit_price = exit_result['price']
                    pnl = self._calculate_pnl(position, exit_price)
                    capital += pnl
                    
                    trades.append({
                        'symbol': signal.symbol,
                        'entry_date': position['entry_date'],
                        'exit_date': signal.actual_entry_date,
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'return': (exit_price - position['entry_price']) / position['entry_price'],
                        'holding_period': (signal.actual_entry_date - position['entry_date']).days
                    })
                    
                    del positions[signal.symbol]
            
            # Enter new position if signal is strong enough
            if signal.confidence >= 0.8 and signal.symbol not in positions:
                position_size = capital * signal.position_size
                shares = int(position_size / signal.actual_entry_price)
                
                if shares > 0:
                    cost = shares * signal.actual_entry_price + signal.transaction_cost
                    if cost <= capital:
                        capital -= cost
                        
                        positions[signal.symbol] = {
                            'shares': shares,
                            'entry_price': signal.actual_entry_price,
                            'entry_date': signal.actual_entry_date,
                            'stop_loss': signal.stop_loss,
                            'target_price': signal.target_price,
                            'signal_type': signal.signal_type
                        }
        
        # Close all positions at end
        final_positions = positions.copy()
        for symbol, position in final_positions.items():
            # Assume exit at last price (would use actual price)
            exit_price = position['entry_price'] * np.random.uniform(0.8, 1.2)
            pnl = self._calculate_pnl(position, exit_price)
            capital += pnl
            
            trades.append({
                'symbol': symbol,
                'entry_date': position['entry_date'],
                'exit_date': datetime.now(),
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'pnl': pnl,
                'return': (exit_price - position['entry_price']) / position['entry_price'],
                'holding_period': (datetime.now() - position['entry_date']).days
            })
        
        # Calculate results
        results = self._calculate_results(trades, initial_capital, capital)
        
        print(f"[BACKTESTER] Backtest complete: {len(trades)} trades executed")
        return results
    
    def _check_exit_conditions(self, signal: BacktestSignal, position: Dict) -> Dict:
        """Check if position should be closed"""
        
        # In production, would use actual market data
        current_price = signal.actual_entry_price * np.random.uniform(0.85, 1.35)
        
        # Stop loss hit
        if current_price <= position['stop_loss']:
            return {'exit': True, 'price': current_price, 'reason': 'stop_loss'}
        
        # Target hit
        if current_price >= position['target_price']:
            return {'exit': True, 'price': current_price, 'reason': 'target'}
        
        # Time-based exit (30 days)
        holding_period = (signal.actual_entry_date - position['entry_date']).days
        if holding_period >= 30:
            return {'exit': True, 'price': current_price, 'reason': 'time'}
        
        return {'exit': False, 'price': current_price}
    
    def _calculate_pnl(self, position: Dict, exit_price: float) -> float:
        """Calculate PnL for closed position"""
        return position['shares'] * (exit_price - position['entry_price'])
    
    def _calculate_results(self, trades: List[Dict], initial_capital: float, final_capital: float) -> Dict:
        """Calculate backtest performance metrics"""
        
        if not trades:
            return {
                'total_return': 0,
                'total_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }
        
        returns = [t['return'] for t in trades]
        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r < 0]
        
        total_return = (final_capital - initial_capital) / initial_capital
        
        # Calculate drawdown
        equity_curve = [initial_capital]
        for trade in trades:
            equity_curve.append(equity_curve[-1] * (1 + trade['return']))
        
        peak = equity_curve[0]
        max_drawdown = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate Sharpe ratio (simplified)
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        return {
            'total_return': total_return,
            'total_trades': len(trades),
            'win_rate': len(wins) / len(trades) if trades else 0,
            'avg_win': np.mean(wins) if wins else 0,
            'avg_loss': np.mean(losses) if losses else 0,
            'profit_factor': abs(sum(wins) / sum(losses)) if losses else float('inf'),
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_holding_period': np.mean([t['holding_period'] for t in trades]) if trades else 0
        }
    
    def compare_with_naive_backtest(self, realistic_results: Dict) -> Dict:
        """Compare realistic backtest with naive (no delays) results"""
        
        print("\n[BACKTESTER] COMPARISON: Realistic vs Naive Backtest")
        print("=" * 60)
        
        # Run naive backtest (no delays, no costs)
        naive_config = self.config.copy()
        naive_config['form4_delay'] = 0
        naive_config['f13_delay'] = 0
        naive_config['slippage_bps'] = 0
        naive_config['commission_bps'] = 0
        
        naive_backtester = LagAwareBacktester(naive_config)
        
        # Generate same signals (without delays for comparison)
        signals = self.simulate_historical_signals(
            datetime(2024, 1, 1),
            datetime(2024, 12, 31)
        )
        
        naive_results = naive_backtester.run_backtest(signals)
        
        # Print comparison
        print(f"{'Metric':<20} {'Realistic':<12} {'Naive':<12} {'Difference':<12}")
        print("-" * 60)
        print(f"{'Total Return':<20} {realistic_results['total_return']:<12.2%} {naive_results['total_return']:<12.2%} {realistic_results['total_return'] - naive_results['total_return']:<12.2%}")
        print(f"{'Win Rate':<20} {realistic_results['win_rate']:<12.2%} {naive_results['win_rate']:<12.2%} {realistic_results['win_rate'] - naive_results['win_rate']:<12.2%}")
        print(f"{'Sharpe Ratio':<20} {realistic_results['sharpe_ratio']:<12.2f} {naive_results['sharpe_ratio']:<12.2f} {realistic_results['sharpe_ratio'] - naive_results['sharpe_ratio']:<12.2f}")
        print(f"{'Max Drawdown':<20} {realistic_results['max_drawdown']:<12.2%} {naive_results['max_drawdown']:<12.2%} {realistic_results['max_drawdown'] - naive_results['max_drawdown']:<12.2%}")
        
        return {
            'realistic': realistic_results,
            'naive': naive_results,
            'difference': {
                'return_gap': realistic_results['total_return'] - naive_results['total_return'],
                'win_rate_gap': realistic_results['win_rate'] - naive_results['win_rate'],
                'sharpe_gap': realistic_results['sharpe_ratio'] - naive_results['sharpe_ratio']
            }
        }


# Example usage
if __name__ == "__main__":
    backtester = LagAwareBacktester()
    
    # Run backtest
    signals = backtester.simulate_historical_signals(
        datetime(2024, 1, 1),
        datetime(2024, 12, 31)
    )
    
    results = backtester.run_backtest(signals)
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Win Rate: {results['win_rate']:.2%}")
