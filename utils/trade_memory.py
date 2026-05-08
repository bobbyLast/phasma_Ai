"""
Trade Memory System - Prevents trading the same symbols repeatedly
"""
import json
import os
from datetime import datetime, timedelta
from typing import Set, Dict, List

class TradeMemory:
    """Tracks recently traded symbols to prevent duplicates"""
    
    def __init__(self, memory_file='trade_memory.json', cooldown_days=7):
        self.memory_file = memory_file
        self.cooldown_days = cooldown_days
        self.recent_trades = self._load_memory()
    
    def _load_memory(self) -> Dict:
        """Load trade memory from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_memory(self):
        """Save trade memory to file"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.recent_trades, f, indent=2)
    
    def is_recently_traded(self, symbol: str) -> bool:
        """Check if symbol was traded recently"""
        if symbol not in self.recent_trades:
            return False
        
        last_trade_date = datetime.fromisoformat(self.recent_trades[symbol])
        days_ago = (datetime.now() - last_trade_date).days
        
        return days_ago < self.cooldown_days
    
    def add_trade(self, symbol: str):
        """Record a new trade"""
        self.recent_trades[symbol] = datetime.now().isoformat()
        self._save_memory()
        print(f"   📝 Trade Memory: Recorded {symbol} (cooldown: {self.cooldown_days} days)")
    
    def get_days_since_trade(self, symbol: str) -> int:
        """Get days since last trade of this symbol"""
        if symbol not in self.recent_trades:
            return 999  # Never traded
        
        last_trade_date = datetime.fromisoformat(self.recent_trades[symbol])
        return (datetime.now() - last_trade_date).days
    
    def clean_old_trades(self):
        """Remove trades older than cooldown period"""
        cutoff_date = datetime.now() - timedelta(days=self.cooldown_days)
        
        symbols_to_remove = []
        for symbol, trade_date_str in self.recent_trades.items():
            trade_date = datetime.fromisoformat(trade_date_str)
            if trade_date < cutoff_date:
                symbols_to_remove.append(symbol)
        
        for symbol in symbols_to_remove:
            del self.recent_trades[symbol]
        
        if symbols_to_remove:
            self._save_memory()
            print(f"   🧹 Cleaned {len(symbols_to_remove)} old trades from memory")
    
    def get_available_symbols(self, all_symbols: List[str]) -> List[str]:
        """Filter symbols to only those not recently traded"""
        return [s for s in all_symbols if not self.is_recently_traded(s)]
    
    def get_recent_trades_summary(self) -> str:
        """Get summary of recent trades"""
        if not self.recent_trades:
            return "No recent trades"
        
        summary = []
        for symbol, trade_date_str in sorted(self.recent_trades.items()):
            days_ago = self.get_days_since_trade(symbol)
            summary.append(f"{symbol}: {days_ago}d ago")
        
        return ", ".join(summary)

# Global instance
_trade_memory = None

def get_trade_memory():
    """Get or create the global trade memory instance"""
    global _trade_memory
    if _trade_memory is None:
        _trade_memory = TradeMemory()
    return _trade_memory
