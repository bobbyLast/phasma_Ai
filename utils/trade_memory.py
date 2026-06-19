"""
Trade Memory System - Prevents trading the same symbols repeatedly
"""
import json
import os
from datetime import datetime, timedelta
from typing import Set, Dict, List

class TradeMemory:
    """Tracks recently traded symbols to prevent duplicates"""
    
    def __init__(self, memory_file=None, cooldown_days=7):
        if memory_file is None:
            from core.runtime_paths import runtime_path
            memory_file = runtime_path("trade_memory.json")
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
    
    def _last_trade_iso(self, symbol: str) -> str:
        raw = self.recent_trades.get(symbol)
        if raw is None:
            return ""
        if isinstance(raw, dict):
            return str(raw.get("last_trade") or "")
        return str(raw)

    def is_recently_traded(self, symbol: str) -> bool:
        """Check if symbol was traded recently"""
        last_iso = self._last_trade_iso(symbol)
        if not last_iso:
            return False
        try:
            last_trade_date = datetime.fromisoformat(last_iso)
        except (TypeError, ValueError):
            return False
        days_ago = (datetime.now() - last_trade_date).days
        return days_ago < self.cooldown_days
    
    def add_trade(self, symbol: str, metadata: dict = None):
        """Record a new trade (called on fills)."""
        entry = {
            "last_trade": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.recent_trades[symbol] = entry
        self._save_memory()
        print(f"   Trade Memory: Recorded {symbol} (cooldown: {self.cooldown_days} days)")

    def record_event(self, symbol: str, event: str, metadata: dict = None):
        """Record submit/reject/skip events for debugging."""
        key = f"_events_{symbol}"
        events = self.recent_trades.get(key, [])
        if not isinstance(events, list):
            events = []
        events.append({
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        })
        self.recent_trades[key] = events[-20:]
        self._save_memory()
    
    def get_days_since_trade(self, symbol: str) -> int:
        """Get days since last trade of this symbol"""
        last_iso = self._last_trade_iso(symbol)
        if not last_iso:
            return 999
        try:
            last_trade_date = datetime.fromisoformat(last_iso)
        except (TypeError, ValueError):
            return 999
        return (datetime.now() - last_trade_date).days
    
    def clean_old_trades(self):
        """Remove trades older than cooldown period"""
        cutoff_date = datetime.now() - timedelta(days=self.cooldown_days)
        
        symbols_to_remove = []
        for symbol, trade_date_str in self.recent_trades.items():
            if symbol.startswith("_events_"):
                continue
            iso = self._last_trade_iso(symbol) if isinstance(trade_date_str, dict) else str(trade_date_str)
            if not iso:
                continue
            try:
                trade_date = datetime.fromisoformat(iso)
            except (TypeError, ValueError):
                continue
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
        for symbol in sorted(self.recent_trades.keys()):
            if symbol.startswith("_events_"):
                continue
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
