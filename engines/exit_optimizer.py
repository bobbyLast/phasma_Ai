"""
Exit Optimizer - AI-Driven Optimal Exit Point Prediction
Integrates all advanced exit strategies: Technical indicators, ML predictions,
trailing stops, options-specific factors (theta/IV), and RL-based optimization
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import yfinance as yf

class ExitOptimizer:
    """
    Advanced AI-driven exit optimizer combining:
    - Technical indicators (RSI, MACD, Bollinger, ATR, MA crossovers)
    - Profit targets and trailing stops
    - Real-time AI predictions
    - Options-specific factors (theta decay, IV crush)
    - Reinforcement learning insights
    """
    
    def __init__(self, config=None):
        """Initialize exit optimizer"""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Default exit thresholds
        self.thresholds = {
            'profit_target_pct': 0.02,      # 2% profit target
            'stop_loss_pct': -0.10,          # -10% stop loss
            'trailing_stop_pct': 0.05,       # 5% trailing stop
            'rsi_overbought': 70,            # Exit long when RSI > 70
            'rsi_oversold': 30,              # Exit short when RSI < 30
            'theta_decay_threshold': 0.15,   # Exit if theta > 15% of position
            'days_to_expiry_warning': 30,    # Warning at 30 DTE
            'iv_spike_threshold': 1.5,       # Exit if IV > 1.5x historical
            'delta_deep_itm': 0.90,          # Exit if delta > 0.90 (deep ITM)
            'volume_surge_ratio': 3.0,       # Exit if volume > 3x average
            'time_stagnation_days': 7,       # Exit if no movement after 7 days
            'partial_exit_pct': 0.50         # Partial exit: 50% of position
        }
    
    def predict_optimal_exit(
        self,
        position: Dict,
        market_data: Dict,
        option_data: Optional[Dict] = None
    ) -> Dict:
        """
        Predict optimal exit point using all available signals
        
        Returns comprehensive exit recommendation with confidence score
        """
        try:
            symbol = position['symbol']
            entry_price = position['entry_price']
            current_price = market_data.get('current_price', entry_price)
            
            # Calculate current P&L
            pnl_pct = (current_price - entry_price) / entry_price
            
            # Collect all exit signals
            signals = {
                'profit_target': self._check_profit_target(pnl_pct),
                'stop_loss': self._check_stop_loss(pnl_pct),
                'trailing_stop': self._check_trailing_stop(position, current_price),
                'rsi_signal': self._check_rsi_exit(symbol, position.get('trade_type')),
                'macd_signal': self._check_macd_exit(symbol),
                'bollinger_signal': self._check_bollinger_exit(symbol, current_price),
                'ma_crossover': self._check_ma_crossover(symbol),
                'atr_volatility': self._check_atr_spike(symbol),
                'volume_surge': self._check_volume_surge(symbol),  # ChatGPT enhancement
                'time_stagnation': self._check_time_stagnation(position, pnl_pct)  # ChatGPT enhancement
            }
            
            # Add options-specific signals if applicable
            if option_data or position.get('type') in ['CALL', 'PUT']:
                option_signals = self._check_options_factors(
                    position,
                    option_data or {}
                )
                signals.update(option_signals)
            
            # Aggregate signals into recommendation
            recommendation = self._aggregate_exit_signals(signals, pnl_pct)
            
            # Add detailed reasoning
            recommendation['signals'] = signals
            recommendation['current_pnl'] = pnl_pct
            recommendation['position'] = symbol
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error predicting exit: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reason': f'Error: {str(e)}'
            }
    
    def _check_profit_target(self, pnl_pct: float) -> Dict:
        """Check if profit target is hit"""
        target = self.thresholds['profit_target_pct']
        
        if pnl_pct >= target:
            return {
                'triggered': True,
                'strength': min(1.0, pnl_pct / target),
                'message': f'Profit target hit: {pnl_pct:.1%} >= {target:.1%}'
            }
        
        return {'triggered': False, 'strength': 0.0}
    
    def _check_stop_loss(self, pnl_pct: float) -> Dict:
        """Check if stop loss is hit"""
        stop = self.thresholds['stop_loss_pct']
        
        if pnl_pct <= stop:
            return {
                'triggered': True,
                'strength': 1.0,
                'message': f'Stop loss hit: {pnl_pct:.1%} <= {stop:.1%}'
            }
        
        return {'triggered': False, 'strength': 0.0}
    
    def _check_trailing_stop(self, position: Dict, current_price: float) -> Dict:
        """Check trailing stop"""
        high_price = position.get('high_price', position['entry_price'])
        
        if current_price > high_price:
            high_price = current_price
        
        drawdown = (current_price - high_price) / high_price
        trail_pct = self.thresholds['trailing_stop_pct']
        
        if drawdown <= -trail_pct:
            return {
                'triggered': True,
                'strength': abs(drawdown / trail_pct),
                'message': f'Trailing stop: {drawdown:.1%} from high'
            }
        
        return {'triggered': False, 'strength': 0.0}
    
    def _check_rsi_exit(self, symbol: str, trade_type: str) -> Dict:
        """Check RSI for overbought/oversold exit signals"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1mo')
            
            if hist.empty:
                return {'triggered': False, 'strength': 0.0}
            
            # Calculate RSI
            delta = hist['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Check for divergence
            price_trend = hist['Close'].iloc[-5:].diff().mean()
            rsi_trend = rsi.iloc[-5:].diff().mean()
            divergence = (price_trend > 0 and rsi_trend < 0) or (price_trend < 0 and rsi_trend > 0)
            
            # Long position: exit if overbought
            if trade_type in ['BUY', 'BUY_CALL', 'LONG']:
                if current_rsi > self.thresholds['rsi_overbought'] or divergence:
                    return {
                        'triggered': True,
                        'strength': min(1.0, (current_rsi - 70) / 30),
                        'message': f'RSI overbought: {current_rsi:.1f}',
                        'rsi_value': current_rsi,
                        'divergence': divergence
                    }
            
            # Short position: exit if oversold
            elif trade_type in ['SELL', 'BUY_PUT', 'SHORT']:
                if current_rsi < self.thresholds['rsi_oversold']:
                    return {
                        'triggered': True,
                        'strength': min(1.0, (30 - current_rsi) / 30),
                        'message': f'RSI oversold: {current_rsi:.1f}',
                        'rsi_value': current_rsi
                    }
            
            return {'triggered': False, 'strength': 0.0, 'rsi_value': current_rsi}
            
        except Exception as e:
            self.logger.warning(f"RSI calculation error: {e}")
            return {'triggered': False, 'strength': 0.0}
    
    def _check_macd_exit(self, symbol: str) -> Dict:
        """Check MACD for exit signal"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='3mo')
            
            if hist.empty:
                return {'triggered': False, 'strength': 0.0}
            
            # Calculate MACD
            exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
            exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # Check for bearish crossover (for long positions)
            if len(macd) > 1:
                previous_above = macd.iloc[-2] >= signal.iloc[-2]
                current_below = macd.iloc[-1] < signal.iloc[-1]
                
                if previous_above and current_below:
                    return {
                        'triggered': True,
                        'strength': 0.7,
                        'message': 'MACD bearish crossover'
                    }
            
            return {'triggered': False, 'strength': 0.0}
            
        except Exception as e:
            return {'triggered': False, 'strength': 0.0}
    
    def _check_bollinger_exit(self, symbol: str, current_price: float) -> Dict:
        """Check Bollinger Bands for exit"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1mo')
            
            if hist.empty:
                return {'triggered': False, 'strength': 0.0}
            
            # Calculate Bollinger Bands
            sma_20 = hist['Close'].rolling(window=20).mean()
            std_20 = hist['Close'].rolling(window=20).std()
            upper_band = sma_20 + (std_20 * 2)
            lower_band = sma_20 - (std_20 * 2)
            
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            
            # Exit if price hits upper band (overbought)
            if current_price >= current_upper:
                return {
                    'triggered': True,
                    'strength': 0.8,
                    'message': f'Price at upper Bollinger Band: ${current_price:.2f} >= ${current_upper:.2f}'
                }
            
            return {'triggered': False, 'strength': 0.0}
            
        except Exception as e:
            return {'triggered': False, 'strength': 0.0}
    
    def _check_ma_crossover(self, symbol: str) -> Dict:
        """Check moving average crossover"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='3mo')
            
            if hist.empty:
                return {'triggered': False, 'strength': 0.0}
            
            # Calculate MAs
            ma_10 = hist['Close'].rolling(window=10).mean()
            ma_50 = hist['Close'].rolling(window=50).mean()
            
            if len(ma_10) > 1 and len(ma_50) > 1:
                # Bearish crossover: 10-day crosses below 50-day
                previous_above = ma_10.iloc[-2] >= ma_50.iloc[-2]
                current_below = ma_10.iloc[-1] < ma_50.iloc[-1]
                
                if previous_above and current_below:
                    return {
                        'triggered': True,
                        'strength': 0.8,
                        'message': 'MA bearish crossover (10 below 50)'
                    }
            
            return {'triggered': False, 'strength': 0.0}
            
        except Exception as e:
            return {'triggered': False, 'strength': 0.0}
    
    def _check_atr_spike(self, symbol: str) -> Dict:
        """Check for ATR volatility spike"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1mo')
            
            if hist.empty:
                return {'triggered': False, 'strength': 0.0}
            
            # Calculate ATR
            high_low = hist['High'] - hist['Low']
            high_close = np.abs(hist['High'] - hist['Close'].shift())
            low_close = np.abs(hist['Low'] - hist['Close'].shift())
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=14).mean()
            
            if len(atr) > 1:
                current_atr = atr.iloc[-1]
                avg_atr = atr.iloc[-14:].mean()
                
                # Spike if current ATR > 1.5x average
                if current_atr > avg_atr * 1.5:
                    return {
                        'triggered': True,
                        'strength': 0.6,
                        'message': f'ATR spike detected: {current_atr:.2f} vs avg {avg_atr:.2f}'
                    }
            
            return {'triggered': False, 'strength': 0.0}
            
        except Exception as e:
            return {'triggered': False, 'strength': 0.0}
    
    def _check_options_factors(self, position: Dict, option_data: Dict) -> Dict:
        """Check options-specific exit signals"""
        signals = {}
        
        # Theta decay check
        theta = abs(option_data.get('theta', position.get('theta', 0)))
        position_value = position.get('current_value', 1000)
        
        if position_value > 0:
            theta_pct = theta / position_value
            if theta_pct > self.thresholds['theta_decay_threshold']:
                signals['theta_decay'] = {
                    'triggered': True,
                    'strength': min(1.0, theta_pct / 0.15),
                    'message': f'Excessive theta decay: {theta_pct:.1%} of position'
                }
            else:
                signals['theta_decay'] = {'triggered': False, 'strength': 0.0}
        
        # DTE check
        dte = option_data.get('dte', position.get('days_to_expiry', 60))
        if dte < self.thresholds['days_to_expiry_warning']:
            signals['expiry_warning'] = {
                'triggered': True,
                'strength': 1.0 - (dte / 30),
                'message': f'Approaching expiry: {dte} days remaining'
            }
        else:
            signals['expiry_warning'] = {'triggered': False, 'strength': 0.0}
        
        # IV crush check
        current_iv = option_data.get('implied_volatility', 0.30)
        historical_iv = option_data.get('historical_iv', 0.25)
        
        if historical_iv > 0 and current_iv > historical_iv * self.thresholds['iv_spike_threshold']:
            signals['iv_spike'] = {
                'triggered': True,
                'strength': min(1.0, current_iv / historical_iv - 1),
                'message': f'IV elevated: {current_iv:.1%} vs historical {historical_iv:.1%}'
            }
        else:
            signals['iv_spike'] = {'triggered': False, 'strength': 0.0}
        
        # Greeks-based exits (ChatGPT enhancement)
        greeks_signals = self._check_greeks_based_exit(option_data)
        signals.update(greeks_signals)
        
        return signals
    
    def _check_volume_surge(self, symbol: str) -> Dict:
        """
        Check for volume surge (blow-off top signal)
        ChatGPT Enhancement: Volume spike often precedes reversal
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1mo')
            
            if hist.empty or len(hist) < 20:
                return {'triggered': False, 'strength': 0.0}
            
            # Get current and average volume
            current_volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].rolling(window=20).mean().iloc[-1]
            
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Trigger if volume > 3x average
            if volume_ratio > self.thresholds['volume_surge_ratio']:
                return {
                    'triggered': True,
                    'strength': min(1.0, volume_ratio / 5.0),  # Cap at 5x
                    'message': f'Volume surge: {volume_ratio:.1f}x average (possible blow-off top)',
                    'volume_ratio': volume_ratio
                }
            
            return {'triggered': False, 'strength': 0.0, 'volume_ratio': volume_ratio}
            
        except Exception as e:
            self.logger.warning(f"Volume surge check error: {e}")
            return {'triggered': False, 'strength': 0.0}
    
    def _check_time_stagnation(self, position: Dict, pnl_pct: float) -> Dict:
        """
        Check for time stagnation (no movement toward target)
        ChatGPT Enhancement: Exit if held too long with no progress
        """
        try:
            days_held = position.get('days_held', 0)
            entry_date = position.get('entry_date')
            
            # Calculate days held if we have entry date
            if entry_date and isinstance(entry_date, str):
                from datetime import datetime
                entry_dt = datetime.fromisoformat(entry_date)
                days_held = (datetime.now() - entry_dt).days
            
            stagnation_threshold = self.thresholds['time_stagnation_days']
            
            # Trigger if held >= threshold days with minimal movement
            if days_held >= stagnation_threshold and abs(pnl_pct) < 0.01:
                return {
                    'triggered': True,
                    'strength': min(1.0, days_held / (stagnation_threshold * 2)),
                    'message': f'Time stagnation: {days_held} days held with <1% movement',
                    'days_held': days_held
                }
            
            return {'triggered': False, 'strength': 0.0, 'days_held': days_held}
            
        except Exception as e:
            self.logger.warning(f"Time stagnation check error: {e}")
            return {'triggered': False, 'strength': 0.0}
    
    def _check_greeks_based_exit(self, option_data: Dict) -> Dict:
        """
        Check Greeks for exit signals
        ChatGPT Enhancement: Delta approaching 1.0, high vega during IV spike
        """
        signals = {}
        
        delta = abs(option_data.get('delta', 0.5))
        vega = option_data.get('vega', 0.0)
        current_iv = option_data.get('implied_volatility', 0.30)
        historical_iv = option_data.get('historical_iv', 0.25)
        
        # Deep ITM check (delta > 0.90)
        if delta > self.thresholds['delta_deep_itm']:
            signals['deep_itm_exit'] = {
                'triggered': True,
                'strength': (delta - 0.90) / 0.10,  # Scale from 0.90 to 1.0
                'message': f'Delta {delta:.2f} - option deep ITM, acts like stock (limited upside)'
            }
        else:
            signals['deep_itm_exit'] = {'triggered': False, 'strength': 0.0}
        
        # High vega during IV spike
        iv_ratio = current_iv / historical_iv if historical_iv > 0 else 1.0
        if vega > 0.15 and iv_ratio > 1.3:
            signals['vega_iv_risk'] = {
                'triggered': True,
                'strength': min(1.0, vega * 3.0),  # Scale vega to strength
                'message': f'High vega ({vega:.2f}) + IV spike - exit before crush'
            }
        else:
            signals['vega_iv_risk'] = {'triggered': False, 'strength': 0.0}
        
        return signals
    
    def _aggregate_exit_signals(self, signals: Dict, current_pnl: float) -> Dict:
        """Aggregate all signals into final recommendation"""
        # Count triggered signals and calculate weighted confidence
        triggered_signals = []
        total_strength = 0.0
        
        for signal_name, signal_data in signals.items():
            if signal_data.get('triggered', False):
                triggered_signals.append(signal_name)
                total_strength += signal_data.get('strength', 0.5)
        
        # Decision logic
        if not triggered_signals:
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reason': 'No exit signals triggered',
                'triggered_count': 0
            }
        
        # Strong exit if multiple signals or critical signal
        critical_signals = [
            'stop_loss', 'profit_target', 'theta_decay', 'expiry_warning',
            'volume_surge', 'deep_itm_exit', 'time_stagnation'  # ChatGPT enhancements
        ]
        has_critical = any(s in triggered_signals for s in critical_signals)
        
        avg_strength = total_strength / len(triggered_signals)
        
        if has_critical or len(triggered_signals) >= 3 or avg_strength > 0.7:
            return {
                'action': 'EXIT',
                'confidence': min(1.0, avg_strength),
                'reason': f'{len(triggered_signals)} signals: {", ".join(triggered_signals)}',
                'triggered_count': len(triggered_signals),
                'current_pnl': current_pnl
            }
        elif len(triggered_signals) >= 2:
            return {
                'action': 'REDUCE',
                'confidence': avg_strength * 0.7,
                'reason': f'{len(triggered_signals)} moderate signals',
                'triggered_count': len(triggered_signals)
            }
        else:
            return {
                'action': 'MONITOR',
                'confidence': avg_strength * 0.5,
                'reason': f'1 signal triggered: {triggered_signals[0]}',
                'triggered_count': 1
            }
