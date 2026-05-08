"""Enhanced Options Flow Detector with Multiple Data Sources"""

import asyncio
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
from dataclasses import dataclass

from utils.multi_source_data_provider import get_multi_source_provider, PriceData

@dataclass
class OptionsFlowSignal:
    symbol: str
    option_type: str  # 'call' or 'put'
    strike: float
    expiration: str
    volume: int
    open_interest: int
    volume_oi_ratio: float
    implied_volatility: float
    unusual_score: float
    sentiment: str  # 'bullish' or 'bearish'
    source: str
    timestamp: datetime

class EnhancedOptionsFlowDetector:
    """Detects unusual options flow using multiple data sources"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Multi-source data provider
        self.data_provider = get_multi_source_provider(self.config)
        
        # Thresholds for unusual activity
        self.min_volume = self.config.get('options_flow', {}).get('min_volume', 100)
        self.min_oi = self.config.get('options_flow', {}).get('min_open_interest', 100)
        self.volume_oi_threshold = self.config.get('options_flow', {}).get('volume_oi_threshold', 0.5)
        self.iv_spike_threshold = self.config.get('options_flow', {}).get('iv_spike_threshold', 0.3)
        
        # Watchlist for focused scanning
        self.watchlist = self.config.get('options_watchlist', [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'SPY', 'QQQ',
            'AMD', 'NFLX', 'BABA', 'UBER', 'LYFT', 'SNAP', 'ROKU', 'ZM', 'PLTR', 'GME'
        ])
        
        # Cache for IV history
        self.iv_history = {}
        
    async def scan_unusual_flow(self, symbols: List[str] = None) -> List[OptionsFlowSignal]:
        """Scan for unusual options flow activity"""
        symbols = symbols or self.watchlist
        signals = []
        
        async with self.data_provider:
            tasks = [self._scan_symbol(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    signals.extend(result)
                elif isinstance(result, Exception):
                    self.logger.warning(f"Error scanning symbol: {result}")
        
        # Sort by unusual score
        signals.sort(key=lambda x: x.unusual_score, reverse=True)
        
        return signals[:20]  # Return top 20 signals
    
    async def _scan_symbol(self, symbol: str) -> List[OptionsFlowSignal]:
        """Scan a single symbol for unusual options activity"""
        signals = []
        
        try:
            # Get options chain
            options_data = await self.data_provider.get_options_chain(symbol)
            if not options_data:
                return signals
            
            # Get current price for context
            price_data = await self.data_provider.get_price_data(symbol)
            current_price = price_data.price if price_data else 0
            
            # Scan calls
            for option in options_data.get('calls', []):
                signal = self._analyze_option(symbol, 'call', option, current_price)
                if signal and signal.unusual_score > 0.5:
                    signals.append(signal)
            
            # Scan puts
            for option in options_data.get('puts', []):
                signal = self._analyze_option(symbol, 'put', option, current_price)
                if signal and signal.unusual_score > 0.5:
                    signals.append(signal)
                    
        except Exception as e:
            self.logger.warning(f"Error scanning {symbol}: {e}")
        
        return signals
    
    def _analyze_option(self, symbol: str, option_type: str, option: Dict, current_price: float) -> Optional[OptionsFlowSignal]:
        """Analyze a single option for unusual activity"""
        
        volume = option.get('volume', 0)
        oi = option.get('oi', 0)
        iv = option.get('iv', 0)
        strike = option.get('strike', 0)
        
        # Skip if below minimum thresholds
        if volume < self.min_volume or oi < self.min_oi:
            return None
        
        # Calculate volume/OI ratio
        volume_oi_ratio = volume / max(oi, 1)
        
        # Check for unusual volume
        volume_score = min(volume_oi_ratio / 2.0, 1.0)  # Normalize to 0-1
        
        # Check IV spike
        iv_score = self._calculate_iv_score(symbol, strike, option_type, iv)
        
        # Check strike proximity (ATM options are more significant)
        proximity_score = self._calculate_proximity_score(strike, current_price)
        
        # Calculate overall unusual score
        unusual_score = (volume_score * 0.5 + iv_score * 0.3 + proximity_score * 0.2)
        
        # Determine sentiment
        if option_type == 'call':
            sentiment = 'bullish' if strike > current_price else 'very bullish'
        else:
            sentiment = 'bearish' if strike < current_price else 'very bearish'
        
        return OptionsFlowSignal(
            symbol=symbol,
            option_type=option_type,
            strike=strike,
            expiration=option.get('expiration', ''),
            volume=volume,
            open_interest=oi,
            volume_oi_ratio=volume_oi_ratio,
            implied_volatility=iv,
            unusual_score=unusual_score,
            sentiment=sentiment,
            source=option.get('source', 'unknown'),
            timestamp=datetime.now()
        )
    
    def _calculate_iv_score(self, symbol: str, strike: float, option_type: str, current_iv: float) -> float:
        """Calculate IV spike score"""
        
        # Get IV history for this symbol
        key = f"{symbol}_{strike}_{option_type}"
        history = self.iv_history.get(key, [])
        
        # Add current IV to history
        history.append({
            'iv': current_iv,
            'timestamp': datetime.now()
        })
        
        # Keep only last 30 days
        cutoff = datetime.now() - timedelta(days=30)
        history = [h for h in history if h['timestamp'] > cutoff]
        self.iv_history[key] = history
        
        if len(history) < 5:
            return 0.5  # Neutral score if not enough history
        
        # Calculate average IV over last 30 days
        avg_iv = sum(h['iv'] for h in history[:-1]) / (len(history) - 1)
        
        # Calculate IV spike
        if avg_iv > 0:
            iv_spike = (current_iv - avg_iv) / avg_iv
            return min(max(iv_spike / self.iv_spike_threshold, 0), 1.0)
        
        return 0.5
    
    def _calculate_proximity_score(self, strike: float, current_price: float) -> float:
        """Calculate how close the strike is to current price"""
        
        if current_price <= 0:
            return 0.5
        
        # Calculate percentage away from current price
        pct_away = abs(strike - current_price) / current_price
        
        # Higher score for closer strikes
        if pct_away < 0.05:  # Within 5%
            return 1.0
        elif pct_away < 0.10:  # Within 10%
            return 0.8
        elif pct_away < 0.20:  # Within 20%
            return 0.6
        elif pct_away < 0.30:  # Within 30%
            return 0.4
        else:
            return 0.2
    
    async def get_top_movers(self, min_score: float = 0.7) -> List[OptionsFlowSignal]:
        """Get top movers based on unusual activity score"""
        
        signals = await self.scan_unusual_flow()
        
        # Filter by minimum score
        top_movers = [s for s in signals if s.unusual_score >= min_score]
        
        return top_movers[:10]  # Return top 10
    
    def generate_report(self, signals: List[OptionsFlowSignal]) -> str:
        """Generate a human-readable report of options flow"""
        
        if not signals:
            return "No unusual options flow detected"
        
        report = "📊 UNUSUAL OPTIONS FLOW REPORT\n"
        report += "=" * 50 + "\n\n"
        
        for i, signal in enumerate(signals[:10], 1):
            report += f"{i}. {signal.symbol} {signal.option_type.upper()}\n"
            report += f"   Strike: ${signal.strike:.2f} | Exp: {signal.expiration}\n"
            report += f"   Volume: {signal.volume:,} | OI: {signal.open_interest:,}\n"
            report += f"   Vol/OI: {signal.volume_oi_ratio:.2f}x | IV: {signal.implied_volatility:.1%}\n"
            report += f"   Score: {signal.unusual_score:.1%} | Sentiment: {signal.sentiment}\n"
            report += f"   Source: {signal.source}\n\n"
        
        return report


# Factory function
def get_enhanced_options_detector(config: Dict = None) -> EnhancedOptionsFlowDetector:
    """Get enhanced options flow detector instance"""
    return EnhancedOptionsFlowDetector(config)
