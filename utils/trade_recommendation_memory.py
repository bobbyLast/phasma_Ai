#!/usr/bin/env python3
"""Trade Recommendation Memory - Tracks past recommendations for historical context"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class TradeRecommendationMemory:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.file_path = os.path.join(data_dir, "trade_recommendations.json")
        self._ensure_data_dir()
        self._load_memory()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_memory(self):
        """Load existing recommendations from JSON"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self.memory = json.load(f)
            except Exception:
                self.memory = {}
        else:
            self.memory = {}
    
    def _save_memory(self):
        """Save recommendations to JSON"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Error saving trade memory: {e}")
    
    def save_recommendation(self, ticker: str, verdict: str, bullets: List[str], confidence: float):
        """Save a new trade recommendation"""
        ticker = ticker.upper()
        
        # Create entry
        entry = {
            "date": datetime.now().isoformat(),
            "verdict": verdict,
            "bullets": bullets,
            "confidence": confidence
        }
        
        # Add to memory
        if ticker not in self.memory:
            self.memory[ticker] = []
        
        self.memory[ticker].append(entry)
        
        # Keep only last 5 entries per ticker
        if len(self.memory[ticker]) > 5:
            self.memory[ticker] = self.memory[ticker][-5:]
        
        # Prune old entries (older than 90 days)
        self._prune_old_entries()
        
        # Save to file
        self._save_memory()
    
    def get_past_recommendations(self, ticker: str, days_back: int = 90) -> List[Dict]:
        """Get past recommendations for a ticker"""
        ticker = ticker.upper()
        if ticker not in self.memory:
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        past_recommendations = []
        
        for entry in self.memory[ticker]:
            try:
                entry_date = datetime.fromisoformat(entry["date"])
                if entry_date >= cutoff_date:
                    past_recommendations.append(entry)
            except Exception:
                continue
        
        return past_recommendations
    
    def _prune_old_entries(self):
        """Remove entries older than 90 days"""
        cutoff_date = datetime.now() - timedelta(days=90)
        
        for ticker in list(self.memory.keys()):
            # Filter old entries
            self.memory[ticker] = [
                entry for entry in self.memory[ticker]
                if datetime.fromisoformat(entry["date"]) >= cutoff_date
            ]
            
            # Remove ticker if no entries left
            if not self.memory[ticker]:
                del self.memory[ticker]
    
    def get_time_ago_string(self, past_date_str: str) -> str:
        """Convert past date to 'X days ago' format"""
        try:
            past_date = datetime.fromisoformat(past_date_str)
            now = datetime.now()
            diff = now - past_date
            
            if diff.days == 0:
                if diff.seconds < 3600:
                    minutes = diff.seconds // 60
                    return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff.days == 1:
                return "yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks} week{'s' if weeks != 1 else ''} ago"
            elif diff.days < 365:
                months = diff.days // 30
                return f"{months} month{'s' if months != 1 else ''} ago"
            else:
                years = diff.days // 365
                return f"{years} year{'s' if years != 1 else ''} ago"
        except Exception:
            return "some time ago"

# Global instance
_trade_memory: Optional[TradeRecommendationMemory] = None

def get_trade_memory() -> TradeRecommendationMemory:
    """Get the global trade memory instance"""
    global _trade_memory
    if _trade_memory is None:
        _trade_memory = TradeRecommendationMemory()
    return _trade_memory
