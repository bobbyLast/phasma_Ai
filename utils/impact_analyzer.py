"""
Impact Analyzer - Measures current market impact and awareness of catalysts
Determines if news is already priced in and calculates remaining potential
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

class ImpactAnalyzer:
    """Analyzes current market impact to determine if catalyst is priced in"""
    
    def __init__(self):
        self.social_media_sources = ['reddit', 'twitter', 'stocktwits']
        self.news_sources = ['yahoo', 'reuters', 'bloomberg', 'cnbc']
    
    def analyze_impact(self, symbol: str, catalyst_date: datetime = None, 
                      current_price: float = None) -> Dict:
        """
        Analyze the current impact and awareness of a catalyst
        
        Returns:
            {
                'awareness_level': 'LOW' | 'MEDIUM' | 'HIGH',
                'pricing_in_pct': 0.30,  # 30% of potential move already priced in
                'remaining_potential': 0.70,  # 70% of potential move remains
                'volume_spike': 5.2,  # 5.2x normal volume
                'price_runup': 0.15,  # Already moved 15% before signal
                'social_mentions': 1250,  # Social media mentions in last 24h
                'news_coverage': 8,  # Number of news articles
                'impact_score': 0.65,  # Overall impact score (0-1)
                'recommendation': 'PROCEED' | 'CAUTION' | 'SKIP'
            }
        """
        
        if catalyst_date is None:
            catalyst_date = datetime.now()
        
        # Get price and volume data
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="30d", interval="1d")
        
        if len(hist) < 10:
            return self._default_analysis()
        
        # Analyze price run-up
        price_analysis = self._analyze_price_runup(hist, catalyst_date, current_price)
        
        # Analyze volume spike
        volume_analysis = self._analyze_volume_spike(hist, catalyst_date)
        
        # Estimate social media impact (simulated based on volume/price movement)
        social_analysis = self._estimate_social_impact(price_analysis, volume_analysis)
        
        # Calculate overall impact
        impact_score = self._calculate_impact_score(
            price_analysis, volume_analysis, social_analysis
        )
        
        # Determine if catalyst is priced in
        pricing_in_pct = min(0.90, impact_score * 0.8)  # Max 90% priced in
        remaining_potential = 1.0 - pricing_in_pct
        
        # Generate recommendation
        if remaining_potential > 0.5:
            recommendation = 'PROCEED'
        elif remaining_potential > 0.2:
            recommendation = 'CAUTION'
        else:
            recommendation = 'SKIP'
        
        return {
            'awareness_level': self._get_awareness_level(impact_score),
            'pricing_in_pct': round(pricing_in_pct, 3),
            'remaining_potential': round(remaining_potential, 3),
            'volume_spike': volume_analysis['spike_multiplier'],
            'price_runup': price_analysis['runup_pct'],
            'social_mentions': social_analysis['estimated_mentions'],
            'news_coverage': social_analysis['news_count'],
            'impact_score': round(impact_score, 3),
            'recommendation': recommendation,
            'analysis_details': {
                'price': price_analysis,
                'volume': volume_analysis,
                'social': social_analysis
            }
        }
    
    def _analyze_price_runup(self, hist: pd.DataFrame, catalyst_date: datetime, 
                           current_price: float = None) -> Dict:
        """Analyze how much the stock has already moved before the signal"""
        
        # Find the lowest price in the last 10 days
        recent_low = hist['Low'].rolling(10).min().iloc[-1]
        
        # Get current price
        if current_price is None:
            current_price = hist['Close'].iloc[-1]
        
        # Calculate run-up percentage
        runup_pct = (current_price - recent_low) / recent_low
        
        # Analyze the pattern of the run-up
        runup_days = self._count_runup_days(hist, recent_low, current_price)
        
        # Check if run-up was gradual or sudden
        volatility = hist['Close'].pct_change().rolling(5).std().iloc[-1]
        
        return {
            'runup_pct': round(runup_pct, 3),
            'runup_days': runup_days,
            'recent_low': round(recent_low, 2),
            'volatility': round(volatility, 4),
            'pattern': 'gradual' if volatility < 0.03 else 'sudden'
        }
    
    def _analyze_volume_spike(self, hist: pd.DataFrame, catalyst_date: datetime) -> Dict:
        """Analyze unusual volume activity"""
        
        # Get average volume over last 30 days (excluding recent spike)
        avg_volume = hist['Volume'].iloc[:-5].mean()
        
        # Get recent volume (last 3 days average)
        recent_volume = hist['Volume'].iloc[-3:].mean()
        
        # Calculate spike multiplier
        spike_multiplier = recent_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Check for sustained high volume
        sustained_days = sum(1 for vol in hist['Volume'].iloc[-5:] if vol > avg_volume * 2)
        
        return {
            'spike_multiplier': round(spike_multiplier, 2),
            'avg_volume': int(avg_volume),
            'recent_volume': int(recent_volume),
            'sustained_days': sustained_days,
            'is_unusual': spike_multiplier > 3.0
        }
    
    def _estimate_social_impact(self, price_analysis: Dict, volume_analysis: Dict) -> Dict:
        """Estimate social media impact based on price and volume data"""
        
        # Base mentions on volume spike
        base_mentions = volume_analysis['spike_multiplier'] * 100
        
        # Adjust for price movement
        price_multiplier = 1 + (price_analysis['runup_pct'] * 5)
        
        # Estimate total mentions
        estimated_mentions = int(base_mentions * price_multiplier)
        
        # Estimate news coverage based on impact
        news_count = min(20, int(volume_analysis['spike_multiplier'] * 2))
        
        return {
            'estimated_mentions': estimated_mentions,
            'news_count': news_count,
            'viral_potential': volume_analysis['spike_multiplier'] > 5.0,
            'sentiment': 'positive' if price_analysis['runup_pct'] > 0.05 else 'neutral'
        }
    
    def _calculate_impact_score(self, price_analysis: Dict, volume_analysis: Dict, 
                               social_analysis: Dict) -> float:
        """Calculate overall impact score (0-1)"""
        
        # Price impact (40% weight)
        price_score = min(1.0, price_analysis['runup_pct'] * 4)  # 25% run-up = 1.0
        
        # Volume impact (40% weight)
        volume_score = min(1.0, volume_analysis['spike_multiplier'] / 5)  # 5x volume = 1.0
        
        # Social impact (20% weight)
        social_score = min(1.0, social_analysis['estimated_mentions'] / 1000)  # 1000 mentions = 1.0
        
        # Weighted average
        impact_score = (price_score * 0.4 + volume_score * 0.4 + social_score * 0.2)
        
        return impact_score
    
    def _get_awareness_level(self, impact_score: float) -> str:
        """Convert impact score to awareness level"""
        if impact_score > 0.7:
            return 'HIGH'
        elif impact_score > 0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _count_runup_days(self, hist: pd.DataFrame, low_price: float, 
                         current_price: float) -> int:
        """Count how many days the run-up took"""
        
        # Find when the stock was near the low
        near_low_days = hist['Close'] <= low_price * 1.02
        
        if not near_low_days.any():
            return 0
        
        # Count days from low to current
        start_idx = near_low_days[::-1].idxmax()
        days = len(hist) - hist.index.get_loc(start_idx)
        
        return days
    
    def _default_analysis(self) -> Dict:
        """Return default analysis when insufficient data"""
        return {
            'awareness_level': 'MEDIUM',
            'pricing_in_pct': 0.5,
            'remaining_potential': 0.5,
            'volume_spike': 1.0,
            'price_runup': 0.0,
            'social_mentions': 100,
            'news_coverage': 2,
            'impact_score': 0.5,
            'recommendation': 'CAUTION'
        }

# Global instance
_impact_analyzer = None

def get_impact_analyzer() -> ImpactAnalyzer:
    """Get the global impact analyzer instance"""
    global _impact_analyzer
    if _impact_analyzer is None:
        _impact_analyzer = ImpactAnalyzer()
    return _impact_analyzer
