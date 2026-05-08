#!/usr/bin/env python3
"""
PHASMA AI - Strict Data Validation Layer
Prevents trading on fake, mock, or invalid data
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class StrictDataValidator:
    """Strict validation layer to ensure only real data is used"""
    
    def __init__(self):
        # Known fake/mock data sources
        self.fake_sources = {
            'mock', 'simulated', 'test', 'demo', 'fake'
        }
        
        # Known fake data patterns
        self.fake_patterns = [
            r'^\$?[0-9]+\.[0-9]{2}$',  # Always exactly 2 decimal places
            r'^[A-Z]{3}_USD$',          # Crypto pattern
            r'^TEST_',
            r'^DEMO_'
        ]
        
        # Minimum price thresholds for common stocks
        self.min_price_thresholds = {
            'stock': 0.01,      # $0.01 minimum
            'etf': 0.01,        # $0.01 minimum
            'crypto': 0.000001, # Much lower for crypto
            'default': 0.01
        }
        
        # Maximum price thresholds (prevent obvious fakes)
        self.max_price_thresholds = {
            'stock': 100000,     # No stock over $100k
            'etf': 100000,       # No ETF over $100k
            'crypto': 1000000,   # Crypto can be higher
            'default': 100000
        }
        
        # Valid symbol patterns
        self.symbol_patterns = {
            'stock': r'^[A-Z]{1,5}$',                    # 1-5 letters
            'etf': r'^[A-Z]{1,5}$',                      # Same as stocks
            'crypto': r'^[A-Z]+-USD$',                   # BTC-USD format
            'option': r'^[A-Z]{1,5}\d{6}[CP]\d{8}$'     # Complex option format
        }
        
    def validate_price_data(self, data: Dict[str, Any]) -> bool:
        """Validate price data is real and not fake"""
        if not data:
            logger.warning("Empty price data received")
            return False
        
        # Check source
        source = data.get('source', '').lower()
        if source in self.fake_sources:
            logger.warning(f"Fake data source detected: {source}")
            return False
        
        # Check price exists and is valid
        price = data.get('price')
        if price is None:
            logger.warning("No price in data")
            return False
        
        try:
            price = float(price)
        except (ValueError, TypeError):
            logger.warning(f"Invalid price format: {price}")
            return False
        
        # Check price thresholds
        asset_type = self._determine_asset_type(data)
        min_price = self.min_price_thresholds.get(asset_type, self.min_price_thresholds['default'])
        max_price = self.max_price_thresholds.get(asset_type, self.max_price_thresholds['default'])
        
        if price < min_price or price > max_price:
            logger.warning(f"Price ${price:.2f} outside valid range [{min_price}, {max_price}] for {asset_type}")
            return False
        
        # Check for obvious fake patterns
        symbol = data.get('symbol', '')
        if self._is_fake_symbol(symbol):
            logger.warning(f"Fake symbol pattern detected: {symbol}")
            return False
        
        # Check volume if present
        volume = data.get('volume')
        if volume is not None:
            try:
                volume = int(volume)
                if volume < 0:
                    logger.warning(f"Negative volume: {volume}")
                    return False
                # Most stocks have volume > 0
                if asset_type in ['stock', 'etf'] and volume == 0:
                    logger.warning(f"Zero volume for {asset_type}: {symbol}")
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Invalid volume format: {volume}")
                return False
        
        # Check timestamp
        timestamp = data.get('timestamp')
        if timestamp:
            if not self._is_recent_timestamp(timestamp):
                logger.warning(f"Stale data timestamp: {timestamp}")
                return False
        
        return True
    
    def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate trading signal is real"""
        if not signal:
            return False
        
        # Check required fields
        required_fields = ['symbol', 'action', 'confidence', 'source']
        for field in required_fields:
            if field not in signal:
                logger.warning(f"Signal missing required field: {field}")
                return False
        
        # Validate symbol
        symbol = signal.get('symbol', '')
        if not symbol or self._is_fake_symbol(symbol):
            logger.warning(f"Invalid symbol in signal: {symbol}")
            return False
        
        # Validate action
        action = signal.get('action', '').upper()
        if action not in ['BUY', 'SELL', 'HOLD']:
            logger.warning(f"Invalid action in signal: {action}")
            return False
        
        # Validate confidence
        confidence = signal.get('confidence')
        try:
            confidence = float(confidence)
            if confidence < 0 or confidence > 1:
                logger.warning(f"Confidence out of range: {confidence}")
                return False
        except (ValueError, TypeError):
            logger.warning(f"Invalid confidence format: {confidence}")
            return False
        
        # Check source
        source = signal.get('source', '').lower()
        if source in self.fake_sources:
            logger.warning(f"Signal from fake source: {source}")
            return False
        
        # Validate price if present
        if 'price' in signal or 'current_price' in signal:
            price_data = {
                'symbol': symbol,
                'price': signal.get('price') or signal.get('current_price'),
                'source': source
            }
            if not self.validate_price_data(price_data):
                return False
        
        return True
    
    def validate_news_item(self, news: Dict[str, Any]) -> bool:
        """Validate news item is real"""
        if not news:
            return False
        
        # Check source
        source = news.get('source', '').lower()
        if source in self.fake_sources:
            return False
        
        # Check title
        title = news.get('title', '')
        if not title or len(title) < 10:
            return False
        
        # Check for test patterns
        if any(pattern in title.lower() for pattern in ['test', 'demo', 'mock']):
            return False
        
        return True
    
    def _determine_asset_type(self, data: Dict[str, Any]) -> str:
        """Determine asset type from data"""
        symbol = data.get('symbol', '').upper()
        
        if '-USD' in symbol:
            return 'crypto'
        elif re.match(self.symbol_patterns['option'], symbol):
            return 'option'
        elif symbol in ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO']:
            return 'etf'
        else:
            return 'stock'
    
    def _is_fake_symbol(self, symbol: str) -> bool:
        """Check if symbol matches fake patterns"""
        if not symbol:
            return True
        
        symbol = symbol.upper()
        
        # Check against fake patterns
        for pattern in self.fake_patterns:
            if re.match(pattern, symbol):
                return True
        
        # Check for obvious test symbols
        test_symbols = ['TEST', 'DEMO', 'FAKE', 'MOCK', 'SAMPLE']
        if any(test in symbol for test in test_symbols):
            return True
        
        return False
    
    def _is_recent_timestamp(self, timestamp: Any) -> bool:
        """Check if timestamp is recent (within last hour)"""
        try:
            if isinstance(timestamp, str):
                # Try parsing ISO format
                ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, (int, float)):
                # Unix timestamp
                ts = datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, datetime):
                ts = timestamp
            else:
                return False
            
            # Check if within last hour
            return datetime.now() - ts < timedelta(hours=1)
        except Exception:
            return False
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation rules"""
        return {
            'fake_sources': list(self.fake_sources),
            'price_thresholds': {
                'min': self.min_price_thresholds,
                'max': self.max_price_thresholds
            },
            'symbol_patterns': self.symbol_patterns,
            'validation_time': datetime.now().isoformat()
        }

# Global validator instance
validator = StrictDataValidator()

def validate_data_or_skip(data: Any, data_type: str = 'price') -> bool:
    """Convenience function to validate data or skip trading"""
    if data_type == 'price':
        if not validator.validate_price_data(data):
            logger.warning("No real price data available. Skipping trade cycle.")
            return False
    elif data_type == 'signal':
        if not validator.validate_signal(data):
            logger.warning("Invalid signal received. Skipping trade.")
            return False
    elif data_type == 'news':
        if not validator.validate_news_item(data):
            logger.warning("Fake news detected. Skipping.")
            return False
    
    return True

def is_mock_data(data: Dict[str, Any]) -> bool:
    """Quick check if data is from mock source"""
    source = data.get('source', '').lower()
    return source in validator.fake_sources
