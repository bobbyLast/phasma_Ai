"""
Profit Maximization Exit Manager
Prevents early exits and maximizes profits by:
- Using trailing stop losses
- Implementing minimum holding periods
- Partial profit taking strategies
- Momentum-based exit decisions
- Volatility-adjusted targets
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf


class ProfitMaximizationExitManager:
    """Advanced exit manager focused on maximizing profits"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.db_path = "profit_maximization_exits.db"
        self._init_database()
        
        # Profit maximization settings
        self.trailing_stop_pct = config.get("trailing_stop_pct", 0.20)  # 20% trailing
        self.min_hold_days = config.get("min_hold_days", 7)  # Minimum 7 days
        self.max_hold_days = config.get("max_hold_days", 90)  # Maximum 90 days
        self.partial_profit_levels = config.get("partial_profit_levels", [0.30, 0.60, 1.00])
        self.partial_sell_sizes = config.get("partial_sell_sizes", [0.25, 0.25, 0.50])
        self.momentum_threshold = config.get("momentum_threshold", 0.40)  # RSI below 40 = exit signal
        
    def _init_database(self):
        """Initialize database for tracking positions and exits"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY,
                ticker TEXT NOT NULL,
                entry_price REAL NOT NULL,
                entry_date TEXT NOT NULL,
                current_shares REAL NOT NULL,
                original_shares REAL NOT NULL,
                highest_price REAL NOT NULL,
                trailing_stop REAL NOT NULL,
                last_partial_sell REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exit_history (
                id INTEGER PRIMARY KEY,
                position_id INTEGER,
                exit_date TEXT NOT NULL,
                exit_price REAL NOT NULL,
                shares_sold REAL NOT NULL,
                exit_reason TEXT NOT NULL,
                profit_pct REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (position_id) REFERENCES positions (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_position(self, ticker: str, entry_price: float, shares: float) -> int:
        """Add a new position to track"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO positions 
            (ticker, entry_price, entry_date, current_shares, original_shares, 
             highest_price, trailing_stop)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            entry_price,
            datetime.now().isoformat(),
            shares,
            shares,
            entry_price,
            entry_price * (1 - self.trailing_stop_pct)
        ))
        
        position_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return position_id
    
    def check_exit_signals(self, ticker: str, current_price: float) -> Dict:
        """Check if position should exit or partially sell"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM positions 
            WHERE ticker = ? AND status = 'active' AND current_shares > 0
        """, (ticker,))
        
        positions = cursor.fetchall()
        conn.close()
        
        if not positions:
            return {"action": "NO_POSITION", "reason": "No active position found"}
        
        results = []
        for pos in positions:
            result = self._analyze_position(pos, current_price)
            results.append(result)
        
        # Return the most urgent action
        if results:
            return max(results, key=lambda x: x.get("urgency", 0))
        return {"action": "HOLD", "reason": "No exit signals"}
    
    def _analyze_position(self, position: Tuple, current_price: float) -> Dict:
        """Analyze a single position for exit signals"""
        pos_id, ticker, entry_price, entry_date, current_shares, original_shares, \
        highest_price, trailing_stop, last_partial_sell, status, created_at = position
        
        entry_dt = datetime.fromisoformat(entry_date)
        days_held = (datetime.now() - entry_dt).days
        current_profit_pct = (current_price - entry_price) / entry_price
        
        # Update highest price and trailing stop if needed
        if current_price > highest_price:
            highest_price = current_price
            # Dynamic trailing stop based on profit level
            if current_profit_pct < 0.30:
                trailing_pct = self.trailing_stop_pct
            elif current_profit_pct < 0.60:
                trailing_pct = 0.15  # Tighten to 15%
            else:
                trailing_pct = 0.10  # Tighten to 10% for big profits
            
            trailing_stop = current_price * (1 - trailing_pct)
            self._update_position(pos_id, highest_price, trailing_stop)
        
        # Check for emergency stop loss
        if current_price <= trailing_stop:
            return {
                "action": "EXIT_ALL",
                "reason": f"Trailing stop triggered at ${current_price:.2f}",
                "urgency": 100,
                "position_id": pos_id,
                "shares": current_shares
            }
        
        # Check minimum holding period
        if days_held < self.min_hold_days:
            return {
                "action": "HOLD",
                "reason": f"Minimum holding period ({self.min_hold_days} days) not met",
                "urgency": 0,
                "days_held": days_held
            }
        
        # Check for partial profit taking
        for i, (level, sell_size) in enumerate(zip(self.partial_profit_levels, self.partial_sell_sizes)):
            if current_profit_pct >= level and last_partial_sell < level:
                shares_to_sell = original_shares * sell_size
                if shares_to_sell <= current_shares:
                    return {
                        "action": "PARTIAL_SELL",
                        "reason": f"Take partial profits at {level*100:.0f}% gain",
                        "urgency": 50 + (level * 20),
                        "position_id": pos_id,
                        "shares": shares_to_sell,
                        "sell_percent": sell_size * 100
                    }
        
        # Check momentum indicators
        momentum_signal = self._check_momentum(ticker)
        if momentum_signal["exit"]:
            return {
                "action": "EXIT_ALL",
                "reason": f"Momentum weakness: {momentum_signal['reason']}",
                "urgency": 70,
                "position_id": pos_id,
                "shares": current_shares
            }
        
        # Check maximum holding period
        if days_held > self.max_hold_days:
            return {
                "action": "EXIT_ALL",
                "reason": f"Maximum holding period ({self.max_hold_days} days) exceeded",
                "urgency": 60,
                "position_id": pos_id,
                "shares": current_shares
            }
        
        # Check for negative catalysts
        catalyst_signal = self._check_catalysts(ticker)
        if catalyst_signal["negative"]:
            return {
                "action": "EXIT_ALL",
                "reason": f"Negative catalyst: {catalyst_signal['reason']}",
                "urgency": 80,
                "position_id": pos_id,
                "shares": current_shares
            }
        
        # Default: hold with confidence
        return {
            "action": "HOLD",
            "reason": f"Strong position (+{current_profit_pct*100:.1f}%, momentum: {momentum_signal['strength']})",
            "urgency": 0,
            "profit_pct": current_profit_pct,
            "days_held": days_held
        }
    
    def _check_momentum(self, ticker: str) -> Dict:
        """Check momentum indicators for exit signals"""
        try:
            # Get recent price data
            data = yf.Ticker(ticker).history(period="30d")
            if len(data) < 14:
                return {"exit": False, "strength": "insufficient_data"}
            
            # Calculate RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Check volume trend
            recent_vol = data['Volume'][-5:].mean()
            avg_vol = data['Volume'][:-5].mean()
            vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
            
            # Check price momentum
            short_ma = data['Close'].rolling(window=10).mean().iloc[-1]
            long_ma = data['Close'].rolling(window=30).mean().iloc[-1]
            price_vs_ma = (data['Close'].iloc[-1] - short_ma) / short_ma
            
            # Exit signals
            exit_reasons = []
            if current_rsi < self.momentum_threshold * 100:
                exit_reasons.append(f"RSI low ({current_rsi:.1f})")
            if vol_ratio < 0.5:
                exit_reasons.append(f"Volume drying up ({vol_ratio:.1f}x average)")
            if price_vs_ma < -0.05:
                exit_reasons.append(f"Price below 10-day MA ({price_vs_ma*100:.1f}%)")
            
            if exit_reasons:
                return {
                    "exit": True,
                    "reason": ", ".join(exit_reasons),
                    "strength": "weak"
                }
            
            # Determine strength
            if current_rsi > 70 and vol_ratio > 1.5 and price_vs_ma > 0.05:
                strength = "very_strong"
            elif current_rsi > 60 and vol_ratio > 1.2:
                strength = "strong"
            elif current_rsi > 50:
                strength = "moderate"
            else:
                strength = "weak"
            
            return {"exit": False, "strength": strength, "rsi": current_rsi}
            
        except Exception as e:
            return {"exit": False, "strength": "error", "error": str(e)}
    
    def _check_catalysts(self, ticker: str) -> Dict:
        """Check for negative news catalysts"""
        # This would integrate with news engine
        # For now, return no negative catalysts
        return {"negative": False, "reason": None}
    
    def _update_position(self, position_id: int, highest_price: float, trailing_stop: float):
        """Update position's highest price and trailing stop"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE positions 
            SET highest_price = ?, trailing_stop = ?
            WHERE id = ?
        """, (highest_price, trailing_stop, position_id))
        
        conn.commit()
        conn.close()
    
    def execute_exit(self, position_id: int, shares: float, exit_price: float, reason: str):
        """Execute an exit (full or partial)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get position details
        cursor.execute("SELECT * FROM positions WHERE id = ?", (position_id,))
        position = cursor.fetchone()
        
        if not position:
            return False
        
        ticker = position[1]
        entry_price = position[2]
        current_shares = position[4]
        original_shares = position[5]
        last_partial_sell = position[8]
        
        # Calculate profit
        profit_pct = (exit_price - entry_price) / entry_price
        
        # Record exit
        cursor.execute("""
            INSERT INTO exit_history 
            (position_id, exit_date, exit_price, shares_sold, exit_reason, profit_pct)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            position_id,
            datetime.now().isoformat(),
            exit_price,
            shares,
            reason,
            profit_pct
        ))
        
        # Update position
        new_shares = current_shares - shares
        if new_shares <= 0.01:  # Fully closed
            cursor.execute("""
                UPDATE positions 
                SET status = 'closed', current_shares = 0
                WHERE id = ?
            """, (position_id,))
        else:
            # Update partial sell level
            total_sold = (original_shares - new_shares) / original_shares
            cursor.execute("""
                UPDATE positions 
                SET current_shares = ?, last_partial_sell = ?
                WHERE id = ?
            """, (new_shares, total_sold, position_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ EXIT EXECUTED: {ticker}")
        print(f"   Sold: {shares:.2f} shares at ${exit_price:.2f}")
        print(f"   Profit: {profit_pct*100:.1f}%")
        print(f"   Reason: {reason}")
        
        return True
    
    def get_active_positions(self) -> List[Dict]:
        """Get all active positions with their status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM positions 
            WHERE status = 'active' AND current_shares > 0
        """)
        
        positions = []
        for row in cursor.fetchall():
            positions.append({
                "id": row[0],
                "ticker": row[1],
                "entry_price": row[2],
                "entry_date": row[3],
                "current_shares": row[4],
                "original_shares": row[5],
                "highest_price": row[6],
                "trailing_stop": row[7],
                "current_price": row[11] if len(row) > 11 else None
            })
        
        conn.close()
        return positions
    
    def generate_daily_report(self) -> Dict:
        """Generate daily profit maximization report"""
        positions = self.get_active_positions()
        
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "active_positions": len(positions),
            "positions": []
        }
        
        for pos in positions:
            if pos["current_price"]:
                profit_pct = (pos["current_price"] - pos["entry_price"]) / pos["entry_price"]
                trailing_distance = (pos["current_price"] - pos["trailing_stop"]) / pos["current_price"]
                
                report["positions"].append({
                    "ticker": pos["ticker"],
                    "profit_pct": profit_pct * 100,
                    "trailing_stop_distance": trailing_distance * 100,
                    "days_held": (datetime.now() - datetime.fromisoformat(pos["entry_date"])).days
                })
        
        return report
