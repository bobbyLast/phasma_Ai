"""
Trader Call Logger - Stage 1 of External Trader Tracking System

Captures and stores external trader calls for performance analysis and smart money evaluation.
This is the intake layer that logs who called what, when, and with what bias.

Data Schema:
- trader_id: Unique identifier for trader/guru
- ticker: Stock symbol being called
- direction: LONG, SHORT, or BULLISH/BEARISH bias
- timestamp: When the call was made
- horizon: DAY_TRADE, SWING, LONG_TERM
- entry_price: Price at time of call (optional)
- notes: Additional context (optional)
- source: Where the call came from (X, Discord, manual, etc.)
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict
import csv

class Direction(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

class Horizon(Enum):
    DAY_TRADE = "DAY_TRADE"
    SWING = "SWING"
    LONG_TERM = "LONG_TERM"
    UNKNOWN = "UNKNOWN"

@dataclass
class TraderCall:
    """Structured representation of a trader call"""
    trader_id: str
    ticker: str
    direction: Direction
    timestamp: str
    horizon: Horizon
    entry_price: Optional[float] = None
    notes: Optional[str] = None
    source: str = "manual"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage"""
        data = asdict(self)
        data['direction'] = self.direction.value
        data['horizon'] = self.horizon.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TraderCall':
        """Create from dictionary (for loading from storage)"""
        data['direction'] = Direction(data['direction'])
        data['horizon'] = Horizon(data['horizon'])
        return cls(**data)

class TraderCallLogger:
    """
    Logs and manages external trader calls
    Stage 1: Basic capture and storage functionality
    """
    
    def __init__(self, data_dir: str = "data/trader_calls"):
        self.data_dir = data_dir
        self.calls_file = os.path.join(data_dir, "trader_calls.json")
        self.csv_file = os.path.join(data_dir, "trader_calls.csv")
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize storage files
        self._init_storage()
        
        print("📝 Trader Call Logger initialized")
        print(f"   - Data directory: {self.data_dir}")
        print(f"   - JSON storage: {self.calls_file}")
        print(f"   - CSV export: {self.csv_file}")
    
    def _init_storage(self):
        """Initialize storage files if they don't exist"""
        if not os.path.exists(self.calls_file):
            with open(self.calls_file, 'w') as f:
                json.dump([], f)
            print(f"✅ Created JSON storage: {self.calls_file}")
        
        # Initialize CSV with headers
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'trader_id', 'ticker', 'direction', 'timestamp', 'horizon',
                    'entry_price', 'notes', 'source'
                ])
            print(f"✅ Created CSV export: {self.csv_file}")
    
    def log_call(self, trader_id: str, ticker: str, direction: str, 
                 horizon: str = "UNKNOWN", entry_price: Optional[float] = None,
                 notes: Optional[str] = None, source: str = "manual") -> bool:
        """
        Log a new trader call
        
        Args:
            trader_id: Unique identifier for the trader
            ticker: Stock symbol (e.g., "AAPL", "TSLA")
            direction: "LONG", "SHORT", "BULLISH", "BEARISH"
            horizon: "DAY_TRADE", "SWING", "LONG_TERM", "UNKNOWN"
            entry_price: Price at time of call (optional)
            notes: Additional context (optional)
            source: Where this call came from
        
        Returns:
            bool: True if successfully logged
        """
        try:
            # Validate and normalize inputs
            ticker = ticker.upper().strip()
            
            try:
                direction_enum = Direction(direction.upper())
            except ValueError:
                print(f"⚠️ Invalid direction: {direction}. Using NEUTRAL")
                direction_enum = Direction.NEUTRAL
            
            try:
                horizon_enum = Horizon(horizon.upper())
            except ValueError:
                print(f"⚠️ Invalid horizon: {horizon}. Using UNKNOWN")
                horizon_enum = Horizon.UNKNOWN
            
            # Create timestamp in UTC
            timestamp = datetime.now(timezone.utc).isoformat()
            
            # Create call object
            call = TraderCall(
                trader_id=trader_id,
                ticker=ticker,
                direction=direction_enum,
                timestamp=timestamp,
                horizon=horizon_enum,
                entry_price=entry_price,
                notes=notes,
                source=source
            )
            
            # Load existing calls
            calls = self.load_calls()
            
            # Add new call
            calls.append(call)
            
            # Save to JSON
            self._save_calls(calls)
            
            # Append to CSV
            self._append_to_csv(call)
            
            print(f"✅ Logged call: {trader_id} {direction_enum.value} {ticker} ({horizon_enum.value})")
            return True
            
        except Exception as e:
            print(f"❌ Error logging call: {str(e)}")
            return False
    
    def load_calls(self) -> List[TraderCall]:
        """Load all trader calls from storage"""
        try:
            with open(self.calls_file, 'r') as f:
                data = json.load(f)
            
            calls = []
            for call_data in data:
                calls.append(TraderCall.from_dict(call_data))
            
            return calls
            
        except Exception as e:
            print(f"❌ Error loading calls: {str(e)}")
            return []
    
    def _save_calls(self, calls: List[TraderCall]):
        """Save calls to JSON storage"""
        try:
            calls_data = [call.to_dict() for call in calls]
            with open(self.calls_file, 'w') as f:
                json.dump(calls_data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving calls: {str(e)}")
    
    def _append_to_csv(self, call: TraderCall):
        """Append single call to CSV file"""
        try:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    call.trader_id,
                    call.ticker,
                    call.direction.value,
                    call.timestamp,
                    call.horizon.value,
                    call.entry_price,
                    call.notes,
                    call.source
                ])
        except Exception as e:
            print(f"❌ Error appending to CSV: {str(e)}")
    
    def get_calls_by_trader(self, trader_id: str) -> List[TraderCall]:
        """Get all calls from a specific trader"""
        calls = self.load_calls()
        return [call for call in calls if call.trader_id == trader_id]
    
    def get_calls_by_ticker(self, ticker: str) -> List[TraderCall]:
        """Get all calls for a specific ticker"""
        calls = self.load_calls()
        return [call for call in calls if call.ticker == ticker.upper()]
    
    def get_recent_calls(self, limit: int = 50) -> List[TraderCall]:
        """Get the most recent calls"""
        calls = self.load_calls()
        # Sort by timestamp (newest first)
        calls.sort(key=lambda x: x.timestamp, reverse=True)
        return calls[:limit]
    
    def get_summary_stats(self) -> Dict:
        """Get basic summary statistics"""
        calls = self.load_calls()
        
        if not calls:
            return {
                'total_calls': 0,
                'unique_traders': 0,
                'unique_tickers': 0,
                'directions': {},
                'horizons': {}
            }
        
        traders = set(call.trader_id for call in calls)
        tickers = set(call.ticker for call in calls)
        
        direction_counts = {}
        for direction in Direction:
            direction_counts[direction.value] = sum(1 for call in calls if call.direction == direction)
        
        horizon_counts = {}
        for horizon in Horizon:
            horizon_counts[horizon.value] = sum(1 for call in calls if call.horizon == horizon)
        
        return {
            'total_calls': len(calls),
            'unique_traders': len(traders),
            'unique_tickers': len(tickers),
            'directions': direction_counts,
            'horizons': horizon_counts,
            'date_range': {
                'earliest': min(call.timestamp for call in calls),
                'latest': max(call.timestamp for call in calls)
            }
        }

