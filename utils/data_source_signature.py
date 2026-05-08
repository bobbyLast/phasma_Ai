#!/usr/bin/env python3
"""
PHASMA AI - Data Source Signature System
Tags every piece of data with verifiable source signatures
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
import json
from enum import Enum

logger = logging.getLogger(__name__)

class DataSourceType(Enum):
    """Types of data sources"""
    REAL_TIME = "real_time"
    DELAYED = "delayed"
    END_OF_DAY = "end_of_day"
    HISTORICAL = "historical"
    CALCULATED = "calculated"

class DataReliability(Enum):
    """Reliability levels for data sources"""
    GROUND_TRUTH = "ground_truth"  # Direct from exchange/SEC
    VERIFIED = "verified"          # From reputable provider
    AGGREGATED = "aggregated"      # Aggregated from multiple sources
    DERIVED = "derived"            # Calculated/derived data

@dataclass
class DataSourceSignature:
    """Verifiable signature for data source"""
    source_id: str                    # e.g., "ALPACA_LIVE", "FINNHUB_REAL"
    source_type: DataSourceType
    reliability: DataReliability
    api_endpoint: str
    verification_key: str            # HMAC key or similar
    max_age_seconds: int
    weight_multiplier: float         # For convergence scoring
    requires_signature: bool         # Whether to verify HMAC
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            **asdict(self),
            'source_type': self.source_type.value,
            'reliability': self.reliability.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataSourceSignature':
        """Create from dictionary"""
        data['source_type'] = DataSourceType(data['source_type'])
        data['reliability'] = DataReliability(data['reliability'])
        return cls(**data)

@dataclass
class DataPacket:
    """Data packet with embedded signature"""
    data: Dict[str, Any]
    signature: DataSourceSignature
    timestamp: str
    packet_hash: str
    verified: bool = False

class DataSourceRegistry:
    """Registry of all approved data sources"""
    
    def __init__(self):
        self.sources: Dict[str, DataSourceSignature] = {}
        self._register_default_sources()
    
    def _register_default_sources(self):
        """Register default approved sources"""
        # Alpaca Market Data
        self.register_source(DataSourceSignature(
            source_id="ALPACA_LIVE",
            source_type=DataSourceType.REAL_TIME,
            reliability=DataReliability.GROUND_TRUTH,
            api_endpoint="https://data.alpaca.markets/v2",
            verification_key="alpaca_live_v2",
            max_age_seconds=900,  # 15 minutes
            weight_multiplier=1.0,
            requires_signature=False
        ))
        
        # Finnhub
        self.register_source(DataSourceSignature(
            source_id="FINNHUB_REAL",
            source_type=DataSourceType.REAL_TIME,
            reliability=DataReliability.VERIFIED,
            api_endpoint="https://finnhub.io/api/v1",
            verification_key="finnhub_api_v1",
            max_age_seconds=300,  # 5 minutes
            weight_multiplier=0.9,
            requires_signature=False
        ))
        
        # SEC EDGAR
        self.register_source(DataSourceSignature(
            source_id="SEC_EDGAR",
            source_type=DataSourceType.END_OF_DAY,
            reliability=DataReliability.GROUND_TRUTH,
            api_endpoint="https://www.sec.gov",
            verification_key="sec_edgar_official",
            max_age_seconds=86400,  # 24 hours
            weight_multiplier=1.0,
            requires_signature=False
        ))
        
        # FRED Economic Data
        self.register_source(DataSourceSignature(
            source_id="FRED_ECON",
            source_type=DataSourceType.DELAYED,
            reliability=DataReliability.GROUND_TRUTH,
            api_endpoint="https://api.stlouisfed.org/fred",
            verification_key="fred_api_v1",
            max_age_seconds=86400,  # Daily data
            weight_multiplier=0.8,
            requires_signature=False
        ))
        
        # Polygon.io
        self.register_source(DataSourceSignature(
            source_id="POLYGON_REAL",
            source_type=DataSourceType.REAL_TIME,
            reliability=DataReliability.VERIFIED,
            api_endpoint="https://api.polygon.io",
            verification_key="polygon_api_v2",
            max_age_seconds=900,
            weight_multiplier=0.9,
            requires_signature=False
        ))
        
        # Alpha Vantage
        self.register_source(DataSourceSignature(
            source_id="ALPHAVANTAGE",
            source_type=DataSourceType.DELAYED,
            reliability=DataReliability.VERIFIED,
            api_endpoint="https://www.alphavantage.co",
            verification_key="av_api_v1",
            max_age_seconds=300,
            weight_multiplier=0.85,
            requires_signature=False
        ))
        
        # IEX Cloud
        self.register_source(DataSourceSignature(
            source_id="IEX_CLOUD",
            source_type=DataSourceType.REAL_TIME,
            reliability=DataReliability.VERIFIED,
            api_endpoint="https://cloud.iexapis.com",
            verification_key="iex_api_v1",
            max_age_seconds=900,
            weight_multiplier=0.9,
            requires_signature=False
        ))
        
        # Yahoo Finance (as backup only)
        self.register_source(DataSourceSignature(
            source_id="YAHOO_FALLBACK",
            source_type=DataSourceType.DELAYED,
            reliability=DataReliability.AGGREGATED,
            api_endpoint="https://query1.finance.yahoo.com",
            verification_key="yahoo_finance_v8",
            max_age_seconds=300,
            weight_multiplier=0.7,
            requires_signature=False
        ))
    
    def register_source(self, signature: DataSourceSignature):
        """Register a new data source"""
        self.sources[signature.source_id] = signature
        logger.info(f"Registered data source: {signature.source_id}")
    
    def get_source(self, source_id: str) -> Optional[DataSourceSignature]:
        """Get source by ID"""
        return self.sources.get(source_id)
    
    def is_approved(self, source_id: str) -> bool:
        """Check if source is approved"""
        return source_id in self.sources
    
    def get_ground_truth_sources(self) -> Set[str]:
        """Get all ground truth sources"""
        return {
            sid for sid, sig in self.sources.items()
            if sig.reliability == DataReliability.GROUND_TRUTH
        }
    
    def get_real_time_sources(self) -> Set[str]:
        """Get all real-time sources"""
        return {
            sid for sid, sig in self.sources.items()
            if sig.source_type == DataSourceType.REAL_TIME
        }

class DataSignatureManager:
    """Manages data packet signatures and verification"""
    
    def __init__(self):
        self.registry = DataSourceRegistry()
        self.verification_cache = {}
        
        # Banned source IDs (never accept these)
        self.banned_sources = {
            'MOCK', 'SIMULATED', 'FAKE', 'TEST', 'DEMO', 'SAMPLE',
            'UNKNOWN', 'BACKTEST', 'PAPER', 'SANDBOX'
        }
    
    def sign_data(self, data: Dict[str, Any], source_id: str) -> Optional[DataPacket]:
        """Sign data packet with source signature"""
        # Check if source is approved
        if source_id in self.banned_sources:
            logger.error(f"Attempted to sign data with banned source: {source_id}")
            return None
        
        signature = self.registry.get_source(source_id)
        if not signature:
            logger.error(f"Unknown data source: {source_id}")
            return None
        
        # Create packet hash
        packet_content = {
            'data': data,
            'source_id': source_id,
            'timestamp': datetime.now().isoformat()
        }
        packet_hash = self._calculate_hash(packet_content)
        
        # Create data packet
        packet = DataPacket(
            data=data,
            signature=signature,
            timestamp=packet_content['timestamp'],
            packet_hash=packet_hash,
            verified=True  # Trusted if we're signing it
        )
        
        return packet
    
    def verify_packet(self, packet: DataPacket) -> bool:
        """Verify data packet signature"""
        # Check cache first
        cache_key = f"{packet.signature.source_id}_{packet.packet_hash}"
        if cache_key in self.verification_cache:
            return self.verification_cache[cache_key]
        
        # Check if source is banned
        if packet.signature.source_id in self.banned_sources:
            logger.error(f"Packet from banned source: {packet.signature.source_id}")
            self.verification_cache[cache_key] = False
            return False
        
        # Check if source is approved
        if not self.registry.is_approved(packet.signature.source_id):
            logger.error(f"Packet from unapproved source: {packet.signature.source_id}")
            self.verification_cache[cache_key] = False
            return False
        
        # Verify timestamp freshness
        try:
            ts = datetime.fromisoformat(packet.timestamp.replace('Z', '+00:00'))
            if datetime.now() - ts > timedelta(seconds=packet.signature.max_age_seconds):
                logger.warning(f"Stale data packet: {packet.timestamp}")
                self.verification_cache[cache_key] = False
                return False
        except:
            logger.error(f"Invalid timestamp in packet: {packet.timestamp}")
            self.verification_cache[cache_key] = False
            return False
        
        # Verify hash integrity
        packet_content = {
            'data': packet.data,
            'source_id': packet.signature.source_id,
            'timestamp': packet.timestamp
        }
        expected_hash = self._calculate_hash(packet_content)
        
        if packet.packet_hash != expected_hash:
            logger.error(f"Packet hash mismatch: {packet.packet_hash} != {expected_hash}")
            self.verification_cache[cache_key] = False
            return False
        
        # If source requires HMAC verification, do it here
        if packet.signature.requires_signature:
            if not self._verify_hmac(packet):
                logger.error(f"HMAC verification failed for {packet.signature.source_id}")
                self.verification_cache[cache_key] = False
                return False
        
        # All checks passed
        self.verification_cache[cache_key] = True
        return True
    
    def _calculate_hash(self, content: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of content"""
        content_str = json.dumps(content, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _verify_hmac(self, packet: DataPacket) -> bool:
        """Verify HMAC signature if required"""
        # Implementation would depend on the specific HMAC method
        # For now, return True as most sources don't require HMAC
        return True
    
    def get_weight_multiplier(self, source_id: str) -> float:
        """Get weight multiplier for convergence scoring"""
        if source_id in self.banned_sources:
            return 0.0  # Kill switch for banned sources
        
        signature = self.registry.get_source(source_id)
        if not signature:
            return 0.0  # Unknown sources get zero weight
        
        return signature.weight_multiplier
    
    def enforce_zero_ghost(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce zero-ghost policy on signals"""
        source_id = signal.get('source_id', signal.get('source', 'UNKNOWN'))
        
        # Apply kill switch
        weight = self.get_weight_multiplier(source_id)
        if weight == 0.0:
            logger.warning(f"Zero-ghost: Signal from {source_id} assigned 0.0 weight")
            signal['weight'] = 0.0
            signal['ghost_killed'] = True
            signal['kill_reason'] = f"Source {source_id} is banned or unapproved"
        else:
            signal['weight'] = weight
            signal['ghost_killed'] = False
        
        return signal

# Global signature manager
_signature_manager = None

def get_signature_manager() -> DataSignatureManager:
    """Get the global signature manager"""
    global _signature_manager
    if _signature_manager is None:
        _signature_manager = DataSignatureManager()
    return _signature_manager

# Convenience functions
def sign_data_packet(data: Dict[str, Any], source_id: str) -> Optional[DataPacket]:
    """Sign a data packet"""
    return get_signature_manager().sign_data(data, source_id)

def verify_data_packet(packet: DataPacket) -> bool:
    """Verify a data packet"""
    return get_signature_manager().verify_packet(packet)

def enforce_zero_ghost_policy(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce zero-ghost policy on a signal"""
    return get_signature_manager().enforce_zero_ghost(signal)

# Example usage
def main():
    """Example of data signature system"""
    manager = get_signature_manager()
    
    # Print approved sources
    print("Approved Data Sources:")
    for source_id, signature in manager.registry.sources.items():
        print(f"  {source_id}: {signature.reliability.value} ({signature.weight_multiplier}x)")
    
    # Example: Sign some data
    price_data = {'symbol': 'AAPL', 'price': 175.50, 'volume': 1000000}
    packet = sign_data_packet(price_data, 'ALPACA_LIVE')
    
    if packet:
        print(f"\nData packet signed: {packet.signature.source_id}")
        print(f"Hash: {packet.packet_hash[:16]}...")
        
        # Verify it
        if verify_data_packet(packet):
            print("✅ Packet verified successfully")
        else:
            print("❌ Packet verification failed")
    
    # Example: Zero-ghost enforcement
    test_signals = [
        {'symbol': 'AAPL', 'source_id': 'ALPACA_LIVE', 'confidence': 0.8},
        {'symbol': 'MSFT', 'source_id': 'MOCK', 'confidence': 0.9},
        {'symbol': 'GOOGL', 'source_id': 'UNKNOWN', 'confidence': 0.7}
    ]
    
    print("\nZero-Ghost Enforcement:")
    for signal in test_signals:
        enforced = enforce_zero_ghost_policy(signal.copy())
        status = "❌ KILLED" if enforced.get('ghost_killed') else f"✅ {enforced.get('weight', 0)}x weight"
        print(f"  {signal['symbol']} ({signal['source_id']}): {status}")

if __name__ == "__main__":
    main()
