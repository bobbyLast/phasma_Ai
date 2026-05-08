#!/usr/bin/env python3
"""
Unusual Whales Engine - Tracks unusual options activity and institutional flow
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os

@dataclass
class UnusualOptionsFlow:
    """Represents unusual options activity"""
    symbol: str
    action: str  # BUY or SELL
    option_type: str  # CALL or PUT
    strike: float
    expiration: str
    volume: int
    volume_avg: int
    oi: int
    sentiment: str  # BULLISH or BEARISH
    confidence: float
    timestamp: datetime
    price: float
    
class UnusualWhalesEngine:
    """Engine for tracking unusual options activity and institutional flow"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.unusualwhales.com/v1"
        self.api_key = config.get('unusual_whales', {}).get('api_key')
        self.enabled = config.get('unusual_whales', {}).get('enabled', False)
        
        # Cache for storing recent unusual activity
        self.unusual_activity_cache = {}
        self.last_update = None
        
        # Minimum thresholds for considering activity "unusual"
        self.min_volume_multiplier = config.get('unusual_whales', {}).get('min_volume_multiplier', 3)
        self.min_confidence = config.get('unusual_whales', {}).get('min_confidence', 60)
        
        if not self.enabled:
            self.logger.info("Unusual Whales engine disabled")
            return
            
        if not self.api_key:
            self.logger.warning("Unusual Whales API key not provided")
            self.enabled = False
            return
            
        self.logger.info("Unusual Whales Engine initialized")
    
    async def get_unusual_options_flow(self, limit: int = 20) -> List[UnusualOptionsFlow]:
        """Get recent unusual options activity"""
        if not self.enabled:
            return []
            
        try:
            # Simulate API call (replace with actual API integration)
            # In production, this would make real API calls to Unusual Whales
            
            # Demo data for testing
            demo_flows = [
                {
                    'symbol': 'AAPL',
                    'action': 'BUY',
                    'option_type': 'CALL',
                    'strike': 195.0,
                    'expiration': '2024-02-16',
                    'volume': 15000,
                    'volume_avg': 2000,
                    'oi': 5000,
                    'sentiment': 'BULLISH',
                    'confidence': 85,
                    'timestamp': datetime.now(),
                    'price': 192.50
                },
                {
                    'symbol': 'TSLA',
                    'action': 'BUY',
                    'option_type': 'CALL',
                    'strike': 250.0,
                    'expiration': '2024-02-23',
                    'volume': 25000,
                    'volume_avg': 3000,
                    'oi': 8000,
                    'sentiment': 'BULLISH',
                    'confidence': 90,
                    'timestamp': datetime.now(),
                    'price': 245.30
                },
                {
                    'symbol': 'NVDA',
                    'action': 'BUY',
                    'option_type': 'CALL',
                    'strike': 800.0,
                    'expiration': '2024-02-16',
                    'volume': 18000,
                    'volume_avg': 2500,
                    'oi': 6000,
                    'sentiment': 'BULLISH',
                    'confidence': 88,
                    'timestamp': datetime.now(),
                    'price': 785.60
                },
                {
                    'symbol': 'SPY',
                    'action': 'BUY',
                    'option_type': 'PUT',
                    'strike': 470.0,
                    'expiration': '2024-02-09',
                    'volume': 30000,
                    'volume_avg': 4000,
                    'oi': 10000,
                    'sentiment': 'BEARISH',
                    'confidence': 75,
                    'timestamp': datetime.now(),
                    'price': 478.20
                },
                {
                    'symbol': 'QQQ',
                    'action': 'BUY',
                    'option_type': 'PUT',
                    'strike': 420.0,
                    'expiration': '2024-02-16',
                    'volume': 20000,
                    'volume_avg': 3500,
                    'oi': 7000,
                    'sentiment': 'BEARISH',
                    'confidence': 70,
                    'timestamp': datetime.now(),
                    'price': 425.80
                }
            ]
            
            # Filter by volume multiplier and confidence
            unusual_flows = []
            for flow_data in demo_flows:
                volume_multiplier = flow_data['volume'] / flow_data['volume_avg']
                if volume_multiplier >= self.min_volume_multiplier and flow_data['confidence'] >= self.min_confidence:
                    flow = UnusualOptionsFlow(**flow_data)
                    unusual_flows.append(flow)
            
            self.logger.info(f"Found {len(unusual_flows)} unusual options flows")
            return unusual_flows[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching unusual options flow: {e}")
            return []
    
    async def get_institutional_flow(self, limit: int = 20) -> List[Dict]:
        """Get recent institutional flow data"""
        if not self.enabled:
            return []
            
        try:
            # Simulate institutional flow data
            demo_flows = [
                {
                    'symbol': 'MSFT',
                    'type': 'BLOCK_TRADE',
                    'action': 'BUY',
                    'size': 50000000,  # $50M
                    'price': 410.50,
                    'sentiment': 'BULLISH',
                    'confidence': 82,
                    'timestamp': datetime.now()
                },
                {
                    'symbol': 'GOOGL',
                    'type': 'BLOCK_TRADE',
                    'action': 'SELL',
                    'size': 75000000,  # $75M
                    'price': 145.20,
                    'sentiment': 'BEARISH',
                    'confidence': 78,
                    'timestamp': datetime.now()
                },
                {
                    'symbol': 'AMZN',
                    'type': ' dark_pool',
                    'action': 'BUY',
                    'size': 30000000,  # $30M
                    'price': 155.80,
                    'sentiment': 'BULLISH',
                    'confidence': 75,
                    'timestamp': datetime.now()
                }
            ]
            
            self.logger.info(f"Found {len(demo_flows)} institutional flows")
            return demo_flows[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching institutional flow: {e}")
            return []
    
    def convert_to_trading_signals(self, unusual_flows: List[UnusualOptionsFlow]) -> List[Dict]:
        """Convert unusual options flow to trading signals"""
        signals = []
        
        for flow in unusual_flows:
            # Determine action based on option type and sentiment
            if flow.option_type == 'CALL' and flow.sentiment == 'BULLISH':
                action = 'BUY'
            elif flow.option_type == 'PUT' and flow.sentiment == 'BEARISH':
                action = 'SELL'
            else:
                continue  # Skip conflicting signals
            
            # Calculate confidence based on volume and sentiment strength
            volume_multiplier = flow.volume / flow.volume_avg
            confidence = min(95, flow.confidence + (volume_multiplier * 5))
            
            signal = {
                'symbol': flow.symbol,
                'action': action,
                'confidence': confidence / 100,  # Convert to decimal
                'source': 'unusual_whales',
                'rationale': f"Unusual {flow.option_type} activity: {flow.volume:,} contracts vs avg {flow.volume_avg:,} ({volume_multiplier:.1f}x normal)",
                'details': {
                    'option_type': flow.option_type,
                    'strike': flow.strike,
                    'expiration': flow.expiration,
                    'volume': flow.volume,
                    'volume_multiplier': volume_multiplier,
                    'sentiment': flow.sentiment
                },
                'timestamp': flow.timestamp.isoformat(),
                'entry_price': flow.price,
                'signal_type': 'options_flow'
            }
            
            signals.append(signal)
        
        return signals
    
    def convert_institutional_to_signals(self, institutional_flows: List[Dict]) -> List[Dict]:
        """Convert institutional flow to trading signals"""
        signals = []
        
        for flow in institutional_flows:
            # Only consider large block trades ($10M+)
            if flow['size'] < 10000000:
                continue
            
            signal = {
                'symbol': flow['symbol'],
                'action': flow['action'],
                'confidence': flow['confidence'] / 100,
                'source': 'unusual_whales',
                'rationale': f"Institutional {flow['type']}: ${flow['size']:,} at ${flow['price']:.2f}",
                'details': {
                    'flow_type': flow['type'],
                    'size': flow['size'],
                    'sentiment': flow['sentiment']
                },
                'timestamp': flow['timestamp'].isoformat(),
                'entry_price': flow['price'],
                'signal_type': 'institutional_flow'
            }
            
            signals.append(signal)
        
        return signals
    
    async def get_signals(self) -> List[Dict]:
        """Get all trading signals from unusual activity"""
        all_signals = []
        
        # Get unusual options flow
        unusual_flows = await self.get_unusual_options_flow()
        options_signals = self.convert_to_trading_signals(unusual_flows)
        all_signals.extend(options_signals)
        
        # Get institutional flow
        institutional_flows = await self.get_institutional_flow()
        institutional_signals = self.convert_institutional_to_signals(institutional_flows)
        all_signals.extend(institutional_signals)
        
        # Sort by confidence
        all_signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        self.logger.info(f"Generated {len(all_signals)} signals from unusual activity")
        return all_signals
    
    def analyze_flow_sentiment(self, symbol: str, days_back: int = 5) -> Dict:
        """Analyze recent flow sentiment for a specific symbol"""
        # This would analyze historical flow data
        # For now, return a simple sentiment analysis
        return {
            'symbol': symbol,
            'overall_sentiment': 'NEUTRAL',
            'bullish_count': 0,
            'bearish_count': 0,
            'total_volume': 0,
            'confidence': 50
        }

# Factory function for easy integration
def get_unusual_whales_engine(config: Dict) -> UnusualWhalesEngine:
    """Get initialized Unusual Whales engine"""
    return UnusualWhalesEngine(config)