# Example usage and testing
if __name__ == "__main__":
    logger = TraderCallLogger()
    
    # Test logging some sample calls
    print("\n🧪 Testing Trader Call Logger...")
    
    # Sample calls from different traders with realistic historical data
    test_calls = [
        {
            'trader_id': 'stock_guru_123',
            'ticker': 'AAPL',
            'direction': 'LONG',
            'horizon': 'SWING',
            'entry_price': 175.00,  # Realistic price from Nov 2024
            'notes': 'Breakout above resistance',
            'source': 'manual'
        },
        {
            'trader_id': 'penny_king',
            'ticker': 'TSLA',
            'direction': 'BULLISH',
            'horizon': 'DAY_TRADE',
            'entry_price': 320.50,  # Realistic price from Nov 2024
            'notes': 'Momentum play',
            'source': 'manual'
        },
        {
            'trader_id': 'value_investor',
            'ticker': 'MSFT',
            'direction': 'LONG',
            'horizon': 'LONG_TERM',
            'entry_price': 410.00,  # Realistic price from Nov 2024
            'notes': 'Strong fundamentals, good entry point',
            'source': 'manual'
        }
    ]
    
    # Log the test calls
    for call_data in test_calls:
        logger.log_call(**call_data)
    
    # Show summary stats
    print("\n📊 Summary Statistics:")
    stats = logger.get_summary_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Show recent calls
    print("\n📝 Recent Calls:")
    recent = logger.get_recent_calls(5)
    for i, call in enumerate(recent, 1):
        print(f"   {i}. {call.trader_id} {call.direction.value} {call.ticker} ({call.horizon.value}) - {call.timestamp}")
    
    print(f"\n✅ Stage 1 complete: Basic logging infrastructure working!")
    print(f"   - Data stored in: {logger.calls_file}")
    print(f"   - CSV export: {logger.csv_file}")
    print(f"   - Ready for Stage 2: Performance tracking")
