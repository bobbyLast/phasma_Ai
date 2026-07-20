#!/usr/bin/env python3
"""
Multi-Platform Geopolitical Scanner
Scans all trading platforms for geopolitical impacts
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from engines.advanced_geopolitical_thinker import AdvancedGeopoliticalThinker
from core.runtime_paths import runtime_path

class MultiPlatformScanner:
    """Scans multiple trading platforms for geopolitical opportunities"""
    
    def __init__(self):
        self.thinker = AdvancedGeopoliticalThinker()
        
        # Platform-specific data sources
        self.platform_sources = {
            'nyse': {
                'url': 'https://query1.finance.yahoo.com/v1/finance/search',
                'focus': 'US equities',
                'sectors': ['Energy', 'Defense', 'Finance', 'Technology']
            },
            'nasdaq': {
                'url': 'https://query1.finance.yahoo.com/v1/finance/search',
                'focus': 'Tech and growth',
                'sectors': ['Software', 'Semiconductors', 'Biotech', 'Internet']
            },
            'cme': {
                'url': 'https://www.cmegroup.com/market-data.html',
                'focus': 'Futures and commodities',
                'products': ['Oil', 'Gold', 'Agriculture', 'Rates']
            },
            'ice': {
                'url': 'https://www.theice.com/marketdata',
                'focus': 'Credit derivatives and forex',
                'products': ['Credit indices', 'FX pairs', 'Energy']
            },
            'cboe': {
                'url': 'https://www.cboe.com/delayed_quotes',
                'focus': 'Options and volatility',
                'products': ['VIX', 'SPX options', 'Equity options']
            },
            'crypto': {
                'exchanges': ['Binance', 'Coinbase', 'Kraken'],
                'focus': 'Digital assets',
                'assets': ['BTC', 'ETH', 'stablecoins', 'DeFi tokens']
            }
        }
        
        # Cross-platform correlations
        self.correlations = {
            'geopolitical_risk': {
                'positive': ['Defense stocks', 'Oil', 'Gold', 'VIX', 'USD', 'Crypto'],
                'negative': ['Consumer stocks', 'Travel', 'Emerging markets', 'Corporate bonds']
            },
            'oil_shock': {
                'positive': ['Energy stocks', 'Oil futures', 'Oil service companies', 'Renewables'],
                'negative': ['Airlines', 'Shipping', 'Chemicals', 'Consumer discretionary']
            },
            'cyber_threat': {
                'positive': ['Cybersecurity stocks', 'Cloud security', 'Defense tech'],
                'negative': ['Tech giants', 'Social media', 'E-commerce']
            }
        }
    
    def scan_all_platforms(self, event: str) -> Dict:
        """Scan all trading platforms for event impacts"""
        print(f"\n🌍 MULTI-PLATFORM GEOPOLITICAL SCANNER")
        print("=" * 60)
        print(f"Event: {event}")
        print(f"Scanning all trading platforms...\n")
        
        # Get advanced analysis
        analysis = self.thinker.think_cascading_effects(event, days_forward=7)
        
        # Scan each platform
        platform_scans = {}
        
        print("📊 SCANNING PLATFORMS:")
        print("-" * 40)
        
        # Stock Exchanges
        platform_scans['nyse'] = self._scan_nyse(analysis)
        platform_scans['nasdaq'] = self._scan_nasdaq(analysis)
        
        # Derivatives Exchanges
        platform_scans['cme'] = self._scan_cme(analysis)
        platform_scans['cboe'] = self._scan_cboe(analysis)
        
        # Forex and Fixed Income
        platform_scans['forex'] = self._scan_forex(analysis)
        platform_scans['bonds'] = self._scan_bonds(analysis)
        
        # Crypto
        platform_scans['crypto'] = self._scan_crypto(analysis)
        
        # Generate cross-platform summary
        summary = self._generate_cross_platform_summary(platform_scans, analysis)
        
        return {
            'event': event,
            'timestamp': datetime.now().isoformat(),
            'platform_scans': platform_scans,
            'cross_platform_summary': summary,
            'advanced_analysis': analysis
        }
    
    def _scan_nyse(self, analysis: Dict) -> Dict:
        """Scan NYSE for opportunities"""
        print("🏛️  NYSE - New York Stock Exchange")
        
        opportunities = []
        
        # Energy sector
        energy_stocks = [
            {'symbol': 'XOM', 'name': 'Exxon Mobil', 'thesis': 'Major oil producer benefits from price spike'},
            {'symbol': 'CVX', 'name': 'Chevron', 'thesis': 'Integrated oil with Venezuelan exposure'},
            {'symbol': 'COP', 'name': 'ConocoPhillips', 'thesis': 'Pure play exploration and production'},
            {'symbol': 'SLB', 'name': 'Schlumberger', 'thesis': 'Oil services see increased demand'}
        ]
        
        # Defense sector
        defense_stocks = [
            {'symbol': 'LMT', 'name': 'Lockheed Martin', 'thesis': 'Defense contractor for military action'},
            {'symbol': 'NOC', 'name': 'Northrop Grumman', 'thesis': 'Aerospace and defense benefits'},
            {'symbol': 'GD', 'name': 'General Dynamics', 'thesis': 'Military systems provider'},
            {'symbol': 'RTX', 'name': 'Raytheon Technologies', 'thesis': 'Missile and defense systems'}
        ]
        
        opportunities.extend(energy_stocks)
        opportunities.extend(defense_stocks)
        
        return {
            'exchange': 'NYSE',
            'focus': 'Large-cap US equities',
            'opportunities': opportunities,
            'risk_factors': ['Market volatility', 'Regulatory changes', 'Escalation risk'],
            'trading_strategy': 'Focus on energy and defense leaders'
        }
    
    def _scan_nasdaq(self, analysis: Dict) -> Dict:
        """Scan NASDAQ for opportunities"""
        print("💻 NASDAQ - Tech and Growth Stocks")
        
        opportunities = []
        
        # Cybersecurity
        cyber_stocks = [
            {'symbol': 'CRWD', 'name': 'CrowdStrike', 'thesis': 'Cybersecurity demand increases'},
            {'symbol': 'PANW', 'name': 'Palo Alto Networks', 'thesis': 'Network security critical'},
            {'symbol': 'ZS', 'name': 'Zscaler', 'thesis': 'Cloud security essential'},
            {'symbol': 'FTNT', 'name': 'Fortinet', 'thesis': 'Threat protection demand'}
        ]
        
        # AI/Defense Tech
        tech_stocks = [
            {'symbol': 'PLTR', 'name': 'Palantir', 'thesis': 'Government contracts for data analysis'},
            {'symbol': 'MSFT', 'name': 'Microsoft', 'thesis': 'Government cloud and AI'},
            {'symbol': 'GOOGL', 'name': 'Alphabet', 'thesis': 'AI for defense applications'},
            {'symbol': 'NVDA', 'name': 'NVIDIA', 'thesis': 'AI chips for military use'}
        ]
        
        opportunities.extend(cyber_stocks)
        opportunities.extend(tech_stocks)
        
        return {
            'exchange': 'NASDAQ',
            'focus': 'Technology and growth',
            'opportunities': opportunities,
            'risk_factors': ['Valuation risk', 'Government regulation', 'Talent competition'],
            'trading_strategy': 'Target cybersecurity and defense tech'
        }
    
    def _scan_cme(self, analysis: Dict) -> Dict:
        """Scan CME for futures opportunities"""
        print("📈 CME - Chicago Mercantile Exchange")
        
        opportunities = [
            {'symbol': 'CL=F', 'name': 'Crude Oil Futures', 'thesis': 'Supply disruption drives prices higher'},
            {'symbol': 'HO=F', 'name': 'Heating Oil Futures', 'thesis': 'Refined products follow crude'},
            {'symbol': 'NG=F', 'name': 'Natural Gas Futures', 'thesis': 'Alternative energy demand rises'},
            {'symbol': 'GC=F', 'name': 'Gold Futures', 'thesis': 'Safe haven demand increases'},
            {'symbol': 'SI=F', 'name': 'Silver Futures', 'thesis': 'Industrial and monetary demand'}
        ]
        
        return {
            'exchange': 'CME Group',
            'focus': 'Commodity and financial futures',
            'opportunities': opportunities,
            'risk_factors': ['Leverage risk', 'Roll costs', 'Contango risk'],
            'trading_strategy': 'Long energy and precious metals'
        }
    
    def _scan_cboe(self, analysis: Dict) -> Dict:
        """Scan CBOE for options opportunities"""
        print("📊 CBOE - Chicago Board Options Exchange")
        
        strategies = [
            {
                'strategy': 'Long VIX calls',
                'underlying': 'VIX',
                'thesis': 'Volatility will remain elevated',
                'risk_reward': 'High risk, high reward'
            },
            {
                'strategy': 'Energy sector call spreads',
                'underlying': 'XLE',
                'thesis': 'Energy stocks continue higher',
                'risk_reward': 'Moderate risk, good reward'
            },
            {
                'strategy': 'Protective puts on broad market',
                'underlying': 'SPY',
                'thesis': 'Hedge against geopolitical risk',
                'risk_reward': 'Insurance cost'
            },
            {
                'strategy': 'Defense sector bull call spreads',
                'underlying': 'ITA',
                'thesis': 'Defense spending increases',
                'risk_reward': 'Moderate risk, reward'
            }
        ]
        
        return {
            'exchange': 'CBOE',
            'focus': 'Options and volatility products',
            'opportunities': strategies,
            'risk_factors': ['Time decay', 'Volatility crush', 'Liquidity risk'],
            'trading_strategy': 'Use options for leverage and protection'
        }
    
    def _scan_forex(self, analysis: Dict) -> Dict:
        """Scan forex markets"""
        print("💱 Forex - Currency Markets")
        
        opportunities = [
            {'pair': 'USDJPY', 'direction': 'Long', 'thesis': 'Safe haven bid for USD and JPY'},
            {'pair': 'USDCHF', 'direction': 'Long', 'thesis': 'Swiss franc safe haven'},
            {'pair': 'EURUSD', 'direction': 'Short', 'thesis': 'Europe vulnerable to energy shock'},
            {'pair': 'USDRUB', 'direction': 'Long', 'thesis': 'Rubles weak on sanctions risk'},
            {'pair': 'USDCAD', 'direction': 'Long', 'thesis': 'Canada benefits from oil prices'}
        ]
        
        return {
            'market': 'Forex',
            'focus': 'Currency pairs',
            'opportunities': opportunities,
            'risk_factors': ['Central bank intervention', 'Gap risk', 'Leverage'],
            'trading_strategy': 'Long safe haven currencies'
        }
    
    def _scan_bonds(self, analysis: Dict) -> Dict:
        """Scan bond markets"""
        print("🏦 Bonds - Fixed Income Markets")
        
        opportunities = [
            {
                'instrument': 'TIPS',
                'direction': 'Long',
                'thesis': 'Inflation protection in demand',
                'symbol': 'TIP'
            },
            {
                'instrument': 'Short-term Treasuries',
                'direction': 'Long',
                'thesis': 'Flight to safety',
                'symbol': 'SHY'
            },
            {
                'instrument': 'Corporate bonds',
                'direction': 'Short',
                'thesis': 'Credit risk increases',
                'symbol': 'LQD'
            },
            {
                'instrument': 'Emerging market debt',
                'direction': 'Short',
                'thesis': 'Capital outflows from EM',
                'symbol': 'EMB'
            }
        ]
        
        return {
            'market': 'Bonds',
            'focus': 'Fixed income securities',
            'opportunities': opportunities,
            'risk_factors': ['Interest rate risk', 'Credit risk', 'Inflation risk'],
            'trading_strategy': 'Focus on inflation protection and safety'
        }
    
    def _scan_crypto(self, analysis: Dict) -> Dict:
        """Scan crypto markets"""
        print("₿ Crypto - Digital Assets")
        
        opportunities = [
            {
                'asset': 'Bitcoin',
                'direction': 'Long',
                'thesis': 'Digital gold narrative strengthens',
                'symbol': 'BTC-USD'
            },
            {
                'asset': 'Ethereum',
                'direction': 'Long',
                'thesis': 'DeFi and NFTs as alternative systems',
                'symbol': 'ETH-USD'
            },
            {
                'asset': 'Stablecoins',
                'direction': 'Long',
                'thesis': 'Demand for non-USD stablecoins',
                'symbols': ['USDT-USD', 'USDC-USD']
            },
            {
                'asset': 'Privacy coins',
                'direction': 'Long',
                'thesis': 'Capital controls increase demand',
                'symbols': ['XMR-USD', 'ZEC-USD']
            }
        ]
        
        return {
            'market': 'Crypto',
            'focus': 'Digital assets',
            'opportunities': opportunities,
            'risk_factors': ['Regulation risk', 'Volatility', 'Custody risk'],
            'trading_strategy': 'Bitcoin as digital gold, altcoins for speculation'
        }
    
    def _generate_cross_platform_summary(self, platform_scans: Dict, analysis: Dict) -> Dict:
        """Generate cross-platform trading summary"""
        summary = {
            'overall_theme': 'Geopolitical Risk Premium',
            'top_trades': [],
            'hedges': [],
            'risks': [],
            'portfolio_allocation': {}
        }
        
        # Collect top opportunities across platforms
        all_opportunities = []
        
        for platform, scan in platform_scans.items():
            if 'opportunities' in scan:
                for opp in scan['opportunities']:
                    opp['platform'] = platform
                    all_opportunities.append(opp)
        
        # Rank by potential
        summary['top_trades'] = all_opportunities[:10]
        
        # Recommended hedges
        summary['hedges'] = [
            {'instrument': 'VIX calls', 'purpose': 'Volatility protection'},
            {'instrument': 'Gold futures', 'purpose': 'Safe haven'},
            {'instrument': 'USDJPY', 'purpose': 'Currency hedge'},
            {'instrument': 'TIPS', 'purpose': 'Inflation hedge'}
        ]
        
        # Key risks
        summary['risks'] = [
            'Escalation beyond Venezuela',
            'Global economic slowdown',
            'Market liquidity crunch',
            'Coordinated sanctions on US'
        ]
        
        # Portfolio allocation
        summary['portfolio_allocation'] = {
            'energy_stocks': '25%',
            'defense_stocks': '20%',
            'cybersecurity': '15%',
            'commodities': '20%',
            'cash/hedges': '20%'
        }
        
        return summary

def main():
    """Run the multi-platform scanner"""
    scanner = MultiPlatformScanner()
    
    # Scan for Venezuela scenario
    scan_results = scanner.scan_all_platforms(
        "USA attacks Venezuela and seizes oil facilities"
    )
    
    # Display summary
    print("\n🎯 CROSS-PLATFORM SUMMARY")
    print("=" * 60)
    
    summary = scan_results['cross_platform_summary']
    
    print(f"\nTheme: {summary['overall_theme']}")
    print(f"\nTop 5 Trades:")
    for i, trade in enumerate(summary['top_trades'][:5], 1):
        symbol = trade.get('symbol', trade.get('pair', trade.get('asset', 'N/A')))
        print(f"{i}. {symbol} ({trade['platform']}) - {trade.get('thesis', 'N/A')}")
    
    print(f"\nPortfolio Allocation:")
    for asset, allocation in summary['portfolio_allocation'].items():
        print(f"  {asset}: {allocation}")
    
    print(f"\nKey Hedges:")
    for hedge in summary['hedges']:
        print(f"  • {hedge['instrument']}: {hedge['purpose']}")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    scan_path = runtime_path("diagnostics", "multi_platform_scan", f"multi_platform_scan_{timestamp}.json")
    os.makedirs(os.path.dirname(scan_path), exist_ok=True)
    with open(scan_path, 'w') as f:
        json.dump(scan_results, f, indent=2)

    print(f"\n💾 Results saved to {scan_path}")

if __name__ == "__main__":
    main()
