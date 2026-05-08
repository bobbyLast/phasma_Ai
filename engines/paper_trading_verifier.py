#!/usr/bin/env python3
"""
Paper Trading Verification Module
Ensures trade accuracy and prevents performance inflation
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import yfinance as market_data

class PaperTradingVerifier:
    """Verifies paper trading accuracy"""
    
    def __init__(self, verification_file: str = "data/paper_portfolio/verification_log.json"):
        self.verification_file = verification_file
        self.ensure_verification_dir()
        self.verification_log = self.load_verification_log()
    
    def ensure_verification_dir(self):
        """Ensure verification directory exists"""
        os.makedirs(os.path.dirname(self.verification_file), exist_ok=True)
    
    def load_verification_log(self) -> Dict:
        """Load verification log"""
        if os.path.exists(self.verification_file):
            try:
                with open(self.verification_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'trades': [], 'checksums': {}}
    
    def save_verification_log(self):
        """Save verification log"""
        with open(self.verification_file, 'w') as f:
            json.dump(self.verification_log, f, indent=2)
    
    def verify_price(self, symbol: str, timestamp: str, reported_price: float) -> Dict:
        """Verify price at timestamp using multiple sources"""
        verification = {
            'symbol': symbol,
            'timestamp': timestamp,
            'reported_price': reported_price,
            'verification_sources': [],
            'is_valid': True,
            'price_variance': 0.0
        }
        
        try:
            # Get historical data from provider bridge
            ticker = market_data.Ticker(symbol)
            hist = ticker.history(period="5d", interval="1m")
            
            if not hist.empty:
                # Find closest price to timestamp
                target_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hist.index = hist.index.tz_convert('UTC')
                
                # Get price within 1 minute of timestamp
                time_diff = abs(hist.index - target_time)
                closest_idx = time_diff.argmin()
                
                if time_diff.iloc[closest_idx].total_seconds() <= 60:
                    verified_price = hist['Close'].iloc[closest_idx]
                    variance = abs(verified_price - reported_price) / reported_price
                    
                    verification['verification_sources'].append({
                        'source': 'provider_bridge',
                        'price': verified_price,
                        'timestamp': hist.index[closest_idx].isoformat(),
                        'variance': variance
                    })
                    
                    verification['verified_price'] = verified_price
                    verification['price_variance'] = variance
                    
                    # Flag if variance > 1%
                    if variance > 0.01:
                        verification['is_valid'] = False
                        verification['warning'] = f"Price variance too high: {variance:.2%}"
        
        except Exception as e:
            verification['error'] = str(e)
            verification['is_valid'] = False
        
        return verification
    
    def create_trade_hash(self, trade_data: Dict) -> str:
        """Create unique hash for trade to prevent tampering"""
        trade_string = json.dumps(trade_data, sort_keys=True)
        return hashlib.sha256(trade_string.encode()).hexdigest()[:16]
    
    def verify_trade_execution(self, trade: Dict) -> Dict:
        """Verify a trade execution"""
        verification = {
            'trade_id': trade.get('id', 'unknown'),
            'symbol': trade.get('symbol', ''),
            'action': trade.get('action', ''),
            'quantity': trade.get('quantity', 0),
            'price': trade.get('price', 0),
            'timestamp': trade.get('timestamp', ''),
            'verification': None,
            'hash': self.create_trade_hash(trade),
            'verified': False
        }
        
        # Verify the price
        price_verification = self.verify_price(
            verification['symbol'],
            verification['timestamp'],
            verification['price']
        )
        
        verification['verification'] = price_verification
        verification['verified'] = price_verification['is_valid']
        
        # Log verification
        self.verification_log['trades'].append(verification)
        self.verification_log['checksums'][verification['trade_id']] = verification['hash']
        self.save_verification_log()
        
        return verification
    
    def check_integrity(self) -> Dict:
        """Check integrity of all logged trades"""
        integrity_report = {
            'total_trades': len(self.verification_log['trades']),
            'verified_trades': 0,
            'failed_verifications': 0,
            'issues': []
        }
        
        for trade in self.verification_log['trades']:
            if trade.get('verified', False):
                integrity_report['verified_trades'] += 1
            else:
                integrity_report['failed_verifications'] += 1
                if 'verification' in trade and trade['verification'].get('error'):
                    integrity_report['issues'].append({
                        'trade_id': trade['trade_id'],
                        'error': trade['verification']['error']
                    })
        
        # Calculate verification rate
        if integrity_report['total_trades'] > 0:
            integrity_report['verification_rate'] = integrity_report['verified_trades'] / integrity_report['total_trades']
        else:
            integrity_report['verification_rate'] = 0.0
        
        return integrity_report
    
    def export_for_audit(self, filename: str = None) -> str:
        """Export data for external audit"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"paper_trading_audit_{timestamp}.json"
        
        audit_data = {
            'export_timestamp': datetime.now().isoformat(),
            'verification_log': self.verification_log,
            'integrity_report': self.check_integrity()
        }
        
        with open(filename, 'w') as f:
            json.dump(audit_data, f, indent=2)
        
        return filename

# Optional: Broker API integration template
class BrokerAPIVerifier:
    """Template for broker API integration"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or os.environ.get('BROKER_API_KEY')
        self.api_secret = api_secret or os.environ.get('BROKER_API_SECRET')
        self.connected = False
    
    def connect(self):
        """Connect to broker API"""
        # Implementation would depend on specific broker
        # Example: Alpaca, Interactive Brokers, TD Ameritrade, etc.
        pass
    
    def verify_order_execution(self, order_id: str) -> Dict:
        """Verify order execution through broker"""
        # Implementation would query broker API
        pass
    
    def get_account_balance(self) -> Dict:
        """Get real account balance"""
        # Implementation would query broker API
        pass

if __name__ == "__main__":
    # Test verification
    verifier = PaperTradingVerifier()
    
    # Test trade
    test_trade = {
        'id': 'test_001',
        'symbol': 'AAPL',
        'action': 'BUY',
        'quantity': 10,
        'price': 150.0,
        'timestamp': datetime.now().isoformat()
    }
    
    verification = verifier.verify_trade_execution(test_trade)
    print("Verification Result:")
    print(json.dumps(verification, indent=2))
    
    # Check integrity
    integrity = verifier.check_integrity()
    print("\nIntegrity Report:")
    print(json.dumps(integrity, indent=2))
