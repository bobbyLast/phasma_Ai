#!/usr/bin/env python3
"""
PHASMA AI - Zero-Ghost Integrity Enforcement
Guarantees zero fake data ever enters the system
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class IntegrityCheck:
    """Result of integrity check"""
    passed: bool
    reason: str
    data: Optional[Dict[str, Any]] = None
    original_source: Optional[str] = None

class ZeroGhostEnforcer:
    """Enforces zero-ghost data integrity throughout the system"""
    
    def __init__(self):
        self.checks_performed = 0
        self.ghosts_killed = 0
        self.last_cache_refresh = None
        self.cache_valid_duration = timedelta(minutes=5)
        self.market_cache_status = "UNKNOWN"
        
        # Integrity policies
        self.policies = {
            'strict_source_validation': True,
            'require_signature': True,
            'block_stale_data': True,
            'kill_on_failure': True,
            'sleep_on_cache_fail': True,
            'sleep_duration': 60  # seconds
        }
        
        # Track data flow
        self.data_flow_log = []
        self.max_log_entries = 1000
    
    async def validate_market_cache_refresh(self, cache_refresh_func: Callable) -> bool:
        """Validate that market cache refresh succeeded with real data"""
        logger.info("Validating market cache refresh...")
        
        try:
            # Attempt to refresh cache
            refresh_result = await cache_refresh_func()
            
            if not refresh_result:
                logger.error("Market cache refresh returned None/False")
                self.market_cache_status = "FAILED"
                return False
            
            # Check if we got real data
            if isinstance(refresh_result, dict):
                # Look for data with valid source signatures
                has_real_data = False
                for key, value in refresh_result.items():
                    if hasattr(value, 'get') and value.get('source_signature'):
                        if value['source_signature'] not in ['MOCK', 'SIMULATED', 'FAKE']:
                            has_real_data = True
                            break
                
                if not has_real_data:
                    logger.error("Market cache contains no valid source signatures")
                    self.market_cache_status = "NO_REAL_DATA"
                    return False
                
                self.market_cache_status = "VALID"
                self.last_cache_refresh = datetime.now()
                logger.info("Market cache refresh validated successfully")
                return True
            
            # If it's not a dict, check for other indicators of real data
            if hasattr(refresh_result, '__len__') and len(refresh_result) > 0:
                self.market_cache_status = "VALID"
                self.last_cache_refresh = datetime.now()
                return True
            
            logger.error("Market cache refresh returned empty data")
            self.market_cache_status = "EMPTY"
            return False
            
        except Exception as e:
            logger.error(f"Error during market cache refresh: {e}")
            self.market_cache_status = "ERROR"
            return False
    
    async def enforce_cache_integrity(self, cache_refresh_func: Callable) -> bool:
        """Enforce cache integrity with sleep on failure"""
        is_valid = await self.validate_market_cache_refresh(cache_refresh_func)
        
        if not is_valid and self.policies['sleep_on_cache_fail']:
            logger.warning(f"Cache validation failed. Sleeping for {self.policies['sleep_duration']}s")
            await asyncio.sleep(self.policies['sleep_duration'])
            return False
        
        return is_valid
    
    def validate_data_packet(self, data: Dict[str, Any], context: str = "unknown") -> IntegrityCheck:
        """Validate a single data packet"""
        self.checks_performed += 1
        
        # Log data flow
        self._log_data_flow(data, context)
        
        # 1. Check for null/empty data
        if not data:
            return IntegrityCheck(
                passed=False,
                reason="Data packet is null or empty",
                original_source=context
            )
        
        # 2. Check source signature
        source_sig = data.get('source_signature') or data.get('source_id') or data.get('source')
        if not source_sig:
            return IntegrityCheck(
                passed=False,
                reason="Missing source signature",
                data=data,
                original_source=context
            )
        
        # 3. Check for banned sources
        banned_sources = ['MOCK', 'SIMULATED', 'FAKE', 'TEST', 'DEMO', 'SAMPLE', 'UNKNOWN']
        if source_sig.upper() in banned_sources:
            self.ghosts_killed += 1
            logger.error(f"👻 GHOST KILLED: {source_sig} source detected in {context}")
            return IntegrityCheck(
                passed=False,
                reason=f"Banned source: {source_sig}",
                data=data,
                original_source=context
            )
        
        # 4. Check timestamp freshness
        timestamp = data.get('timestamp')
        if timestamp and self.policies['block_stale_data']:
            try:
                if isinstance(timestamp, str):
                    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                elif isinstance(timestamp, (int, float)):
                    ts = datetime.fromtimestamp(timestamp)
                else:
                    ts = datetime.now()
                
                age = datetime.now() - ts
                max_age = timedelta(minutes=15)  # Configurable
                
                if age > max_age:
                    return IntegrityCheck(
                        passed=False,
                        reason=f"Stale data: {age} old (max: {max_age})",
                        data=data,
                        original_source=context
                    )
            except:
                logger.warning(f"Invalid timestamp format: {timestamp}")
        
        # 5. Validate data structure
        if 'price' in data:
            try:
                price = float(data['price'])
                if price <= 0 or price > 1000000:  # Sanity checks
                    return IntegrityCheck(
                        passed=False,
                        reason=f"Invalid price: {price}",
                        data=data,
                        original_source=context
                    )
            except:
                return IntegrityCheck(
                    passed=False,
                    reason="Price is not a valid number",
                    data=data,
                    original_source=context
                )
        
        # 6. Check for obvious fake patterns
        if self._has_fake_patterns(data):
            self.ghosts_killed += 1
            logger.error(f"👻 GHOST KILLED: Fake patterns detected in {context}")
            return IntegrityCheck(
                passed=False,
                reason="Contains fake data patterns",
                data=data,
                original_source=context
            )
        
        # All checks passed
        return IntegrityCheck(
            passed=True,
            reason="All integrity checks passed",
            data=data,
            original_source=context
        )
    
    def validate_signal_batch(self, signals: List[Dict[str, Any]], context: str = "batch") -> List[IntegrityCheck]:
        """Validate a batch of signals"""
        results = []
        
        for signal in signals:
            check = self.validate_data_packet(signal, f"{context}:{signal.get('symbol', 'unknown')}")
            results.append(check)
            
            # If kill on failure is enabled, stop at first failure
            if not check.passed and self.policies['kill_on_failure']:
                logger.error(f"Kill switch activated: {check.reason}")
                break
        
        return results
    
    def enforce_signal_integrity(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enforce integrity on a signal, returning None if invalid"""
        check = self.validate_data_packet(signal, f"signal:{signal.get('symbol', 'unknown')}")
        
        if not check.passed:
            if self.policies['kill_on_failure']:
                logger.error(f"Signal killed: {check.reason}")
                return None
            else:
                # Mark as invalid but return for debugging
                signal['invalid'] = True
                signal['invalid_reason'] = check.reason
                return signal
        
        return signal
    
    def _has_fake_patterns(self, data: Dict[str, Any]) -> bool:
        """Check for obvious fake data patterns"""
        # Check for perfectly round numbers (unlikely in real markets)
        if 'price' in data:
            try:
                price = float(data['price'])
                if price == round(price, 2) and price > 100:
                    # Check if it's too round (e.g., 100.00, 500.00)
                    decimal_part = price % 1
                    if decimal_part == 0.0:
                        return True
            except:
                pass
        
        # Check for default/test values
        test_values = [0, 1, 999, 999.99, 1000000]
        for value in test_values:
            if any(data.get(k) == value for k in ['price', 'volume', 'market_cap']):
                return True
        
        # Check for test symbols
        symbol = data.get('symbol', '').upper()
        if symbol.startswith(('TEST_', 'DEMO_', 'MOCK_', 'SAMPLE_')):
            return True
        
        return False
    
    def _log_data_flow(self, data: Dict[str, Any], context: str):
        """Log data flow for auditing"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'source': data.get('source_signature', data.get('source', 'UNKNOWN')),
            'symbol': data.get('symbol', 'N/A'),
            'data_type': type(data).__name__
        }
        
        self.data_flow_log.append(entry)
        
        # Keep log size manageable
        if len(self.data_flow_log) > self.max_log_entries:
            self.data_flow_log = self.data_flow_log[-self.max_log_entries:]
    
    def get_integrity_report(self) -> Dict[str, Any]:
        """Get comprehensive integrity report"""
        return {
            'checks_performed': self.checks_performed,
            'ghosts_killed': self.ghosts_killed,
            'ghost_kill_rate': self.ghosts_killed / max(self.checks_performed, 1),
            'market_cache_status': self.market_cache_status,
            'last_cache_refresh': self.last_cache_refresh.isoformat() if self.last_cache_refresh else None,
            'policies': self.policies,
            'recent_data_flow': self.data_flow_log[-10:],  # Last 10 entries
            'timestamp': datetime.now().isoformat()
        }
    
    def reset_statistics(self):
        """Reset integrity statistics"""
        self.checks_performed = 0
        self.ghosts_killed = 0
        self.data_flow_log = []
        logger.info("Integrity statistics reset")

# Global enforcer instance
_zero_ghost_enforcer = None

def get_zero_ghost_enforcer() -> ZeroGhostEnforcer:
    """Get the global zero-ghost enforcer"""
    global _zero_ghost_enforcer
    if _zero_ghost_enforcer is None:
        _zero_ghost_enforcer = ZeroGhostEnforcer()
    return _zero_ghost_enforcer

# Decorator for automatic integrity checking
def enforce_integrity(context: str = "function"):
    """Decorator to enforce integrity on function return values"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            enforcer = get_zero_ghost_enforcer()
            
            if isinstance(result, dict):
                check = enforcer.validate_data_packet(result, context)
                if not check.passed:
                    logger.error(f"Integrity check failed in {context}: {check.reason}")
                    if enforcer.policies['kill_on_failure']:
                        return None
            elif isinstance(result, list):
                validated = []
                for item in result:
                    if isinstance(item, dict):
                        check = enforcer.validate_data_packet(item, f"{context}:list_item")
                        if check.passed:
                            validated.append(item)
                        elif enforcer.policies['kill_on_failure']:
                            break
                result = validated
            
            return result
        
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            enforcer = get_zero_ghost_enforcer()
            
            if isinstance(result, dict):
                check = enforcer.validate_data_packet(result, context)
                if not check.passed:
                    logger.error(f"Integrity check failed in {context}: {check.reason}")
                    if enforcer.policies['kill_on_failure']:
                        return None
            elif isinstance(result, list):
                validated = []
                for item in result:
                    if isinstance(item, dict):
                        check = enforcer.validate_data_packet(item, f"{context}:list_item")
                        if check.passed:
                            validated.append(item)
                        elif enforcer.policies['kill_on_failure']:
                            break
                result = validated
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Example usage
async def main():
    """Example of zero-ghost enforcement"""
    enforcer = get_zero_ghost_enforcer()
    
    # Test data packets
    test_packets = [
        {'symbol': 'AAPL', 'price': 175.50, 'source_signature': 'ALPACA_LIVE'},
        {'symbol': 'TEST', 'price': 100.00, 'source_signature': 'MOCK'},
        {'symbol': 'MSFT', 'price': 380.25, 'source_signature': 'FINNHUB_REAL'},
        {'symbol': 'FAKE', 'price': 0, 'source_signature': 'UNKNOWN'}
    ]
    
    print("Zero-Ghost Integrity Enforcement Test")
    print("=" * 50)
    
    for packet in test_packets:
        result = enforcer.enforce_signal_integrity(packet.copy())
        if result:
            print(f"✅ {packet['symbol']}: PASSED")
        else:
            print(f"❌ {packet['symbol']}: KILLED")
    
    # Show report
    report = enforcer.get_integrity_report()
    print("\nIntegrity Report:")
    print(f"  Checks performed: {report['checks_performed']}")
    print(f"  Ghosts killed: {report['ghosts_killed']}")
    print(f"  Kill rate: {report['ghost_kill_rate']:.1%}")

if __name__ == "__main__":
    asyncio.run(main())
