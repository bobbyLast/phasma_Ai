"""
Expansion Engine - Forces AI to Discover NEW Stocks
Prevents getting stuck on known stocks and continuously expands universe
"""

import asyncio
import sys
import os

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from datetime import datetime, timedelta
from typing import List, Dict, Set
import random
import json

class ExpansionEngine:
    """Continuously expands the stock universe, preventing AI from getting stuck"""
    
    def __init__(self, config):
        self.config = config
        
        # Known stocks to avoid (prevents getting stuck)
        self.known_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM',
            'JNJ', 'WMT', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'XOM',
            'CVX', 'LLY', 'PFE', 'ABT', 'CRM', 'ACN', 'MRK', 'NFLX',
            'COST', 'LIN', 'NKE', 'ABBV', 'DHR', 'MDT', 'BMY', 'TXN',
            'NEE', 'AVGO', 'PLD', 'CMCSA', 'HON', 'T', 'ADBE', 'IBM',
            'ORCL', 'QCOM', 'CAT', 'DE', 'INTC', 'SAP', 'C', 'LOW',
            'GE', 'UPS', 'BA', 'MMM', 'LMT', 'RTX', 'AMD', 'TMO',
            'SBUX', 'GILD', 'AMAT', 'ISRG', 'EL', 'D', 'ZTS', 'BLK',
            'AIR', 'NOW', 'SPGI', 'MDLZ', 'ICE', 'SYK', 'PLTR', 'RCL',
            'MO', 'SNPS', 'CDNS', 'ADP', 'CSX', 'ATVI', 'KLAC', 'FTNT',
            'MCO', 'CPRT', 'MRNA', 'REGN', 'MXIM', 'EW', 'AON', 'SRE',
            'SHW', 'ORLY', 'CCI', 'EQIX', 'AEP', 'WELL', 'FIS', 'XEL',
            'PSA', 'CB', 'ANET', 'EXC', 'GM', 'DELL', 'TJX', 'PGR',
            'FDX', 'MET', 'CI', 'ETN', 'CME', 'A', 'PODD', 'DXCM',
            'MPC', 'EMR', 'JCI', 'HUM', 'KMB', 'KMI', 'WMB', 'CTVA',
            'WEC', 'HES', 'FCX', 'GIS', 'BSX', 'BDX', 'ROST', 'LRCX',
            'O', 'MCK', 'APH', 'ELV', 'MS', 'TRV', 'ADSK', 'ALL',
            'CL', 'K', 'PEG', 'SBAC', 'IQV', 'STZ', 'EOG', 'BDX',
            'DLR', 'PAYX', 'YUM', 'ROP', 'VRSK', 'AFL', 'COP', 'WM',
            'AMT', 'IRM', 'ECL', 'HPQ', 'AEE', 'ATO', 'SYY', 'TXT',
            'KDP', 'AWK', 'HCA', 'F', 'WBD', 'NUE', 'RSG', 'OKE',
            'MTD', 'CTAS', 'CMCSA', 'WST', 'MRO', 'XRAY', 'ANSS',
            'HII', 'WRK', 'LW', 'TRMB', 'CARR', 'GNRC', 'KEYS',
            'CDAY', 'OTIS', 'CBOE', 'CEG', 'GEHC', 'VLTO', 'FOUR'
        }
        
        # Expansion strategies
        self.expansion_strategies = {
            'new_listings': self._find_new_listings,
            'unusual_volume': self._find_unusual_volume,
            'sector_expansion': self._expand_sector_universe,
            'market_cap_expansion': self._expand_by_market_cap,
            'geographic_expansion': self._expand_geographically,
            'thematic_expansion': self._expand_by_themes,
            'social_discovery': self._discover_from_social,
            'options_flow_discovery': self._discover_from_options,
            'insider_discovery': self._discover_from_insiders,
            'random_exploration': self._random_explore
        }
        
        # Track discovered stocks
        self.discovered_today = set()
        self.discovery_history = []
        
        # Load previous discoveries
        self._load_discovery_history()
    
    async def expand_universe(self, current_signals: List[Dict]) -> List[Dict]:
        """Expand universe with NEW stocks, avoiding known ones"""
        
        print("\n🌍 EXPANSION ENGINE: Discovering NEW Opportunities")
        print("=" * 60)
        print("Avoiding known stocks to find fresh opportunities...")
        print("=" * 60)
        
        # Get symbols from current signals
        current_symbols = set(s.get('symbol', '') for s in current_signals)
        
        # Remove known stocks
        fresh_symbols = current_symbols - self.known_stocks
        print(f"   Fresh symbols in current signals: {len(fresh_symbols)}")
        
        # Run all expansion strategies
        new_discoveries = []
        
        for strategy_name, strategy_func in self.expansion_strategies.items():
            print(f"\n🔍 Running {strategy_name.replace('_', ' ').title()}...")
            
            try:
                discoveries = await strategy_func(current_signals)
                
                # Filter out known stocks
                fresh_discoveries = [d for d in discoveries if d.get('symbol', '') not in self.known_stocks]
                
                # Filter out already discovered today
                truly_new = [d for d in fresh_discoveries if d.get('symbol', '') not in self.discovered_today]
                
                new_discoveries.extend(truly_new)
                print(f"   Found {len(truly_new)} NEW opportunities")
                
            except Exception as e:
                print(f"   Error in {strategy_name}: {e}")
        
        # Remove duplicates
        unique_discoveries = self._deduplicate_discoveries(new_discoveries)
        
        # Sort by novelty score
        unique_discoveries.sort(key=lambda x: x.get('novelty_score', 0), reverse=True)
        
        # Update tracking
        for discovery in unique_discoveries:
            self.discovered_today.add(discovery.get('symbol', ''))
            self.discovery_history.append({
                'symbol': discovery.get('symbol', ''),
                'timestamp': datetime.now().isoformat(),
                'strategy': discovery.get('discovery_strategy', 'unknown'),
                'novelty_score': discovery.get('novelty_score', 0)
            })
        
        # Save history
        self._save_discovery_history()
        
        print(f"\n✅ Total NEW discoveries: {len(unique_discoveries)}")
        print(f"   Avoided {len(self.known_stocks)} known stocks")
        print(f"   Universe expanded by {len(unique_discoveries)} fresh opportunities")
        
        return unique_discoveries
    
    async def _find_new_listings(self, current_signals: List[Dict]) -> List[Dict]:
        """Find newly listed stocks"""
        discoveries = []
        
        # Simulate finding new listings (would integrate with IPO data)
        new_listings = [
            {'symbol': 'RENU', 'name': 'Renewable Energy NU', 'sector': 'Energy', 'price': 12.50},
            {'symbol': 'TECH', 'name': 'Tech Innovations Inc', 'sector': 'Technology', 'price': 8.75},
            {'symbol': 'BIOX', 'name': 'BioX Therapeutics', 'sector': 'Healthcare', 'price': 15.20},
            {'symbol': 'FINQ', 'name': 'Finance Quantum', 'sector': 'Finance', 'price': 22.30},
            {'symbol': 'SPACE', 'name': 'Space Exploration Co', 'sector': 'Industrial', 'price': 18.90}
        ]
        
        for listing in new_listings:
            if listing['symbol'] not in self.known_stocks:
                discoveries.append({
                    'symbol': listing['symbol'],
                    'title': f"NEW LISTING: {listing['name']} ({listing['symbol']})",
                    'summary': f"Recently listed {listing['sector']} company at ${listing['price']}",
                    'confidence': 0.6,
                    'discovery_strategy': 'new_listings',
                    'novelty_score': 0.9,
                    'trade_type': 'IPO_MOMENTUM'
                })
        
        return discoveries
    
    async def _find_unusual_volume(self, current_signals: List[Dict]) -> List[Dict]:
        """Find stocks with unusual volume"""
        discoveries = []
        
        # Simulate unusual volume scan
        volume_anomalies = [
            {'symbol': 'MESH', 'volume_ratio': 5.2, 'price': 6.80},
            {'symbol': 'QBIT', 'volume_ratio': 4.8, 'price': 9.20},
            {'symbol': 'NUWR', 'volume_ratio': 4.1, 'price': 14.50},
            {'symbol': 'PYKT', 'volume_ratio': 3.9, 'price': 11.30},
            {'symbol': 'ZAPX', 'volume_ratio': 3.5, 'price': 7.90}
        ]
        
        for anomaly in volume_anomalies:
            if anomaly['symbol'] not in self.known_stocks:
                discoveries.append({
                    'symbol': anomaly['symbol'],
                    'title': f"UNUSUAL VOLUME: {anomaly['symbol']} {anomaly['volume_ratio']}x normal",
                    'summary': f"Volume spike detected at ${anomaly['price']} per share",
                    'confidence': 0.65,
                    'discovery_strategy': 'unusual_volume',
                    'novelty_score': 0.8,
                    'trade_type': 'VOLUME_BREAKOUT'
                })
        
        return discoveries
    
    async def _expand_sector_universe(self, current_signals: List[Dict]) -> List[Dict]:
        """Find lesser-known stocks in hot sectors"""
        discoveries = []
        
        # Define sector expansions
        sector_expansions = {
            'AI_TECH': ['SOUN', 'UPST', 'PATH', 'DUOL', 'AI'],
            'BIOTECH': ['CRSP', 'EDIT', 'NTLA', 'BEAM', 'RNAC'],
            'CLEAN_ENERGY': ['ENPH', 'SEDG', 'RUN', 'FSLR', 'PLUG'],
            'FINTECH': ['SQ', 'PYPL', 'AFRM', 'UPST', 'SOFO'],
            'CYBERSECURITY': ['CRWD', 'ZS', 'OKTA', 'PANW', 'FTNT'],
            'E_COMMERCE': ['ETSY', 'CHWY', 'THD', 'BARK', 'BIGC'],
            'SEMICONDUCTORS': ['MRVL', 'MU', 'AMD', 'LRCX', 'KLAC'],
            'CANNABIS': ['TLRY', 'CGC', 'CRON', 'HEXO', 'ACB'],
            'GAMING': ['EA', 'TTWO', 'ATVI', 'MGAM', 'ZNGA'],
            'EV_CHARGING': ['CHPT', 'EVGO', 'BLNK', 'EV', 'TSLA']
        }
        
        # Find hot sectors from current signals
        hot_sectors = random.choice(list(sector_expansions.keys()))
        sector_stocks = sector_expansions[hot_sectors]
        
        for stock in sector_stocks:
            if stock not in self.known_stocks and stock not in self.discovered_today:
                discoveries.append({
                    'symbol': stock,
                    'title': f"SECTOR EXPANSION: {stock} in {hot_sectors}",
                    'summary': f"Lesser-known player in hot {hot_sectors.replace('_', ' ')} sector",
                    'confidence': 0.55,
                    'discovery_strategy': 'sector_expansion',
                    'novelty_score': 0.7,
                    'trade_type': 'SECTOR_BETA'
                })
        
        return discoveries[:5]  # Limit to 5
    
    async def _expand_by_market_cap(self, current_signals: List[Dict]) -> List[Dict]:
        """Find stocks in specific market cap ranges"""
        discoveries = []
        
        # Define market cap tiers
        cap_tiers = {
            'micro_cap': {'min': 50_000_000, 'max': 300_000_000, 'multiplier': 1.2},
            'small_cap': {'min': 300_000_000, 'max': 2_000_000_000, 'multiplier': 1.1},
            'mid_cap': {'min': 2_000_000_000, 'max': 10_000_000_000, 'multiplier': 1.0}
        }
        
        # Simulate finding stocks in each tier
        for tier, config in cap_tiers.items():
            sample_stocks = [
                {'symbol': f'M{random.randint(100, 999)}', 'cap': random.randint(config['min'], config['max'])}
                for _ in range(3)
            ]
            
            for stock in sample_stocks:
                if stock['symbol'] not in self.known_stocks:
                    discoveries.append({
                        'symbol': stock['symbol'],
                        'title': f"{tier.upper()}: {stock['symbol']} (${stock['cap']/1_000_000:.0f}M)",
                        'summary': f"{tier.replace('_', ' ').title()} opportunity with growth potential",
                        'confidence': 0.5,
                        'discovery_strategy': 'market_cap_expansion',
                        'novelty_score': 0.6,
                        'trade_type': 'CAP_TIER_PLAY'
                    })
        
        return discoveries
    
    async def _expand_geographically(self, current_signals: List[Dict]) -> List[Dict]:
        """Find international stocks"""
        discoveries = []
        
        # International opportunities
        international_stocks = [
            {'symbol': 'BABA', 'name': 'Alibaba', 'country': 'China'},
            {'symbol': 'TCEHY', 'name': 'Tencent', 'country': 'China'},
            {'symbol': 'ASML', 'name': 'ASML Holding', 'country': 'Netherlands'},
            {'symbol': 'SAP', 'name': 'SAP SE', 'country': 'Germany'},
            {'symbol': 'TM', 'name': 'Toyota', 'country': 'Japan'}
        ]
        
        for stock in international_stocks:
            if stock['symbol'] not in self.known_stocks:
                discoveries.append({
                    'symbol': stock['symbol'],
                    'title': f"INTERNATIONAL: {stock['name']} ({stock['country']})",
                    'summary': f"Opportunity in {stock['country']} market",
                    'confidence': 0.45,
                    'discovery_strategy': 'geographic_expansion',
                    'novelty_score': 0.75,
                    'trade_type': 'INTERNATIONAL_PLAY'
                })
        
        return discoveries
    
    async def _expand_by_themes(self, current_signals: List[Dict]) -> List[Dict]:
        """Find stocks based on emerging themes"""
        discoveries = []
        
        # Emerging themes
        themes = {
            'QUANTUM_COMPUTING': ['IONQ', 'QMCO', 'RGTI', 'ARQQ'],
            'SPACE_TECH': ['RKLB', 'ASTS', 'SPCE', 'MNTS'],
            'WEB3_BLOCKCHAIN': ['COIN', 'MARA', 'RIOT', 'HUT'],
            'GENE_EDITING': ['CRSP', 'EDIT', 'NTLA', 'BEAM'],
            'AUTONOMOUS_VEHICLES': ['GOOG', 'TSLA', 'CZR', 'LCID'],
            'ROBOTICS': ['IRBT', 'ROBO', 'BOTZ', 'AUBO'],
            '5G_INFRA': ['VZ', 'T', 'S', 'TMUS'],
            'WATER_TECH': ['AWK', 'WTRG', 'MSEX', 'AQUA'],
            'CARBON_CAPTURE': ['CCS', 'CCE', 'CLNE', 'BE'],
            'ALTERNATIVE_PROTEIN': ['BYND', 'TSN', 'PPC', 'JBS']
        }
        
        # Pick random theme
        theme = random.choice(list(themes.keys()))
        theme_stocks = themes[theme]
        
        for stock in theme_stocks:
            if stock not in self.known_stocks and stock not in self.discovered_today:
                discoveries.append({
                    'symbol': stock,
                    'title': f"THEME PLAY: {stock} in {theme.replace('_', ' ')}",
                    'summary': f"Exposure to emerging {theme.replace('_', ' ').lower()} theme",
                    'confidence': 0.6,
                    'discovery_strategy': 'thematic_expansion',
                    'novelty_score': 0.85,
                    'trade_type': 'THEMATIC_PLAY'
                })
        
        return discoveries[:3]
    
    async def _discover_from_social(self, current_signals: List[Dict]) -> List[Dict]:
        """Discover stocks trending on social media"""
        discoveries = []
        
        # Simulate social media trends
        social_trends = [
            {'symbol': 'GME', 'mentions': 50000, 'sentiment': 'bullish'},
            {'symbol': 'AMC', 'mentions': 45000, 'sentiment': 'bullish'},
            {'symbol': 'BB', 'mentions': 30000, 'sentiment': 'bullish'},
            {'symbol': 'NOK', 'mentions': 25000, 'sentiment': 'neutral'},
            {'symbol': 'SNDL', 'mentions': 20000, 'sentiment': 'bullish'}
        ]
        
        for trend in social_trends:
            if trend['symbol'] not in self.known_stocks:
                discoveries.append({
                    'symbol': trend['symbol'],
                    'title': f"SOCIAL BUZZ: {trend['symbol']} {trend['mentions']:,} mentions",
                    'summary': f"Trending on social media with {trend['sentiment']} sentiment",
                    'confidence': 0.7,
                    'discovery_strategy': 'social_discovery',
                    'novelty_score': 0.8,
                    'trade_type': 'SOCIAL_MOMENTUM'
                })
        
        return discoveries
    
    async def _discover_from_options(self, current_signals: List[Dict]) -> List[Dict]:
        """Discover stocks with unusual options activity"""
        discoveries = []
        
        # Simulate options flow
        options_flow = [
            {'symbol': 'RIVN', 'call_volume': 50000, 'strike': '$25'},
            {'symbol': 'LCID', 'call_volume': 45000, 'strike': '$20'},
            {'symbol': 'PLTR', 'call_volume': 40000, 'strike': '$15'},
            {'symbol': 'COIN', 'put_volume': 35000, 'strike': '$50'},
            {'symbol': 'MARA', 'call_volume': 30000, 'strike': '$10'}
        ]
        
        for flow in options_flow:
            if flow['symbol'] not in self.known_stocks:
                discoveries.append({
                    'symbol': flow['symbol'],
                    'title': f"OPTIONS FLOW: {flow['symbol']} unusual {flow.get('call_volume', flow.get('put_volume')):,} volume",
                    'summary': f"Unusual options activity at {flow['strike']} strike",
                    'confidence': 0.75,
                    'discovery_strategy': 'options_flow_discovery',
                    'novelty_score': 0.9,
                    'trade_type': 'OPTIONS_FLOW'
                })
        
        return discoveries
    
    async def _discover_from_insiders(self, current_signals: List[Dict]) -> List[Dict]:
        """Discover stocks with insider buying"""
        discoveries = []
        
        # Simulate insider trades
        insider_trades = [
            {'symbol': 'HOOD', 'insider': 'CEO', 'amount': '$1M', 'type': 'buy'},
            {'symbol': 'AFRM', 'insider': 'CFO', 'amount': '$500K', 'type': 'buy'},
            {'symbol': 'UPST', 'insider': 'Director', 'amount': '$250K', 'type': 'buy'},
            {'symbol': 'RBLX', 'insider': 'CTO', 'amount': '$750K', 'type': 'buy'},
            {'symbol': 'SNAP', 'insider': 'VP', 'amount': '$300K', 'type': 'buy'}
        ]
        
        for trade in insider_trades:
            if trade['symbol'] not in self.known_stocks:
                discoveries.append({
                    'symbol': trade['symbol'],
                    'title': f"INSIDER BUYING: {trade['insider']} {trade['type']}s {trade['amount']} of {trade['symbol']}",
                    'summary': f"Insider confidence with {trade['amount']} purchase",
                    'confidence': 0.8,
                    'discovery_strategy': 'insider_discovery',
                    'novelty_score': 0.85,
                    'trade_type': 'INSIDER_FOLLOW'
                })
        
        return discoveries
    
    async def _random_explore(self, current_signals: List[Dict]) -> List[Dict]:
        """Random exploration to find hidden gems"""
        discoveries = []
        
        # Generate random stock symbols (simulated)
        for _ in range(5):
            # Generate random 3-4 letter ticker
            length = random.choice([3, 4])
            symbol = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=length))
            
            if symbol not in self.known_stocks and symbol not in self.discovered_today:
                discoveries.append({
                    'symbol': symbol,
                    'title': f"HIDDEN GEM: {symbol} discovered by random exploration",
                    'summary': f"Random discovery requiring further investigation",
                    'confidence': 0.3,
                    'discovery_strategy': 'random_exploration',
                    'novelty_score': 0.95,
                    'trade_type': 'EXPLORATORY'
                })
        
        return discoveries
    
    def _deduplicate_discoveries(self, discoveries: List[Dict]) -> List[Dict]:
        """Remove duplicate discoveries"""
        seen_symbols = set()
        unique = []
        
        for discovery in discoveries:
            symbol = discovery.get('symbol', '')
            if symbol and symbol not in seen_symbols:
                seen_symbols.add(symbol)
                unique.append(discovery)
        
        return unique
    
    def _load_discovery_history(self):
        """Load previous discovery history"""
        try:
            with open('discovery_history.json', 'r') as f:
                data = json.load(f)
                self.discovery_history = data.get('history', [])
                
                # Load today's discoveries
                today = datetime.now().date().isoformat()
                for record in self.discovery_history:
                    if record['timestamp'].startswith(today):
                        self.discovered_today.add(record['symbol'])
        except:
            self.discovery_history = []
    
    def _save_discovery_history(self):
        """Save discovery history"""
        data = {
            'last_updated': datetime.now().isoformat(),
            'history': self.discovery_history[-1000:]  # Keep last 1000
        }
        
        with open('discovery_history.json', 'w') as f:
            json.dump(data, f, indent=2)

# Integration function
async def run_expansion_engine(current_signals: List[Dict]) -> List[Dict]:
    """Run expansion engine to find NEW opportunities"""
    
    print("=" * 80)
    print("🌍 EXPANSION ENGINE - FORCED DISCOVERY OF NEW STOCKS")
    print("=" * 80)
    print("Breaking free from known stocks to find fresh opportunities...")
    print("=" * 80)
    
    # Initialize
    from config.secure_config import config
    engine = ExpansionEngine(config)
    
    # Expand universe
    new_opportunities = await engine.expand_universe(current_signals)
    
    return new_opportunities

if __name__ == "__main__":
    # Test with sample signals
    sample_signals = [
        {'symbol': 'AAPL', 'confidence': 0.8},
        {'symbol': 'MSFT', 'confidence': 0.7},
        {'symbol': 'NEW1', 'confidence': 0.6}  # One new stock
    ]
    
    results = asyncio.run(run_expansion_engine(sample_signals))
    
    print(f"\n✅ Found {len(results)} NEW opportunities!")
    for r in results[:5]:
        print(f"   • {r['symbol']}: {r['title'][:50]}...")
