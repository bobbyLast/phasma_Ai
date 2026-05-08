"""
Whale Activity Tracker - Monitor large holder movements and exchange flows
Tracks whale behavior for both crypto and stock markets
"""

import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import yfinance as yf

@dataclass
class WhaleTransaction:
    """Single whale transaction"""
    timestamp: datetime
    whale_id: str
    transaction_type: str  # BUY/SELL/TRANSFER
    amount: float
    value_usd: float
    exchange: Optional[str]
    from_address: Optional[str]
    to_address: Optional[str]

@dataclass
class WhaleAlert:
    """Alert for significant whale activity"""
    symbol: str
    alert_type: str  # ACCUMULATION/DISTRIBUTION/EXCHANGE_FLOW
    severity: str  # HIGH/MEDIUM/LOW
    description: str
    data: Dict
    timestamp: datetime

class WhaleActivityTracker:
    """Track whale activity across crypto and stock markets"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # API endpoints (would need real API keys for production)
        self.cryptoquant_api = "https://api.cryptoquant.com/v1"
        self.glassnode_api = "https://api.glassnode.com/v1"
        
        # Whale thresholds
        self.whale_thresholds = {
            'btc': 100,  # 100 BTC minimum
            'eth': 1000,  # 1000 ETH minimum
            'stock_usd': 1_000_000,  # $1M minimum for stock whales
        }
        
        # Cache for whale data
        self.whale_cache = {}
        self.alert_history = []
        
        # Whale categories
        self.whale_categories = {
            'crypto': {
                'whales': '1000+ BTC',
                'sharks': '100-1000 BTC',
                'dolphins': '10-100 BTC',
                'crabs': '<10 BTC'
            },
            'stocks': {
                'whales': '$10M+ positions',
                'sharks': '$1M-$10M positions',
                'dolphins': '$100K-$1M positions'
            }
        }
        
        print("[WHALE] Whale Activity Tracker initialized")
        print("[WHALE] Tracking: BTC, ETH, and stock institutional flows")
    
    def analyze_whale_activity(self, symbol: str, asset_type: str = 'CRYPTO') -> Dict:
        """Analyze whale activity for a given symbol"""
        print(f"\n[WHALE] Analyzing whale activity for {symbol}")
        print("-" * 40)
        
        analysis = {
            'symbol': symbol,
            'asset_type': asset_type,
            'current_activity': {},
            'trends': {},
            'alerts': [],
            'exchange_flows': {},
            'holder_distribution': {},
            'large_transactions': [],
            'timestamp': datetime.now()
        }
        
        if asset_type == 'CRYPTO':
            analysis.update(self._analyze_crypto_whales(symbol))
        elif asset_type == 'STOCK':
            analysis.update(self._analyze_stock_whales(symbol))
        
        # Generate alerts based on activity
        alerts = self._generate_whale_alerts(analysis)
        analysis['alerts'] = alerts
        
        # Store alerts
        self.alert_history.extend(alerts)
        
        # Print summary
        self._print_whale_summary(analysis)
        
        return analysis
    
    def _analyze_crypto_whales(self, symbol: str) -> Dict:
        """Analyze crypto whale activity"""
        crypto_data = {}
        
        if symbol.upper() in ['BTC', 'BITCOIN', 'BTC-USD']:
            # Exchange flows (in/out of exchanges)
            exchange_data = self._get_crypto_exchange_flows('BTC')
            crypto_data['exchange_flows'] = exchange_data
            
            # Whale movements
            whale_data = self._get_crypto_whale_movements('BTC')
            crypto_data['whale_movements'] = whale_data
            
            # Holder distribution
            distribution = self._get_holder_distribution('BTC')
            crypto_data['holder_distribution'] = distribution
            
            # Large transactions (last 24h)
            large_txs = self._get_large_transactions('BTC')
            crypto_data['large_transactions'] = large_txs
            
            # Trend analysis
            trends = self._analyze_whale_trends(exchange_data, whale_data)
            crypto_data['trends'] = trends
            
            print(f"  Exchange Net Flow: {exchange_data.get('net_24h', 0):.0f} BTC")
            print(f"  Whale Activity: {whale_data.get('activity_level', 'UNKNOWN')}")
            print(f"  Large Transactions (24h): {len(large_txs)}")
        
        elif symbol.upper() in ['ETH', 'ETHEREUM']:
            # Similar analysis for ETH
            exchange_data = self._get_crypto_exchange_flows('ETH')
            crypto_data['exchange_flows'] = exchange_data
            
            whale_data = self._get_crypto_whale_movements('ETH')
            crypto_data['whale_movements'] = whale_data
            
            print(f"  Exchange Net Flow: {exchange_data.get('net_24h', 0):.0f} ETH")
            print(f"  Whale Activity: {whale_data.get('activity_level', 'UNKNOWN')}")
        
        return crypto_data
    
    def _analyze_stock_whales(self, symbol: str) -> Dict:
        """Analyze stock whale (institutional) activity"""
        stock_data = {}
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get institutional holders
            if 'institutionalHolders' in ticker.info:
                holders = ticker.info['institutionalHolders']
                stock_data['institutional_holders'] = holders
                
                # Calculate total institutional ownership
                total_inst_shares = sum(h.get('shares', 0) for h in holders)
                stock_data['total_institutional_shares'] = total_inst_shares
                
                # Identify largest holders
                if holders:
                    largest = max(holders, key=lambda x: x.get('shares', 0))
                    stock_data['largest_holder'] = largest
                    print(f"  Largest Institutional Holder: {largest.get('company', 'Unknown')}")
                    print(f"  Shares Held: {largest.get('shares', 0):,}")
            
            # Get major holders (if available)
            if 'majorHolders' in ticker.info:
                stock_data['major_holders'] = ticker.info['majorHolders']
            
            # Insider transactions (if available)
            if 'insiderTransactions' in ticker.info:
                insider_txs = ticker.info['insiderTransactions']
                stock_data['insider_transactions'] = insider_txs
                
                # Analyze insider sentiment
                insider_sentiment = self._analyze_insider_sentiment(insider_txs)
                stock_data['insider_sentiment'] = insider_sentiment
                print(f"  Insider Sentiment: {insider_sentiment}")
            
            # Recent significant transactions (simulated)
            recent_txs = self._get_significant_stock_transactions(symbol)
            stock_data['recent_transactions'] = recent_txs
            
            print(f"  Total Institutional Holders: {len(holders) if holders else 0}")
        
        except Exception as e:
            print(f"  Error analyzing stock whales: {e}")
        
        return stock_data
    
    def _get_crypto_exchange_flows(self, crypto: str) -> Dict:
        """Get crypto exchange flow data"""
        # Simulated data (would fetch from CryptoQuant/Glassnode in production)
        flows = {
            'inflow_24h': 1250,
            'outflow_24h': 2100,
            'net_24h': -850,  # Negative = outflow from exchanges (bullish)
            'inflow_7d': 8750,
            'outflow_7d': 12300,
            'net_7d': -3550,
            'inflow_30d': 37500,
            'outflow_30d': 42000,
            'net_30d': -4500,
            'trend': 'OUTFLOW'  # Overall trend
        }
        
        # Add exchange-specific data
        flows['by_exchange'] = {
            'binance': {'net_24h': -350},
            'coinbase': {'net_24h': -200},
            'kraken': {'net_24h': -150},
            'others': {'net_24h': -150}
        }
        
        return flows
    
    def _get_crypto_whale_movements(self, crypto: str) -> Dict:
        """Get whale movement data"""
        # Simulated whale tracking data
        movements = {
            'whale_count_24h': 45,
            'total_volume_24h': 2150,  # Total BTC moved by whales
            'accumulation_phase': True,
            'distribution_phase': False,
            'activity_level': 'HIGH_ACCUMULATION',
            'average_transaction_size': 47.8,
            'largest_transaction': 250,
            'whale_balance_change': '+1250 BTC',  # Net change in whale addresses
        }
        
        # Add category breakdown
        movements['by_category'] = {
            'whales_1000_plus': {'net_change': '+850 BTC', 'transactions': 12},
            'sharks_100_1000': {'net_change': '+400 BTC', 'transactions': 33},
        }
        
        return movements
    
    def _get_holder_distribution(self, crypto: str) -> Dict:
        """Get holder distribution data"""
        distribution = {
            'total_addresses': 980_000,
            'whale_addresses': 1050,  # 1000+ BTC
            'shark_addresses': 8900,  # 100-1000 BTC
            'whale_percentage': 0.11,  # 0.11% of addresses are whales
            'whale_holdings_percentage': 62.5,  # Whales hold 62.5% of supply
            'supply_distribution': {
                'whales': 62.5,
                'sharks': 25.0,
                'retail': 12.5
            }
        }
        
        return distribution
    
    def _get_large_transactions(self, crypto: str) -> List[Dict]:
        """Get large transactions from last 24h"""
        transactions = [
            {
                'hash': '0x1a2b3c...',
                'amount': 250.5,
                'value_usd': 16_282_500,
                'from': 'Unknown Whale',
                'to': 'Cold Storage',
                'exchange': None,
                'timestamp': datetime.now() - timedelta(hours=2)
            },
            {
                'hash': '0x4d5e6f...',
                'amount': 180.0,
                'value_usd': 11_700_000,
                'from': 'Exchange',
                'to': 'Unknown Wallet',
                'exchange': 'Binance',
                'timestamp': datetime.now() - timedelta(hours=5)
            },
            {
                'hash': '0x7g8h9i...',
                'amount': 125.0,
                'value_usd': 8_125_000,
                'from': 'Cold Storage',
                'to': 'Exchange',
                'exchange': 'Coinbase',
                'timestamp': datetime.now() - timedelta(hours=8)
            }
        ]
        
        return transactions
    
    def _analyze_insider_sentiment(self, insider_txs: List) -> str:
        """Analyze insider transaction sentiment"""
        if not insider_txs:
            return 'NO_DATA'
        
        # Count buys vs sells
        buys = sum(1 for tx in insider_txs if tx.get('transaction', '').lower() in ['buy', 'purchase'])
        sells = sum(1 for tx in insider_txs if tx.get('transaction', '').lower() in ['sell', 'sale'])
        
        if buys > sells * 1.5:
            return 'BULLISH'
        elif sells > buys * 1.5:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _get_significant_stock_transactions(self, symbol: str) -> List[Dict]:
        """Get significant stock transactions (Form 4 filings)"""
        # Simulated insider transactions
        transactions = [
            {
                'insider': 'CEO John Smith',
                'transaction': 'BUY',
                'shares': 50_000,
                'value': 2_500_000,
                'date': datetime.now() - timedelta(days=2),
                'form': '4'
            },
            {
                'insider': 'CFO Jane Doe',
                'transaction': 'SELL',
                'shares': 25_000,
                'value': 1_250_000,
                'date': datetime.now() - timedelta(days=5),
                'form': '4'
            }
        ]
        
        return transactions
    
    def _analyze_whale_trends(self, exchange_flows: Dict, whale_movements: Dict) -> Dict:
        """Analyze whale activity trends"""
        trends = {
            'short_term': 'NEUTRAL',
            'medium_term': 'BULLISH',
            'long_term': 'BULLISH',
            'confidence': 0.75,
            'reasoning': []
        }
        
        # Analyze exchange flows
        net_7d = exchange_flows.get('net_7d', 0)
        net_30d = exchange_flows.get('net_30d', 0)
        
        if net_7d < -1000:  # Significant outflow
            trends['short_term'] = 'BULLISH'
            trends['reasoning'].append(f'Exchange outflow of {-net_7d:.0f} BTC in 7 days')
        
        if net_30d < -5000:
            trends['medium_term'] = 'BULLISH'
            trends['reasoning'].append(f'Exchange outflow of {-net_30d:.0f} BTC in 30 days')
        
        # Analyze whale movements
        if whale_movements.get('accumulation_phase'):
            trends['long_term'] = 'BULLISH'
            trends['reasoning'].append('Whales in accumulation phase')
        
        # Check for divergence
        if trends['short_term'] != trends['medium_term']:
            trends['confidence'] *= 0.8
            trends['reasoning'].append('Short and medium term trends diverge')
        
        return trends
    
    def _generate_whale_alerts(self, analysis: Dict) -> List[WhaleAlert]:
        """Generate alerts based on whale activity"""
        alerts = []
        
        symbol = analysis['symbol']
        asset_type = analysis['asset_type']
        
        if asset_type == 'CRYPTO':
            exchange_flows = analysis.get('exchange_flows', {})
            whale_movements = analysis.get('whale_movements', {})
            
            # Alert for large exchange outflows
            net_24h = exchange_flows.get('net_24h', 0)
            if net_24h < -500:  # 500+ BTC outflow
                alerts.append(WhaleAlert(
                    symbol=symbol,
                    alert_type='EXCHANGE_OUTFLOW',
                    severity='HIGH' if net_24h < -1000 else 'MEDIUM',
                    description=f'Massive exchange outflow: {abs(net_24h):.0f} BTC moved to cold storage',
                    data={'amount': net_24h, 'threshold': 500},
                    timestamp=datetime.now()
                ))
            
            # Alert for whale accumulation
            if whale_movements.get('accumulation_phase'):
                whale_change = whale_movements.get('whale_balance_change', '0')
                if '+' in whale_change:
                    alerts.append(WhaleAlert(
                        symbol=symbol,
                        alert_type='WHALE_ACCUMULATION',
                        severity='HIGH',
                        description=f'Whales accumulating: {whale_change} net increase',
                        data={'balance_change': whale_change},
                        timestamp=datetime.now()
                    ))
            
            # Alert for large transactions
            large_txs = analysis.get('large_transactions', [])
            for tx in large_txs:
                if tx.get('amount', 0) > 200:  # 200+ BTC
                    alerts.append(WhaleAlert(
                        symbol=symbol,
                        alert_type='LARGE_TRANSACTION',
                        severity='MEDIUM',
                        description=f'Large transaction: {tx["amount"]:.1f} BTC (${tx["value_usd"]/1_000_000:.1f}M)',
                        data=tx,
                        timestamp=tx['timestamp']
                    ))
        
        elif asset_type == 'STOCK':
            # Alert for significant insider buying
            recent_txs = analysis.get('recent_transactions', [])
            for tx in recent_txs:
                if tx.get('transaction') == 'BUY' and tx.get('value', 0) > 1_000_000:
                    alerts.append(WhaleAlert(
                        symbol=symbol,
                        alert_type='INSIDER_BUYING',
                        severity='HIGH',
                        description=f'Insider buying: {tx["insider"]} bought {tx["shares"]:,} shares (${tx["value"]/1_000_000:.1f}M)',
                        data=tx,
                        timestamp=tx['date']
                    ))
            
            # Alert for institutional activity
            inst_holders = analysis.get('institutional_holders', [])
            if inst_holders and len(inst_holders) > 0:
                total_shares = analysis.get('total_institutional_shares', 0)
                if total_shares > 10_000_000:  # 10M+ shares
                    alerts.append(WhaleAlert(
                        symbol=symbol,
                        alert_type='INSTITUTIONAL_HOLDING',
                        severity='MEDIUM',
                        description=f'High institutional ownership: {total_shares:,} shares held',
                        data={'total_shares': total_shares, 'holder_count': len(inst_holders)},
                        timestamp=datetime.now()
                    ))
        
        return alerts
    
    def _print_whale_summary(self, analysis: Dict):
        """Print whale activity summary"""
        print("\n[WHALE ACTIVITY SUMMARY]")
        print("-" * 40)
        print(f"Symbol: {analysis['symbol']}")
        print(f"Asset Type: {analysis['asset_type']}")
        
        alerts = analysis.get('alerts', [])
        if alerts:
            print(f"\nALERTS: {len(alerts)} generated")
            for alert in alerts[:3]:  # Top 3 alerts
                print(f"  • {alert.alert_type}: {alert.description}")
        
        trends = analysis.get('trends', {})
        if trends:
            print(f"\nTRENDS:")
            print(f"  Short-term: {trends.get('short_term', 'UNKNOWN')}")
            print(f"  Medium-term: {trends.get('medium_term', 'UNKNOWN')}")
            print(f"  Long-term: {trends.get('long_term', 'UNKNOWN')}")
            print(f"  Confidence: {trends.get('confidence', 0):.1%}")
        
        print("-" * 40)
    
    def get_whale_alerts(self, hours: int = 24) -> List[WhaleAlert]:
        """Get recent whale alerts"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp > cutoff]
    
    def track_whale_portfolio(self, whale_addresses: List[str]) -> Dict:
        """Track specific whale addresses (crypto only)"""
        # This would require blockchain API access
        portfolio_data = {
            'addresses_tracked': len(whale_addresses),
            'total_balance': 0,
            'recent_activity': [],
            'portfolio_changes': []
        }
        
        print(f"[WHALE] Tracking {len(whale_addresses)} whale addresses")
        return portfolio_data
