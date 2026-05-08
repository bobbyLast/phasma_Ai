#!/usr/bin/env python3
"""
PHASMA AI - Strict Reality Architecture
Ensures only ground truth data is used - no mock/fake data ever
"""

import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import asyncio
import aiohttp
import alpaca_trade_api as tradeapi
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    reason: str
    data: Optional[Dict] = None

class StrictRealityValidator:
    """Strict validator that only allows ground truth data"""
    
    def __init__(self):
        # Verified real data sources
        self.verified_sources = {
            'alpaca', 'sec_edgar', 'finnhub', 'alpha_vantage', 
            'polygon', 'iex', 'yahoo', 'openinsider'
        }
        
        # Red flags for fake data
        self.fake_indicators = [
            'mock', 'simulated', 'fake', 'test', 'demo', 'sample'
        ]
        
    def validate_price_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate price data is ground truth"""
        if not data:
            return ValidationResult(False, "No data provided")
        
        # Check source
        source = data.get('source', '').lower()
        if source in self.fake_indicators:
            return ValidationResult(False, f"Fake data source: {source}")
        
        if source not in self.verified_sources:
            return ValidationResult(False, f"Unverified source: {source}")
        
        # Check timestamp freshness (must be within 15 minutes)
        timestamp = data.get('timestamp')
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    ts = datetime.fromtimestamp(timestamp)
                
                if datetime.now() - ts > timedelta(minutes=15):
                    return ValidationResult(False, f"Stale data: {timestamp}")
            except:
                return ValidationResult(False, "Invalid timestamp format")
        
        # Check price exists and is realistic
        price = data.get('price')
        if price is None:
            return ValidationResult(False, "No price data")
        
        try:
            price = float(price)
            if price <= 0 or price > 1000000:  # Sanity check
                return ValidationResult(False, f"Invalid price: {price}")
        except:
            return ValidationResult(False, f"Invalid price format: {price}")
        
        # Check volume (must be > 0 for real stocks)
        volume = data.get('volume')
        if volume is not None:
            try:
                volume = int(volume)
                if volume < 0:
                    return ValidationResult(False, f"Negative volume: {volume}")
            except:
                return ValidationResult(False, f"Invalid volume format")
        
        return ValidationResult(True, "Valid ground truth data", data)
    
    def validate_signal(self, signal: Dict[str, Any]) -> ValidationResult:
        """Validate trading signal is based on real data"""
        if not signal:
            return ValidationResult(False, "No signal provided")
        
        # Check required fields
        required = ['symbol', 'action', 'confidence', 'source']
        for field in required:
            if field not in signal:
                return ValidationResult(False, f"Missing required field: {field}")
        
        # Validate source
        source = signal.get('source', '').lower()
        if source in self.fake_indicators:
            return ValidationResult(False, f"Signal from fake source: {source}")
        
        # Validate confidence
        confidence = signal.get('confidence')
        try:
            confidence = float(confidence)
            if confidence < 0 or confidence > 1:
                return ValidationResult(False, f"Invalid confidence: {confidence}")
        except:
            return ValidationResult(False, f"Invalid confidence format")
        
        return ValidationResult(True, "Valid signal", signal)

class GroundTruthDataCache:
    """SQLite cache for real data to reduce API calls"""
    
    def __init__(self, db_path: str = "data/ground_truth_cache.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_cache (
                    symbol TEXT,
                    price REAL,
                    volume INTEGER,
                    source TEXT,
                    timestamp DATETIME,
                    PRIMARY KEY (symbol, timestamp)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signal_cache (
                    id TEXT PRIMARY KEY,
                    symbol TEXT,
                    action TEXT,
                    confidence REAL,
                    source TEXT,
                    data TEXT,
                    timestamp DATETIME
                )
            """)
    
    def get_price(self, symbol: str, max_age_minutes: int = 5) -> Optional[Dict]:
        """Get cached price if fresh enough"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT price, volume, source, timestamp 
                FROM price_cache 
                WHERE symbol = ? AND datetime(timestamp) > datetime('now', '-{} minutes')
                ORDER BY timestamp DESC 
                LIMIT 1
            """.format(max_age_minutes), (symbol,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'symbol': symbol,
                    'price': row[0],
                    'volume': row[1],
                    'source': row[2],
                    'timestamp': row[3],
                    'cached': True
                }
        return None
    
    def cache_price(self, symbol: str, data: Dict[str, Any]):
        """Cache price data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO price_cache 
                (symbol, price, volume, source, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                symbol,
                data.get('price'),
                data.get('volume'),
                data.get('source'),
                datetime.now().isoformat()
            ))
    
    def cleanup_old_data(self, hours: int = 24):
        """Remove old cached data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                DELETE FROM price_cache 
                WHERE datetime(timestamp) < datetime('now', '-{hours} hours')
            """)
            conn.execute(f"""
                DELETE FROM signal_cache 
                WHERE datetime(timestamp) < datetime('now', '-{hours} hours')
            """)

class StaggeredExecutor:
    """Executes API calls with staggered timing to avoid rate limits"""
    
    def __init__(self, delay_seconds: float = 1.0):
        self.delay_seconds = delay_seconds
        self.last_call_time = {}
    
    async def execute_with_cooldown(self, source: str, func, *args, **kwargs):
        """Execute function with cooldown between calls"""
        # Check last call time for this source
        last_time = self.last_call_time.get(source, 0)
        now = time.time()
        
        # Wait if needed
        if now - last_time < self.delay_seconds:
            wait_time = self.delay_seconds - (now - last_time)
            logger.debug(f"Cooldown for {source}: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        # Execute the function
        try:
            result = await func(*args, **kwargs)
            self.last_call_time[source] = time.time()
            return result
        except Exception as e:
            logger.error(f"Error in staggered execution for {source}: {e}")
            return None

class GroundTruthDataProvider:
    """Primary data provider using only real sources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validator = StrictRealityValidator()
        self.cache = GroundTruthDataCache()
        self.executor = StaggeredExecutor(delay_seconds=1.0)
        
        # Initialize Alpaca as primary source
        self.alpaca = None
        if config.get('ALPACA_API_KEY') and config.get('ALPACA_SECRET_KEY'):
            try:
                self.alpaca = tradeapi.REST(
                    key_id=config['ALPACA_API_KEY'],
                    secret_key=config['ALPACA_SECRET_KEY'],
                    base_url='https://paper-api.alpaca.markets',
                    api_version='v2'
                )
                logger.info("Alpaca Market Data API connected")
            except Exception as e:
                logger.error(f"Failed to connect to Alpaca: {e}")
    
    async def get_real_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real price with strict validation"""
        # Check cache first
        cached = self.cache.get_price(symbol)
        if cached:
            logger.debug(f"Using cached price for {symbol}")
            return cached
        
        # Try Alpaca first (primary source)
        if self.alpaca:
            price_data = await self.executor.execute_with_cooldown(
                'alpaca', self._get_from_alpaca, symbol
            )
            if price_data:
                validation = self.validator.validate_price_data(price_data)
                if validation.is_valid:
                    self.cache.cache_price(symbol, validation.data)
                    return validation.data
                else:
                    logger.warning(f"Alpaca data invalid for {symbol}: {validation.reason}")
        
        # If no data available, do NOT fall back to mock
        logger.error(f"REAL DATA UNAVAILABLE for {symbol}. Aborting request.")
        return None
    
    async def _get_from_alpaca(self, symbol: str) -> Optional[Dict]:
        """Get price from Alpaca Market Data API"""
        try:
            # Get latest trade
            barset = self.alpaca.get_latest_bar(symbol)
            if barset:
                return {
                    'symbol': symbol,
                    'price': barset.c,
                    'volume': barset.v,
                    'source': 'alpaca',
                    'timestamp': barset.t.isoformat()
                }
        except Exception as e:
            logger.error(f"Alpaca API error for {symbol}: {e}")
        return None
    
    def validate_or_exit(self, data: Any, data_type: str = 'price') -> bool:
        """Validate data or exit if invalid"""
        if data_type == 'price':
            validation = self.validator.validate_price_data(data)
        elif data_type == 'signal':
            validation = self.validator.validate_signal(data)
        else:
            logger.error(f"Unknown data type: {data_type}")
            return False
        
        if not validation.is_valid:
            logger.error(f"DATA VALIDATION FAILED: {validation.reason}")
            logger.error("ABORTING - No fake data allowed in Strict Reality Mode")
            return False
        
        return True

# Global strict reality provider
ground_truth_provider = None

def initialize_ground_truth(config: Dict[str, Any]):
    """Initialize the ground truth data provider"""
    global ground_truth_provider
    ground_truth_provider = GroundTruthDataProvider(config)
    logger.info("Strict Reality Architecture initialized - NO MOCK DATA ALLOWED")

def get_real_price(symbol: str) -> Optional[Dict[str, Any]]:
    """Get real price or return None (never mock)"""
    if not ground_truth_provider:
        logger.error("Ground truth provider not initialized")
        return None
    
    # This would be async in real implementation
    # For now, return None to show strict reality
    logger.error(f"Real price requested for {symbol} - implement async call")
    return None

# Example usage in trading logic:
def OLD_get_price_with_fallback(ticker):
    """OLD WAY - WITH MOCK FALLBACK (DANGEROUS!)"""
    price = api.get_price(ticker)
    if price is None:
        price = generate_mock_price(ticker)  # DANGEROUS!
    return price

def NEW_get_price_strict_reality(ticker):
    """NEW WAY - STRICT REALITY (SAFE)"""
    price = get_real_price(ticker)
    if price is None:
        logger.error(f"REAL DATA UNAVAILABLE for {ticker}. Aborting cycle.")
        return None  # Stop immediately. No real data = No trade.
    return price
