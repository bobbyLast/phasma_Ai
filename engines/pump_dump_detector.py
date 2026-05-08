"""
Pump/Dump Detector - Identifies and manages penny stock pump patterns

Detects pump patterns to avoid getting dumped on:
- Volume surge detection (>3x average)
- Price acceleration patterns
- Insider activity correlation
- Automatic tiered profit-taking

Features:
- Real-time pump detection
- Tiered exit strategy (25% at +20%, 50% at +50%)
- Integration with insider trading signals
- Prevents holding through dumps
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
import json
import os


class PumpPattern:
    """Represents a detected pump pattern"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.volume_surge = 0.0
        self.price_acceleration = 0.0
        self.insider_activity = False
        self.pump_strength = 0.0
        self.detected_at = datetime.now()
        self.exit_levels = []
        self.position_taken = False


class PumpDumpDetector:
    """
    Detects pump patterns and manages exits to avoid dumps
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Detection thresholds
        self.volume_surge_threshold = float(self.config.get('pump_dump', {}).get('volume_surge_threshold', 3.0))
        self.price_acceleration_threshold = float(self.config.get('pump_dump', {}).get('price_acceleration_threshold', 0.5))
        self.min_price = float(self.config.get('pump_dump', {}).get('min_price', 0.1))
        self.max_price = float(self.config.get('pump_dump', {}).get('max_price', 10.0))
        
        # Exit strategy
        self.first_exit_pct = float(self.config.get('pump_dump', {}).get('first_exit_pct', 0.20))  # 20%
        self.second_exit_pct = float(self.config.get('pump_dump', {}).get('second_exit_pct', 0.50))  # 50%
        self.first_exit_size = float(self.config.get('pump_dump', {}).get('first_exit_size', 0.25))  # 25%
        self.second_exit_size = float(self.config.get('pump_dump', {}).get('second_exit_size', 0.50))  # 50%
        
        # Tracking
        self.active_pumps = {}
        self.position_exits = {}
        
    def analyze_stock(self, ticker: str, entry_price: float, position_size: int) -> Dict:
        """Analyze a stock for pump patterns and set exit strategy"""
        
        # Must be penny stock
        if not (self.min_price <= entry_price <= self.max_price):
            return {'pump_detected': False, 'reason': 'Price outside penny stock range'}
        
        try:
            # Get data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            if hist.empty or len(hist) < 3:
                return {'pump_detected': False, 'reason': 'Insufficient data'}
            
            # Calculate metrics
            current_price = hist['Close'].iloc[-1]
            avg_volume = hist['Volume'].mean()
            recent_volume = hist['Volume'].iloc[-1]
            
            # Volume surge
            volume_surge = recent_volume / avg_volume if avg_volume > 0 else 0
            
            # Price acceleration (3-day change)
            price_3d = hist['Close'].pct_change(3).iloc[-1]
            
            # Recent price action
            price_1d = hist['Close'].pct_change(1).iloc[-1]
            price_2d = hist['Close'].pct_change(2).iloc[-1]
            
            # Detect pump pattern
            pump_detected = False
            pump_strength = 0.0
            exit_strategy = None
            
            # Strong volume surge + price acceleration
            if volume_surge >= self.volume_surge_threshold and price_3d >= self.price_acceleration_threshold:
                pump_detected = True
                pump_strength = min((volume_surge / 10) + (price_3d * 2), 1.0)
                
                # Create exit strategy
                exit_strategy = self._create_exit_strategy(entry_price, pump_strength)
                
                # Track the pump
                pump = PumpPattern(ticker)
                pump.volume_surge = volume_surge
                pump.price_acceleration = price_3d
                pump.pump_strength = pump_strength
                pump.exit_levels = exit_strategy['exit_levels']
                self.active_pumps[ticker] = pump
                
                print(f"[PUMP DETECTED] {ticker}: Volume {volume_surge:.1f}x, Price +{price_3d:.1%}")
                print(f"   Strength: {pump_strength:.1%} | Exit levels set")
            
            return {
                'pump_detected': pump_detected,
                'pump_strength': pump_strength,
                'volume_surge': volume_surge,
                'price_acceleration': price_3d,
                'exit_strategy': exit_strategy,
                'current_price': current_price
            }
            
        except Exception as e:
            return {'pump_detected': False, 'reason': f'Error: {str(e)}'}
    
    def _create_exit_strategy(self, entry_price: float, pump_strength: float) -> Dict:
        """Create tiered exit strategy based on pump strength"""
        
        # Calculate exit prices
        first_exit_price = entry_price * (1 + self.first_exit_pct)
        second_exit_price = entry_price * (1 + self.second_exit_pct)
        
        # Adjust based on pump strength
        if pump_strength > 0.8:  # Very strong pump
            first_exit_price = entry_price * 1.15  # Take first profit earlier
            second_exit_price = entry_price * 1.40  # Second exit earlier
        elif pump_strength < 0.5:  # Weak pump
            first_exit_price = entry_price * 1.25  # Wait longer
            second_exit_price = entry_price * 1.60  # Higher target
        
        exit_levels = [
            {
                'level': 1,
                'price': first_exit_price,
                'sell_percent': self.first_exit_size,
                'description': f"Take {self.first_exit_size*100:.0f}% profit at +{(first_exit_price/entry_price - 1)*100:.0f}%"
            },
            {
                'level': 2,
                'price': second_exit_price,
                'sell_percent': self.second_exit_size,
                'description': f"Take {self.second_exit_size*100:.0f}% profit at +{(second_exit_price/entry_price - 1)*100:.0f}%"
            }
        ]
        
        return {
            'exit_levels': exit_levels,
            'strategy': 'Tiered profit-taking to avoid dump',
            'remaining_percent': 1 - (self.first_exit_size + self.second_exit_size)
        }
    
    def check_exit_signal(self, ticker: str, current_price: float, entry_price: float) -> Optional[Dict]:
        """Check if should exit based on pump pattern"""
        
        if ticker not in self.active_pumps:
            return None
        
        pump = self.active_pumps[ticker]
        
        # Check each exit level
        for exit_level in pump.exit_levels:
            if current_price >= exit_level['price']:
                return {
                    'exit_signal': True,
                    'exit_level': exit_level['level'],
                    'sell_percent': exit_level['sell_percent'],
                    'exit_price': exit_level['price'],
                    'reason': exit_level['description'],
                    'pump_strength': pump.pump_strength
                }
        
        # Check for dump warning (volume spike with price drop)
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            
            if not hist.empty:
                recent_volume = hist['Volume'].iloc[-1]
                avg_volume = hist['Volume'].mean()
                volume_surge = recent_volume / avg_volume if avg_volume > 0 else 0
                
                # High volume with price drop = dump warning
                price_change = hist['Close'].pct_change(1).iloc[-1]
                if volume_surge > 5 and price_change < -0.1:  # 5x volume, -10% price
                    return {
                        'exit_signal': True,
                        'exit_level': 'EMERGENCY',
                        'sell_percent': 1.0,  # Sell all
                        'exit_price': current_price,
                        'reason': 'DUMP DETECTED - High volume with price collapse',
                        'warning': True
                    }
        except:
            pass
        
        return None
    
    def add_insider_signal(self, ticker: str, signal_type: str, signal_strength: float):
        """Add insider trading signal to pump detection"""
        
        if ticker in self.active_pumps:
            pump = self.active_pumps[ticker]
            
            if signal_type == 'buy' and signal_strength > 0.5:
                pump.insider_activity = True
                pump.pump_strength = min(pump.pump_strength + 0.2, 1.0)
                print(f"[INSIDER BOOST] {ticker}: Pump strength increased to {pump.pump_strength:.1%}")
    
    def get_active_pumps(self) -> List[Dict]:
        """Get list of active pump patterns"""
        
        active = []
        for ticker, pump in self.active_pumps.items():
            # Remove pumps older than 7 days
            if datetime.now() - pump.detected_at > timedelta(days=7):
                continue
            
            active.append({
                'ticker': ticker,
                'pump_strength': pump.pump_strength,
                'volume_surge': pump.volume_surge,
                'price_acceleration': pump.price_acceleration,
                'detected_at': pump.detected_at,
                'exit_levels': pump.exit_levels
            })
        
        return active
