"""
Micro Execution Engine - Mind 3 of the Three-Mind Trading Framework

Turns ideas into precisely timed trades with controlled risk.
Implements technical pattern recognition and execution rules.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import talib


@dataclass
class MicroSignal:
    """Micro-level trading signal"""
    symbol: str
    pattern_type: str  # RSI_DIVERGENCE, SUPPORT_BOUNCE, BREAKOUT, etc.
    entry_price: float
    stop_loss: float
    target_price: float
    risk_reward: float
    confidence: float  # 0-1
    technical_score: float  # 0-1
    execution_rules: Dict
    thesis: str


@dataclass
class TradePlan:
    """Complete trade execution plan"""
    symbol: str
    action: str  # BUY, SELL, SELL_SHORT, BUY_COVER
    entry_type: str  # MARKET, LIMIT, STOP
    entry_price: float
    stop_loss: float
    target_price: float
    position_size: float  # As percentage of capital
    max_holding_period: int  # Days
    trailing_stop: bool
    partial_exit_rules: List[Dict]
    confluence_score: float  # 0-100, combines all three minds


class MicroExecutionEngine:
    """Mind 3: Technical analysis and execution planning"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Technical parameters
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.atr_period = 14
        self.ma_short = 20
        self.ma_long = 200
        self.min_risk_reward = 2.0
        
        # Pattern recognition thresholds
        self.divergence_lookback = 20
        self.support_resistance_lookback = 50
        self.volume_multiplier = 1.5
        
    def analyze_micro_setup(self, symbol: str, price_data: Dict, 
                          macro_alignment: float = 0, value_bias: float = 0) -> Optional[MicroSignal]:
        """Complete micro-level analysis for a single setup"""
        
        try:
            closes = np.array(price_data.get('closes', []))
            highs = np.array(price_data.get('highs', []))
            lows = np.array(price_data.get('lows', []))
            volumes = np.array(price_data.get('volumes', []))
            
            if len(closes) < 50:
                return None
            
            # Detect patterns
            patterns = []
            
            # RSI Divergence
            rsi_div = self._detect_rsi_divergence(closes, lows)
            if rsi_div:
                patterns.append(('RSI_DIVERGENCE', rsi_div))
            
            # Support/Resistance Bounce
            sr_bounce = self._detect_support_resistance_bounce(closes, lows, highs)
            if sr_bounce:
                patterns.append(('SUPPORT_BOUNCE', sr_bounce))
            
            # Breakout
            breakout = self._detect_breakout(closes, volumes)
            if breakout:
                patterns.append(('BREAKOUT', breakout))
            
            # Mean Reversion
            mean_rev = self._detect_mean_reversion(closes)
            if mean_rev:
                patterns.append(('MEAN_REVERSION', mean_rev))
            
            # Select best pattern
            if not patterns:
                return None
            
            best_pattern = max(patterns, key=lambda x: x[1]['score'])
            pattern_type, pattern_data = best_pattern
            
            # Calculate execution levels
            current_price = closes[-1]
            atr = self._calculate_atr(highs, lows, closes)
            
            entry_price = pattern_data.get('entry_price', current_price)
            stop_loss = pattern_data.get('stop_loss', current_price - atr * 2)
            target_price = pattern_data.get('target_price', current_price + atr * 3)
            
            # Calculate risk/reward
            risk = abs(entry_price - stop_loss)
            reward = abs(target_price - entry_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            # Skip if risk/reward insufficient
            if risk_reward < self.min_risk_reward:
                return None
            
            # Calculate technical score
            technical_score = pattern_data['score']
            
            # Adjust confidence based on macro and value alignment
            base_confidence = technical_score * 0.6
            macro_boost = macro_alignment * 0.2
            value_boost = value_bias * 0.2
            confidence = np.clip(base_confidence + macro_boost + value_boost, 0, 1)
            
            # Generate execution rules
            execution_rules = self._generate_execution_rules(
                pattern_type, entry_price, stop_loss, target_price, atr
            )
            
            # Generate thesis
            thesis = self._generate_micro_thesis(
                symbol, pattern_type, pattern_data, risk_reward
            )
            
            return MicroSignal(
                symbol=symbol,
                pattern_type=pattern_type,
                entry_price=entry_price,
                stop_loss=stop_loss,
                target_price=target_price,
                risk_reward=risk_reward,
                confidence=confidence,
                technical_score=technical_score,
                execution_rules=execution_rules,
                thesis=thesis
            )
            
        except Exception as e:
            print(f"Error in micro analysis for {symbol}: {e}")
            return None
    
    def _detect_rsi_divergence(self, closes: np.array, lows: np.array) -> Optional[Dict]:
        """Detect RSI divergence patterns"""
        
        try:
            rsi = talib.RSI(closes, timeperiod=self.rsi_period)
            
            if len(rsi) < self.divergence_lookback:
                return None
            
            # Look for bullish divergence (lower lows in price, higher lows in RSI)
            price_lows = []
            rsi_lows = []
            
            for i in range(len(lows) - self.divergence_lookback, len(lows)):
                if i > 0 and lows[i] < lows[i-1]:
                    price_lows.append((i, lows[i]))
                    rsi_lows.append((i, rsi[i]))
            
            # Check for divergence
            if len(price_lows) >= 2 and len(rsi_lows) >= 2:
                # Price making lower lows
                price_descending = price_lows[-1][1] < price_lows[-2][1]
                # RSI making higher lows
                rsi_ascending = rsi_lows[-1][1] > rsi_lows[-2][1]
                
                if price_descending and rsi_ascending and rsi_lows[-1][1] < self.rsi_oversold:
                    return {
                        'score': 0.8,
                        'entry_price': closes[-1],
                        'stop_loss': lows[-1] * 0.98,
                        'target_price': closes[-1] + (closes[-1] - lows[-1]) * 3,
                        'rsi_value': rsi_lows[-1][1]
                    }
            
            return None
            
        except Exception as e:
            print(f"Error detecting RSI divergence: {e}")
            return None
    
    def _detect_support_resistance_bounce(self, closes: np.array, 
                                        lows: np.array, highs: np.array) -> Optional[Dict]:
        """Detect support/resistance bounce patterns"""
        
        try:
            # Find recent support level
            recent_low = np.min(lows[-20:])
            support_level = np.percentile(lows[-self.support_resistance_lookback:], 10)
            
            # Check if price is near support
            current_price = closes[-1]
            near_support = abs(current_price - support_level) / support_level < 0.02
            
            if near_support and current_price > support_level:
                # Check for bounce confirmation (recent price action)
                recent_closes = closes[-5:]
                bouncing = recent_closes[-1] > recent_closes[0]
                
                if bouncing:
                    return {
                        'score': 0.7,
                        'entry_price': current_price,
                        'stop_loss': support_level * 0.98,
                        'target_price': support_level + (current_price - support_level) * 3,
                        'support_level': support_level
                    }
            
            return None
            
        except Exception as e:
            print(f"Error detecting S/R bounce: {e}")
            return None
    
    def _detect_breakout(self, closes: np.array, volumes: np.array) -> Optional[Dict]:
        """Detect breakout patterns"""
        
        try:
            # Calculate moving averages
            ma_short = talib.SMA(closes, timeperiod=self.ma_short)
            ma_long = talib.SMA(closes, timeperiod=self.ma_long)
            
            if len(ma_short) < 2 or len(ma_long) < 2:
                return None
            
            # Check for bullish breakout
            current_price = closes[-1]
            above_ma_short = current_price > ma_short[-1]
            above_ma_long = current_price > ma_long[-1]
            ma_cross_up = ma_short[-1] > ma_long[-1] and ma_short[-2] <= ma_long[-2]
            
            # Volume confirmation
            avg_volume = np.mean(volumes[-20:])
            volume_spike = volumes[-1] > avg_volume * self.volume_multiplier
            
            if (above_ma_short and above_ma_long and ma_cross_up) or volume_spike:
                # Calculate resistance level
                resistance = np.max(closes[-20:])
                
                return {
                    'score': 0.75,
                    'entry_price': current_price,
                    'stop_loss': ma_short[-1] * 0.98,
                    'target_price': resistance + (resistance - ma_long[-1]),
                    'resistance': resistance
                }
            
            return None
            
        except Exception as e:
            print(f"Error detecting breakout: {e}")
            return None
    
    def _detect_mean_reversion(self, closes: np.array) -> Optional[Dict]:
        """Detect mean reversion opportunities"""
        
        try:
            # Calculate Bollinger Bands
            upper, middle, lower = talib.BBANDS(closes, timeperiod=20)
            
            if len(lower) < 2:
                return None
            
            current_price = closes[-1]
            lower_band = lower[-1]
            
            # Check if price is at or below lower Bollinger Band
            at_support = current_price <= lower_band * 1.02
            
            if at_support:
                # Calculate mean reversion target (middle band)
                target = middle[-1]
                
                return {
                    'score': 0.65,
                    'entry_price': current_price,
                    'stop_loss': lower_band * 0.95,
                    'target_price': target,
                    'lower_band': lower_band
                }
            
            return None
            
        except Exception as e:
            print(f"Error detecting mean reversion: {e}")
            return None
    
    def _calculate_atr(self, highs: np.array, lows: np.array, closes: np.array) -> float:
        """Calculate Average True Range"""
        
        try:
            atr = talib.ATR(highs, lows, closes, timeperiod=self.atr_period)
            return atr[-1] if len(atr) > 0 else closes[-1] * 0.02
        except:
            return closes[-1] * 0.02
    
    def _generate_execution_rules(self, pattern_type: str, entry: float, 
                                stop: float, target: float, atr: float) -> Dict:
        """Generate specific execution rules for the pattern"""
        
        rules = {
            'entry_type': 'LIMIT',
            'entry_price': entry,
            'stop_type': 'STOP',
            'stop_price': stop,
            'target_type': 'LIMIT',
            'target_price': target,
            'time_stop': 10,  # Days
            'trailing_stop': False
        }
        
        # Pattern-specific adjustments
        if pattern_type == 'BREAKOUT':
            rules['entry_type'] = 'STOP'
            rules['entry_price'] = entry + atr * 0.1
            rules['trailing_stop'] = True
            rules['trail_distance'] = atr * 2
        
        elif pattern_type == 'RSI_DIVERGENCE':
            rules['entry_type'] = 'MARKET'
            rules['time_stop'] = 7
        
        elif pattern_type == 'MEAN_REVERSION':
            rules['partial_exit'] = {
                'level': target * 0.5,
                'exit_percent': 50
            }
        
        return rules
    
    def _generate_micro_thesis(self, symbol: str, pattern_type: str, 
                             pattern_data: Dict, risk_reward: float) -> str:
        """Generate micro-level trading thesis"""
        
        if pattern_type == 'RSI_DIVERGENCE':
            thesis = f"{symbol} showing bullish RSI divergence with {risk_reward:.1f}:1 risk/reward"
        elif pattern_type == 'SUPPORT_BOUNCE':
            thesis = f"{symbol} bouncing from key support at ${pattern_data.get('support_level', 0):.2f}"
        elif pattern_type == 'BREAKOUT':
            thesis = f"{symbol} breaking above resistance with volume confirmation"
        elif pattern_type == 'MEAN_REVERSION':
            thesis = f"{symbol} oversold at lower Bollinger Band, mean reversion expected"
        else:
            thesis = f"{symbol} technical setup with {risk_reward:.1f}:1 risk/reward"
        
        return thesis
    
    def create_trade_plan(self, micro_signal: MicroSignal, 
                         macro_context: Dict, value_assessment: Dict) -> TradePlan:
        """Create complete trade execution plan"""
        
        # Determine position size based on confidence and regime
        base_size = 0.02  # 2% base risk
        confidence_multiplier = micro_signal.confidence
        regime_multiplier = macro_context.get('position_size_multiplier', 1.0)
        
        position_size = base_size * confidence_multiplier * regime_multiplier
        
        # Determine action
        action = "BUY" if micro_signal.entry_price > micro_signal.stop_loss else "SELL"
        
        # Create partial exit rules
        partial_exits = []
        if micro_signal.risk_reward > 3.0:
            partial_exits.append({
                'level': micro_signal.entry_price + (micro_signal.target_price - micro_signal.entry_price) * 0.5,
                'exit_percent': 30
            })
        
        # Calculate confluence score
        macro_score = macro_context.get('confidence', 0) * 100
        value_score = value_assessment.get('conviction', 0) * 100
        technical_score = micro_signal.technical_score * 100
        
        confluence_score = (macro_score * 0.3 + value_score * 0.3 + technical_score * 0.4)
        
        return TradePlan(
            symbol=micro_signal.symbol,
            action=action,
            entry_type=micro_signal.execution_rules['entry_type'],
            entry_price=micro_signal.entry_price,
            stop_loss=micro_signal.stop_loss,
            target_price=micro_signal.target_price,
            position_size=position_size,
            max_holding_period=micro_signal.execution_rules.get('time_stop', 10),
            trailing_stop=micro_signal.execution_rules.get('trailing_stop', False),
            partial_exit_rules=partial_exits,
            confluence_score=confluence_score
        )
