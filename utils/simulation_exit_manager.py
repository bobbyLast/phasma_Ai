"""
Simulation-Based Exit Manager - Maximizes Profits Using Monte Carlo Targets

Instead of selling on arbitrary 2x/3x/4x multiples, this manager:
- Uses Monte Carlo simulation target_price as primary exit signal
- Incorporates optimal_exit_day from simulations
- Holds winners until they reach their simulated optimal exit
- Only exits early on crash detection or stop-loss
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os

class ExitSignal(Enum):
    HOLD = "HOLD"
    PARTIAL_SELL = "PARTIAL_SELL"
    FULL_SELL = "FULL_SELL"
    EMERGENCY_EXIT = "EMERGENCY_EXIT"

class SellReason(Enum):
    SIMULATION_TARGET = "SIMULATION_TARGET"  # Hit Monte Carlo target price
    OPTIMAL_EXIT_DAY = "OPTIMAL_EXIT_DAY"    # Reached optimal exit day
    CRASH_DETECTED = "CRASH_DETECTED"        # Market crash conditions
    STOP_LOSS = "STOP_LOSS"                  # Hit simulation stop loss
    TECHNICAL_PEAK = "TECHNICAL_PEAK"        # Technical indicators show peak
    MANUAL = "MANUAL"

@dataclass
class SimulationExit:
    """Exit strategy based on Monte Carlo simulations"""
    ticker: str
    entry_price: float
    current_price: float
    target_price: float        # From Monte Carlo simulation
    stop_loss: float          # From Monte Carlo simulation
    optimal_exit_day: int     # From Monte Carlo simulation
    entry_date: datetime
    days_held: int
    
    # Current status (calculated)
    price_progress: float = 0.0      # % of target reached
    profit_pct: float = 0.0         # Current profit %
    is_crashing: bool = False
    
    # Exit decision
    last_signal: ExitSignal = ExitSignal.HOLD
    last_reason: SellReason = SellReason.MANUAL
    confidence: float = 0.0   # Simulation confidence
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['last_signal'] = self.last_signal.value
        data['last_reason'] = self.last_reason.value
        data['entry_date'] = self.entry_date.isoformat()
        return data

class SimulationExitManager:
    """
    Exit manager that maximizes profits using Monte Carlo simulation targets
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.positions = {}
        self.crash_detector = None
        
        # Load existing positions
        self._load_positions()
    
    def _load_positions(self):
        """Load positions from state file"""
        try:
            # Load from phasma_state.json
            state_file = "phasma_state.json"
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    
                # Extract open positions with simulation data
                open_positions = state.get('risk_state', {}).get('open_positions', {})
                
                for ticker, pos_data in open_positions.items():
                    if pos_data.get('signal', {}).get('simulation_results'):
                        sim_results = pos_data['signal']['simulation_results']
                        signal_data = pos_data['signal']
                        
                        # Get entry price from signal
                        entry_price = signal_data.get('entry_price', 0)
                        if entry_price == 0:
                            # Fallback to current price if entry_price is 0
                            entry_price = sim_results.get('target_price', 50.0) * 0.8  # Assume 80% of target
                        
                        # Create simulation exit
                        exit_pos = SimulationExit(
                            ticker=ticker,
                            entry_price=entry_price,
                            current_price=sim_results.get('target_price', entry_price),
                            target_price=sim_results.get('target_price', 0),
                            stop_loss=sim_results.get('stop_loss', entry_price * 0.9),
                            optimal_exit_day=sim_results.get('holding_days', 30),
                            entry_date=datetime.fromisoformat(pos_data.get('entry_time', datetime.now().isoformat())),
                            days_held=0,
                            confidence=sim_results.get('win_rate', 0.5)
                        )
                        
                        self.positions[ticker] = exit_pos
                        print(f"Loaded simulation exit for {ticker}: target=${exit_pos.target_price:.2f}, stop=${exit_pos.stop_loss:.2f}")
                        
        except Exception as e:
            print(f"Error loading positions: {e}")
    
    def analyze_position(self, ticker: str) -> Optional[SimulationExit]:
        """
        Analyze position using simulation targets
        
        Returns:
            Updated SimulationExit with exit signal
        """
        if ticker not in self.positions:
            return None
        
        position = self.positions[ticker]
        
        # Get current price
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.history(period='1d')['Close'].iloc[-1]
            position.current_price = current_price
        except:
            return position
        
        # Calculate metrics
        position.days_held = (datetime.now() - position.entry_date).days
        
        # Avoid division by zero
        if position.entry_price > 0 and position.target_price != position.entry_price:
            position.price_progress = (current_price - position.entry_price) / (position.target_price - position.entry_price)
            position.profit_pct = (current_price - position.entry_price) / position.entry_price * 100
        else:
            position.price_progress = 0.0
            position.profit_pct = 0.0
        
        # Check exit conditions (in order of priority)
        
        # 1. Check if hit simulation target price
        if current_price >= position.target_price:
            position.last_signal = ExitSignal.FULL_SELL
            position.last_reason = SellReason.SIMULATION_TARGET
            print(f"{ticker}: HIT TARGET ${position.target_price:.2f} - SELL")
            return position
        
        # 2. Check if reached optimal exit day without hitting target
        if position.days_held >= position.optimal_exit_day:
            if position.profit_pct > 0:  # Only sell if profitable
                position.last_signal = ExitSignal.FULL_SELL
                position.last_reason = SellReason.OPTIMAL_EXIT_DAY
                print(f"{ticker}: OPTIMAL EXIT DAY ({position.optimal_exit_day}d) - SELL at {position.profit_pct:.1f}%")
                return position
        
        # 3. Check for crash conditions
        if self._is_crashing(ticker, current_price, position):
            position.last_signal = ExitSignal.EMERGENCY_EXIT
            position.last_reason = SellReason.CRASH_DETECTED
            position.is_crashing = True
            print(f"{ticker}: CRASH DETECTED - EMERGENCY EXIT")
            return position
        
        # 4. Check stop loss
        if current_price <= position.stop_loss:
            position.last_signal = ExitSignal.FULL_SELL
            position.last_reason = SellReason.STOP_LOSS
            print(f"{ticker}: STOP LOSS ${position.stop_loss:.2f} - SELL")
            return position
        
        # 5. Check for technical peak (only if high profit)
        if position.profit_pct > 10 and self._is_technical_peak(ticker):
            position.last_signal = ExitSignal.FULL_SELL
            position.last_reason = SellReason.TECHNICAL_PEAK
            print(f"{ticker}: TECHNICAL PEAK at {position.profit_pct:.1f}% - SELL")
            return position
        
        # Default: HOLD
        position.last_signal = ExitSignal.HOLD
        position.last_reason = SellReason.MANUAL
        
        return position
    
    def _is_crashing(self, ticker: str, current_price: float, position: SimulationExit) -> bool:
        """Check if stock is crashing"""
        try:
            # Get recent price data
            stock = yf.Ticker(ticker)
            hist = stock.history(period='5d')
            
            if len(hist) < 2:
                return False
            
            # Check for sharp drop
            recent_drop = (hist['Close'].iloc[-2] - current_price) / hist['Close'].iloc[-2]
            
            # Crash if dropped >10% in one day or >15% in two days
            if recent_drop > 0.10:
                return True
            
            two_day_drop = (hist['Close'].iloc[-3] - current_price) / hist['Close'].iloc[-3] if len(hist) >= 3 else 0
            if two_day_drop > 0.15:
                return True
            
            # Check volume spike on down day
            volume_ratio = hist['Volume'].iloc[-1] / hist['Volume'].iloc[-2] if hist['Volume'].iloc[-2] > 0 else 1
            if recent_drop > 0.05 and volume_ratio > 2.0:
                return True
            
        except:
            pass
        
        return False
    
    def _is_technical_peak(self, ticker: str) -> bool:
        """Check if stock shows technical signs of peaking"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='14d')
            
            if len(hist) < 14:
                return False
            
            # Calculate RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Check for overbought RSI
            if current_rsi > 75:
                # Check for bearish divergence
                recent_high = hist['Close'].iloc[-3:].max()
                older_high = hist['Close'].iloc[-10:-3].max()
                
                if recent_high > older_high and rsi.iloc[-3:].max() < rsi.iloc[-10:-3].max():
                    return True
            
        except:
            pass
        
        return False
    
    def get_all_positions(self) -> Dict[str, SimulationExit]:
        """Get all positions"""
        return self.positions
    
    def remove_position(self, ticker: str):
        """Remove position after exit"""
        if ticker in self.positions:
            del self.positions[ticker]
            print(f"Removed {ticker} from simulation exit tracking")
    
    def print_status(self):
        """Print current status of all positions"""
        if not self.positions:
            print("No positions in simulation exit manager")
            return
        
        print("\n" + "="*60)
        print("SIMULATION-BASED EXIT MANAGER STATUS")
        print("="*60)
        
        for ticker, pos in self.positions.items():
            print(f"\n{ticker}:")
            print(f"  Entry: ${pos.entry_price:.2f} | Current: ${pos.current_price:.2f}")
            print(f"  Target: ${pos.target_price:.2f} | Stop: ${pos.stop_loss:.2f}")
            print(f"  Progress: {pos.price_progress:.1%} | Profit: {pos.profit_pct:.1f}%")
            print(f"  Days: {pos.days_held}/{pos.optimal_exit_day}")
            print(f"  Signal: {pos.last_signal.value} | Reason: {pos.last_reason.value}")
        
        print("="*60)
