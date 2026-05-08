#!/usr/bin/env python3
"""
News Impact Tracker - Learns from historical news announcements and their stock price impact
to improve future confidence predictions for similar events.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class NewsImpactTracker:
    """Tracks and learns from news announcement → stock price correlations"""
    
    def __init__(self, db_path: str = "data/news_impact.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database for tracking news impact"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_impact (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                announcement_type TEXT NOT NULL,
                strategic_driver TEXT,
                investment_amount REAL,
                investment_range TEXT,
                announcement_date TEXT NOT NULL,
                pre_announcement_price REAL,
                post_7day_price REAL,
                post_30day_price REAL,
                max_gain_7days REAL,
                max_loss_7days REAL,
                volatility_spike REAL,
                volume_spike REAL,
                impact_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS impact_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                announcement_type TEXT NOT NULL,
                strategic_driver TEXT NOT NULL,
                investment_range TEXT NOT NULL,
                avg_impact_score REAL,
                success_rate REAL,
                sample_size INTEGER,
                confidence_weight REAL,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_announcement(self, symbol: str, announcement_type: str, 
                           strategic_driver: str, investment_amount: float,
                           pre_price: float) -> int:
        """Record a new announcement for future impact tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        investment_range = self.get_investment_range(investment_amount)
        
        cursor.execute('''
            INSERT INTO news_impact 
            (symbol, announcement_type, strategic_driver, investment_amount, 
             investment_range, announcement_date, pre_announcement_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, announcement_type, strategic_driver, investment_amount,
              investment_range, datetime.now().isoformat(), pre_price))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded announcement: {symbol} {announcement_type} ${investment_amount}B")
        return record_id
    
    def update_impact(self, record_id: int, post_7day_price: float, 
                     post_30day_price: float, max_gain: float, 
                     max_loss: float, volatility_spike: float, volume_spike: float):
        """Update the impact data for a recorded announcement"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate impact score based on price movement and volatility
        price_change_7d = (post_7day_price - post_7day_price) / post_7day_price
        price_change_30d = (post_30day_price - post_30day_price) / post_30day_price
        
        # Weighted impact score (70% price movement, 30% volatility/volume confirmation)
        impact_score = abs(price_change_7d) * 0.7 + (volatility_spike + volume_spike) * 0.15
        
        cursor.execute('''
            UPDATE news_impact 
            SET post_7day_price = ?, post_30day_price = ?, 
                max_gain_7days = ?, max_loss_7days = ?,
                volatility_spike = ?, volume_spike = ?, impact_score = ?
            WHERE id = ?
        ''', (post_7day_price, post_30day_price, max_gain, max_loss,
              volatility_spike, volume_spike, impact_score, record_id))
        
        conn.commit()
        conn.close()
        
        # Update patterns based on new data
        self.update_patterns()
        logger.info(f"Updated impact for record {record_id}: {impact_score:.3f}")
    
    def get_historical_impact(self, announcement_type: str, strategic_driver: str, 
                            investment_amount: float) -> Dict[str, Any]:
        """Get historical impact data for similar announcements"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find similar historical announcements
        investment_range = self.get_investment_range(investment_amount)
        
        cursor.execute('''
            SELECT AVG(impact_score), COUNT(*), AVG(max_gain_7days), AVG(max_loss_7days)
            FROM news_impact 
            WHERE announcement_type = ? AND strategic_driver = ? 
            AND investment_range = ?
            AND impact_score IS NOT NULL
        ''', (announcement_type, strategic_driver, investment_range))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[1] > 0:  # If we have historical data
            return {
                'avg_impact_score': result[0] or 0,
                'sample_size': result[1] or 0,
                'avg_max_gain': result[2] or 0,
                'avg_max_loss': result[3] or 0,
                'confidence_weight': min(1.0, result[1] / 10)  # More samples = higher confidence
            }
        
        return {'avg_impact_score': 0.2, 'sample_size': 0, 'confidence_weight': 0.1}
    
    def get_investment_range(self, amount: float) -> str:
        """Categorize investment amount into ranges"""
        if amount >= 20:
            return "20B+"
        elif amount >= 10:
            return "10B-20B"
        elif amount >= 5:
            return "5B-10B"
        else:
            return "1B-5B"
    
    def update_patterns(self):
        """Update the impact patterns table with latest data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Group by announcement type, strategic driver, and investment range
        cursor.execute('''
            INSERT OR REPLACE INTO impact_patterns 
            (announcement_type, strategic_driver, investment_range, 
             avg_impact_score, success_rate, sample_size, confidence_weight)
            SELECT 
                announcement_type, 
                strategic_driver, 
                investment_range,
                AVG(impact_score) as avg_impact,
                COUNT(CASE WHEN impact_score > 0.1 THEN 1 END) * 1.0 / COUNT(*) as success_rate,
                COUNT(*) as sample_size,
                MIN(1.0, COUNT(*) * 1.0 / 10) as confidence_weight
            FROM news_impact 
            WHERE impact_score IS NOT NULL
            GROUP BY announcement_type, strategic_driver, investment_range
        ''')
        
        conn.commit()
        conn.close()
    
    def get_confidence_adjustment(self, announcement_type: str, strategic_driver: str, 
                                investment_amount: float) -> float:
        """Get confidence adjustment based on historical performance"""
        historical = self.get_historical_impact(announcement_type, strategic_driver, investment_amount)
        
        if historical['sample_size'] >= 3:  # Minimum sample size
            # Higher historical impact = higher confidence boost
            base_adjustment = historical['avg_impact_score']
            confidence_multiplier = historical['confidence_weight']
            
            return base_adjustment * confidence_multiplier
        
        return 0.1  # Default minimal adjustment for unknown patterns
