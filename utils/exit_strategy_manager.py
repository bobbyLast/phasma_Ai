"""
Exit Strategy Manager - Advanced Exit System for Trading Positions

Implements sophisticated exit strategies including:
- Peak detection using technical indicators
- Progressive selling at price multiples (2x, 3x, 4x, PI10)
- Performance-based hold vs sell decisions
- Risk management with stop-loss and trailing stops
- Position tracking and partial execution

Key Features:
- Real-time peak detection (RSI, MACD, volume analysis)
- Configurable selling rules at different return multiples
- Dynamic position sizing for partial sells
- Performance monitoring to determine continued holding
- Integration with existing trade memory system
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
    PRICE_TARGET = "PRICE_TARGET"
    PEAK_DETECTED = "PEAK_DETECTED"
    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    PERFORMANCE_DECLINE = "PERFORMANCE_DECLINE"
    MANUAL = "MANUAL"

@dataclass
class ExitRule:
    """Configuration for exit rules at different price multiples"""
    multiple: float  # 2.0, 3.0, 4.0, 10.0
    sell_percentage: float  # 0.25 for 25%, 0.5 for 50%
    description: str
    triggered: bool = False
    triggered_date: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class PositionExit:
    """Exit strategy state for a specific position"""
    ticker: str
    entry_price: float
    current_position_size: float
    original_position_size: float
    highest_price: float
    current_price: float
    
    # Exit rules
    exit_rules: List[ExitRule]
    
    # Technical indicators
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    volume_ratio: Optional[float] = None
    
    # Risk management
    stop_loss_price: Optional[float] = None
    trailing_stop_price: Optional[float] = None
    
    # Status
    last_analysis: str = ""
    last_signal: ExitSignal = ExitSignal.HOLD
    last_reason: SellReason = SellReason.MANUAL
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['exit_rules'] = [rule.to_dict() for rule in self.exit_rules]
        data['last_signal'] = self.last_signal.value
        data['last_reason'] = self.last_reason.value
        return data

class ExitStrategyManager:
    """
    Advanced exit strategy management system
    Handles peak detection, progressive selling, and performance monitoring
    """
    
    def __init__(self, config: Dict = None, data_dir: str = "data/exit_strategies"):
        self.config = config or {}
        self.data_dir = data_dir
        self.positions_file = os.path.join(data_dir, "position_exits.json")
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize positions storage
        self.positions: Dict[str, PositionExit] = {}
        self._load_positions()
        
        # Default exit rules configuration
        self.default_exit_rules = [
            ExitRule(2.0, 0.25, "2x return - sell 25%"),
            ExitRule(3.0, 0.25, "3x return - sell 25%"),
            ExitRule(4.0, 0.25, "4x return - sell 25%"),
            ExitRule(10.0, 0.50, "PI10 (10x) - sell remaining 50%")
        ]
        
        # Technical analysis parameters
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.peak_detection_periods = 14
        self.volume_lookback = 20
        
        print("🎯 Exit Strategy Manager initialized")
        print("   - Peak detection: RSI, MACD, volume analysis")
        print("   - Progressive selling: 2x, 3x, 4x, PI10 multiples")
        print("   - Risk management: Stop-loss, trailing stops")
    
    def add_position(self, ticker: str, entry_price: float, position_size: float,
                    custom_exit_rules: List[ExitRule] = None,
                    stop_loss_pct: float = 0.15,  # 15% stop loss
                    trailing_stop_pct: float = 0.10) -> bool:
        """
        Add a new position to track with exit strategy
        
        Args:
            ticker: Stock symbol
            entry_price: Entry price per share
            position_size: Number of shares or contract size
            custom_exit_rules: Custom exit rules (optional)
            stop_loss_pct: Stop loss percentage (default 15%)
            trailing_stop_pct: Trailing stop percentage (default 10%)
        
        Returns:
            bool: True if successfully added
        """
        try:
            # Calculate stop loss price
            stop_loss_price = entry_price * (1 - stop_loss_pct)
            
            # Create position with exit rules
            position = PositionExit(
                ticker=ticker,
                entry_price=entry_price,
                current_position_size=position_size,
                original_position_size=position_size,
                highest_price=entry_price,
                current_price=entry_price,
                exit_rules=custom_exit_rules or self.default_exit_rules.copy(),
                stop_loss_price=stop_loss_price,
                trailing_stop_price=entry_price * (1 - trailing_stop_pct)
            )
            
            self.positions[ticker] = position
            self._save_positions()
            
            print(f"✅ Added position: {ticker} @ ${entry_price:.2f}, size: {position_size}")
            print(f"   - Stop loss: ${stop_loss_price:.2f} ({stop_loss_pct*100:.0f}%)")
            print(f"   - Exit rules: {[rule.description for rule in position.exit_rules]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding position {ticker}: {str(e)}")
            return False
    
    def analyze_position(self, ticker: str) -> Optional[PositionExit]:
        """
        Analyze a position and determine exit signal
        
        Args:
            ticker: Stock symbol to analyze
        
        Returns:
            Updated PositionExit with exit signal
        """
        try:
            if ticker not in self.positions:
                print(f"❌ Position {ticker} not found")
                return None
            
            position = self.positions[ticker]
            
            # Get current price and technical data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2mo")
            
            if hist.empty:
                print(f"❌ No data available for {ticker}")
                return position
            
            current_price = hist['Close'].iloc[-1]
            position.current_price = current_price
            
            # Update highest price
            if current_price > position.highest_price:
                position.highest_price = current_price
                # Update trailing stop
                if position.trailing_stop_price:
                    new_trailing_stop = current_price * (1 - 0.10)  # 10% trailing
                    if new_trailing_stop > position.trailing_stop_price:
                        position.trailing_stop_price = new_trailing_stop
            
            # Calculate technical indicators
            position.rsi = self._calculate_rsi(hist)
            position.macd, position.macd_signal = self._calculate_macd(hist)
            position.volume_ratio = self._calculate_volume_ratio(hist)
            
            # Determine exit signal
            signal, reason = self._determine_exit_signal(position)
            position.last_signal = signal
            position.last_reason = reason
            
            # Generate analysis summary
            position.last_analysis = self._generate_analysis_summary(position)
            
            # Save updated position
            self._save_positions()
            
            return position
            
        except Exception as e:
            print(f"❌ Error analyzing position {ticker}: {str(e)}")
            return None
    
    def _determine_exit_signal(self, position: PositionExit) -> Tuple[ExitSignal, SellReason]:
        """
        Determine exit signal based on multiple factors
        
        Returns:
            Tuple of (ExitSignal, SellReason)
        """
        current_price = position.current_price
        entry_price = position.entry_price
        return_multiple = current_price / entry_price
        
        # Check emergency conditions first
        if position.stop_loss_price and current_price <= position.stop_loss_price:
            return ExitSignal.EMERGENCY_EXIT, SellReason.STOP_LOSS
        
        if position.trailing_stop_price and current_price <= position.trailing_stop_price:
            return ExitSignal.EMERGENCY_EXIT, SellReason.TRAILING_STOP
        
        # Check progressive selling rules
        for rule in position.exit_rules:
            if not rule.triggered and return_multiple >= rule.multiple:
                return ExitSignal.PARTIAL_SELL, SellReason.PRICE_TARGET
        
        # Check for peak detection (overbought conditions)
        if self._is_peak_detected(position):
            return ExitSignal.FULL_SELL, SellReason.PEAK_DETECTED
        
        # Check for performance decline
        if self._is_performance_declining(position):
            return ExitSignal.FULL_SELL, SellReason.PERFORMANCE_DECLINE
        
        # Default: hold
        return ExitSignal.HOLD, SellReason.MANUAL
    
    def _is_peak_detected(self, position: PositionExit) -> bool:
        """Detect if stock has peaked using technical indicators"""
        try:
            # RSI overbought
            if position.rsi and position.rsi > self.rsi_overbought:
                # Additional confirmation needed
                confirmations = 0
                
                # MACD bearish divergence
                if position.macd and position.macd_signal and position.macd < position.macd_signal:
                    confirmations += 1
                
                # Volume decline
                if position.volume_ratio and position.volume_ratio < 0.7:
                    confirmations += 1
                
                # Price below recent high
                if position.current_price < position.highest_price * 0.95:
                    confirmations += 1
                
                # Need at least 2 confirmations
                return confirmations >= 2
            
            return False
            
        except Exception:
            return False
    
    def _is_performance_declining(self, position: PositionExit) -> bool:
        """Check if position performance is declining"""
        try:
            # Recent price action
            current_price = position.current_price
            highest_price = position.highest_price
            
            # If down 10% from peak with overbought conditions
            if current_price < highest_price * 0.90:
                if position.rsi and position.rsi > 65:  # Still elevated but declining
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _calculate_rsi(self, hist: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate RSI indicator"""
        try:
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not rsi.empty else None
            
        except Exception:
            return None
    
    def _calculate_macd(self, hist: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
        """Calculate MACD indicator"""
        try:
            exp1 = hist['Close'].ewm(span=12).mean()
            exp2 = hist['Close'].ewm(span=26).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9).mean()
            
            return macd.iloc[-1], signal.iloc[-1]
            
        except Exception:
            return None, None
    
    def _calculate_volume_ratio(self, hist: pd.DataFrame) -> Optional[float]:
        """Calculate current volume vs average volume ratio"""
        try:
            current_volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].tail(20).mean()
            
            return current_volume / avg_volume if avg_volume > 0 else None
            
        except Exception:
            return None
    
    def _generate_analysis_summary(self, position: PositionExit) -> str:
        """Generate human-readable analysis summary"""
        try:
            current_price = position.current_price
            entry_price = position.entry_price
            return_pct = ((current_price - entry_price) / entry_price) * 100
            
            summary = f"Return: {return_pct:+.1f}% @ ${current_price:.2f}\n"
            
            # Technical indicators
            if position.rsi:
                summary += f"RSI: {position.rsi:.1f} "
                if position.rsi > 70:
                    summary += "(Overbought) "
                elif position.rsi < 30:
                    summary += "(Oversold) "
            
            if position.volume_ratio:
                summary += f"Volume: {position.volume_ratio:.1f}x "
            
            # Exit rules status
            triggered_rules = [r for r in position.exit_rules if r.triggered]
            if triggered_rules:
                summary += f"\nTriggered: {[r.description for r in triggered_rules]}"
            
            # Risk levels
            if position.stop_loss_price and current_price <= position.stop_loss_price * 1.05:
                summary += f"\n⚠️ Near stop loss: ${position.stop_loss_price:.2f}"
            
            return summary.strip()
            
        except Exception:
            return "Analysis error"
    
    def execute_exit_signal(self, ticker: str) -> Dict:
        """
        Execute the exit signal for a position
        
        Returns:
            Dict with execution details
        """
        try:
            position = self.analyze_position(ticker)
            if not position:
                return {"error": "Position not found"}
            
            signal = position.last_signal
            reason = position.last_reason
            
            execution = {
                "ticker": ticker,
                "signal": signal.value,
                "reason": reason.value,
                "current_price": position.current_price,
                "current_position": position.current_position_size,
                "execution_details": []
            }
            
            if signal == ExitSignal.PARTIAL_SELL:
                # Find next untriggered rule
                for rule in position.exit_rules:
                    if not rule.triggered:
                        return_multiple = position.current_price / position.entry_price
                        if return_multiple >= rule.multiple:
                            # Execute partial sell
                            sell_amount = position.original_position_size * rule.sell_percentage
                            new_position_size = position.current_position_size - sell_amount
                            
                            # Update position
                            position.current_position_size = new_position_size
                            rule.triggered = True
                            rule.triggered_date = datetime.now(timezone.utc).isoformat()
                            
                            execution["execution_details"] = [
                                f"Sell {rule.sell_percentage*100:.0f}% at {rule.multiple}x return",
                                f"Shares: {sell_amount:.2f}",
                                f"Remaining: {new_position_size:.2f}"
                            ]
                            
                            self._save_positions()
                            break
            
            elif signal == ExitSignal.FULL_SELL or signal == ExitSignal.EMERGENCY_EXIT:
                # Execute full sell
                execution["execution_details"] = [
                    f"Sell full position: {position.current_position_size:.2f} shares",
                    f"Reason: {reason.value}"
                ]
                
                # Remove position after full sell
                del self.positions[ticker]
                self._save_positions()
            
            else:  # HOLD
                execution["execution_details"] = ["Hold position - no action needed"]
            
            return execution
            
        except Exception as e:
            return {"error": f"Execution error: {str(e)}"}
    
    def get_all_positions(self) -> Dict[str, PositionExit]:
        """Get all tracked positions"""
        return self.positions.copy()
    
    def get_position_summary(self) -> List[Dict]:
        """Get summary of all positions"""
        summary = []
        
        for ticker, position in self.positions.items():
            return_pct = ((position.current_price - position.entry_price) / position.entry_price) * 100
            
            summary.append({
                "ticker": ticker,
                "entry_price": position.entry_price,
                "current_price": position.current_price,
                "return_pct": return_pct,
                "position_size": position.current_position_size,
                "original_size": position.original_position_size,
                "signal": position.last_signal.value,
                "rsi": position.rsi,
                "analysis": position.last_analysis
            })
        
        return summary
    
    def _load_positions(self):
        """Load positions from file"""
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file, 'r') as f:
                    data = json.load(f)
                
                for ticker, pos_data in data.items():
                    # Reconstruct exit rules
                    exit_rules = []
                    for rule_data in pos_data.get('exit_rules', []):
                        rule = ExitRule(
                            multiple=rule_data['multiple'],
                            sell_percentage=rule_data['sell_percentage'],
                            description=rule_data['description'],
                            triggered=rule_data.get('triggered', False),
                            triggered_date=rule_data.get('triggered_date')
                        )
                        exit_rules.append(rule)
                    
                    # Reconstruct position
                    position = PositionExit(
                        ticker=pos_data['ticker'],
                        entry_price=pos_data['entry_price'],
                        current_position_size=pos_data['current_position_size'],
                        original_position_size=pos_data['original_position_size'],
                        highest_price=pos_data['highest_price'],
                        current_price=pos_data['current_price'],
                        exit_rules=exit_rules,
                        rsi=pos_data.get('rsi'),
                        stop_loss_price=pos_data.get('stop_loss_price'),
                        trailing_stop_price=pos_data.get('trailing_stop_price'),
                        last_analysis=pos_data.get('last_analysis', ''),
                        last_signal=ExitSignal(pos_data.get('last_signal', 'HOLD')),
                        last_reason=SellReason(pos_data.get('last_reason', 'MANUAL'))
                    )
                    
                    self.positions[ticker] = position
                
                print(f"✅ Loaded {len(self.positions)} positions")
        
        except Exception as e:
            print(f"⚠️ Error loading positions: {str(e)}")
    
    def _save_positions(self):
        """Save positions to file"""
        try:
            data = {}
            for ticker, position in self.positions.items():
                data[ticker] = position.to_dict()
            
            with open(self.positions_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving positions: {str(e)}")

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Exit Strategy Manager...")
    
    manager = ExitStrategyManager()
    
    # Add test positions
    test_positions = [
        {
            "ticker": "AAPL",
            "entry_price": 150.00,
            "position_size": 100
        },
        {
            "ticker": "TSLA", 
            "entry_price": 200.00,
            "position_size": 50
        }
    ]
    
    # Add positions
    for pos in test_positions:
        manager.add_position(**pos)
    
    print(f"\n📊 Position Summary:")
    summary = manager.get_position_summary()
    for item in summary:
        print(f"   {item['ticker']}: {item['return_pct']:+.1f}% @ ${item['current_price']:.2f}")
        print(f"      Signal: {item['signal']}, Size: {item['position_size']}/{item['original_size']}")
    
    print(f"\n✅ Exit Strategy Manager working!")
    print(f"   - Peak detection: RSI, MACD, volume analysis")
    print(f"   - Progressive selling: 2x, 3x, 4x, PI10 multiples")
    print(f"   - Risk management: Stop-loss, trailing stops")
    print(f"   - Ready for integration with trading system")
