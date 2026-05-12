"""
Sector Bias Breaker - Prevents AI from sticking to top 3 stocks
Forces exploration beyond the big names in each sector
"""

import asyncio
import sys
import os

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from typing import List, Dict, Set
import random

class SectorBiasBreaker:
    """Breaks the AI's tendency to only look at top 3 stocks in each sector"""
    
    def __init__(self, config):
        self.config = config
        
        # Define top 3 stocks that AI gets stuck on
        self.top_three_bias = {
            'TECHNOLOGY': ['AAPL', 'MSFT', 'GOOGL'],
            'FINANCE': ['JPM', 'BAC', 'WFC'],
            'HEALTHCARE': ['JNJ', 'UNH', 'PFE'],
            'ENERGY': ['XOM', 'CVX', 'COP'],
            'CONSUMER': ['AMZN', 'WMT', 'HD'],
            'INDUSTRIAL': ['CAT', 'DE', 'MMM'],
            'DEFENSE': ['LMT', 'BA', 'RTX'],
            'TELECOM': ['VZ', 'T', 'TMUS'],
            'AUTOS': ['TSLA', 'GM', 'F'],
            'RETAIL': ['WMT', 'TGT', 'COST'],
            'SEMICONDUCTORS': ['NVDA', 'AMD', 'INTC'],
            'SOFTWARE': ['MSFT', 'ORCL', 'SAP'],
            'INTERNET': ['GOOGL', 'META', 'AMZN'],
            'SOCIAL_MEDIA': ['META', 'SNAP', 'TWTR'],
            'STREAMING': ['NFLX', 'DIS', 'ROKU'],
            'GAMING': ['TTWO', 'EA', 'ATVI'],
            'BIOTECH': ['JNJ', 'PFE', 'MRK'],
            'PHARMA': ['JNJ', 'PFE', 'ABBV'],
            'INSURANCE': ['BRK.A', 'UNH', 'AIG'],
            'REAL_ESTATE': ['SPG', 'AMT', 'PLD'],
            'UTILITIES': ['NEE', 'DUK', 'SO'],
            'MATERIALS': ['LIN', 'DOW', 'DD'],
            'CHEMICALS': ['DOW', 'DD', 'BASF'],
            'AEROSPACE': ['BA', 'LMT', 'RTX'],
            'RAILROADS': ['UNP', 'CSX', 'NSC'],
            'SHIPPING': ['FDX', 'UPS', 'ZTO'],
            'MINING': ['BHP', 'RIO', 'VALE'],
            'OIL_SERVICES': ['SLB', 'HAL', 'BKR'],
            'GOLD': ['GOLD', 'NEM', 'BARRICK'],
            'SILVER': ['SLV', 'WPM', 'PAAS'],
            'COPPER': ['FCX', 'SCCO', 'RIO'],
            'LITHIUM': ['ALB', 'SQM', 'LTHM'],
            'SOLAR': ['ENPH', 'SEDG', 'FSLR'],
            'WIND': ['VWS', 'GE', 'SI'],
            'BATTERIES': ['TSLA', 'PANW', 'ENPH'],
            'EV_CHARGING': ['CHPT', 'EVGO', 'BLNK'],
            'CRYPTO': ['BTC', 'ETH', 'USDT'],
            'EXCHANGES': ['CME', 'ICE', 'NDAQ'],
            'BROKERAGE': ['SCHW', 'ETFC', 'AMTD'],
            'PAYMENTS': ['V', 'MA', 'PYPL'],
            'CARD_NETWORKS': ['V', 'MA', 'AXP'],
            'BUY_NOW_PAY': ['AFRM', 'PYPL', 'SQ'],
            'INSURANCE_TECH': ['ROOT', 'Lemonade', 'Hippo']
        }
        
        # Create expanded universe for each sector (beyond top 3)
        self.expanded_universe = {
            'TECHNOLOGY': [
                # Beyond AAPL, MSFT, GOOGL
                'META', 'NVDA', 'ADBE', 'CRM', 'NFLX', 'PYPL', 'INTC', 'CSCO', 'TXN', 'AVGO',
                'ACN', 'IBM', 'ORCL', 'SAP', 'NOW', 'INTU', 'MU', 'AMD', 'QCOM', 'AMAT',
                'SNPS', 'CDNS', 'KLAC', 'LRCX', 'MRVL', 'ANET', 'FTNT', 'PANW', 'CRWD', 'ZS',
                'OKTA', 'DDOG', 'ZM', 'DOCU', 'SNOW', 'PLTR', 'UPST', 'AFRM', 'SQ', 'ROKU'
            ],
            'FINANCE': [
                # Beyond JPM, BAC, WFC
                'GS', 'MS', 'C', 'AXP', 'BLK', 'SPGI', 'ICE', 'CME', 'SCHW', 'ETFC',
                'AMTD', 'V', 'MA', 'PYPL', 'COF', 'USB', 'PNC', 'TFC', 'FITB', 'KEY',
                'RF', 'HBAN', 'ZION', 'BOKF', 'PB', 'WTFC', 'CFR', 'NYCB', 'WAL', 'FHN'
            ],
            'HEALTHCARE': [
                # Beyond JNJ, UNH, PFE
                'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'MDT', 'ISRG', 'BMY', 'AMGN', 'GILD',
                'CVS', 'CI', 'SYK', 'BSX', 'BDX', 'HUM', 'ILMN', 'IDXX', 'STE', 'DVA',
                'HCA', 'THC', 'UHS', 'HCA', 'PFGC', 'CERN', 'ALGN', 'INMD', 'PKI', 'RMD'
            ],
            'ENERGY': [
                # Beyond XOM, CVX, COP
                'BP', 'SHEL', 'TOT', 'ENB', 'KMI', 'OXY', 'EOG', 'SLB', 'HAL', 'BKR',
                'XOM', 'CVX', 'COP', 'PSX', 'VLO', 'MPC', 'HES', 'MRO', 'DVN', 'FANG',
                'CLR', 'OKE', 'WMB', 'ET', 'KMI', 'ENB', 'PAA', 'EPD', 'MPLX', 'WES'
            ],
            'CONSUMER': [
                # Beyond AMZN, WMT, HD
                'COST', 'TGT', 'LOW', 'MCD', 'NKE', 'SBUX', 'TJX', 'ROST', 'KR', 'GPS',
                'ANF', 'URBN', 'LULU', 'EL', 'PVH', 'RL', 'TPR', 'COH', 'KORS', 'CPRI',
                'BBY', 'TSLA', 'F', 'GM', 'FCAU', 'TM', 'HMC', 'HYMTF', 'BYDDF', 'NIO'
            ],
            'INDUSTRIAL': [
                # Beyond CAT, DE, MMM
                'HON', 'GE', 'UPS', 'RTX', 'LMT', 'BA', 'NOC', 'GD', 'EMR', 'ITW',
                'TYN', 'ROP', 'PH', 'CARR', 'OTIS', 'WM', 'RSG', 'CL', 'KMB', 'GIS',
                'SYY', 'CCEP', 'KO', 'PEP', 'MNST', 'KDP', 'STZ', 'BUD', 'TAP', 'SAM'
            ],
            'DEFENSE': [
                # Beyond LMT, BA, RTX
                'NOC', 'GD', 'HII', 'LDOS', 'TXT', 'BWXT', 'AJRD', 'HEI', 'HEIA', 'SPR',
                'KTOS', 'MAXR', 'BA', 'LMT', 'RTX', 'GD', 'NOC', 'HII', 'LDOS', 'TXT'
            ],
            'SEMICONDUCTORS': [
                # Beyond NVDA, AMD, INTC
                'TSM', 'ASML', 'TXN', 'QCOM', 'BMCH', 'MU', 'MRVL', 'LRCX', 'KLAC', 'AMAT',
                'SNPS', 'CDNS', 'ADI', 'MCHP', 'MPWR', 'ON', 'SMTC', 'SWKS', 'QRVO', 'AVGO',
                'NXPI', 'NXP', 'INFY', 'CRUS', 'SYNA', 'CY', 'DIOD', 'POWI', 'SLAB', 'MXIM'
            ],
            'BIOTECH': [
                # Beyond JNJ, PFE, MRK
                'CRSP', 'EDIT', 'NTLA', 'BEAM', 'RNA', 'BLUE', 'GH', 'NVAX', 'MRNA', 'BNTX',
                'BIIB', 'GILD', 'AMGN', 'REGN', 'ALNY', 'IONS', 'SGMO', 'RGEN', 'BCRX', 'ARCT',
                'VIR', 'VERU', 'SAGE', 'CNSP', 'NBIX', 'PTCT', 'ARWR', 'DNA', 'SRPT', 'RARE'
            ],
            'CRYPTO': [
                # Beyond BTC, ETH, USDT
                'BNB', 'XRP', 'ADA', 'SOL', 'DOGE', 'DOT', 'SHIB', 'AVAX', 'MATIC', 'LINK',
                'UNI', 'LTC', 'ATOM', 'XLM', 'NEAR', 'ALGO', 'VET', 'FTT', 'ICP', 'HBAR',
                'FLOW', 'MANA', 'SAND', 'AXS', 'LRC', 'ENJ', 'CHZ', 'AAVE', 'SUSHI', 'CRV'
            ]
        }
        
        # Bias detection patterns
        self.bias_patterns = {
            'top_three_only': lambda signals: self._detect_top_three_bias(signals),
            'sector_concentration': lambda signals: self._detect_sector_concentration(signals),
            'market_cap_bias': lambda signals: self._detect_market_cap_bias(signals),
            'familiarity_bias': lambda signals: self._detect_familiarity_bias(signals)
        }
    
    def break_sector_bias(self, current_signals: List[Dict]) -> List[Dict]:
        """Identify and break sector bias in signals"""
        
        print("\n🚫 SECTOR BIAS BREAKER: Analyzing for top-3 bias...")
        print("-" * 60)
        
        # Detect biases
        biases_detected = {}
        for bias_name, detector in self.bias_patterns.items():
            bias_info = detector(current_signals)
            if bias_info['detected']:
                biases_detected[bias_name] = bias_info
                print(f"   ⚠️ {bias_name.replace('_', ' ').title()}: {bias_info['description']}")
        
        if not biases_detected:
            print("   ✅ No sector bias detected")
            return current_signals
        
        # Generate anti-bias recommendations
        anti_bias_signals = self._generate_anti_bias_opportunities(biases_detected)
        
        print(f"\n   Generated {len(anti_bias_signals)} anti-bias opportunities")
        
        # Combine with original
        enhanced_signals = current_signals + anti_bias_signals
        
        return enhanced_signals
    
    def _detect_top_three_bias(self, signals: List[Dict]) -> Dict:
        """Detect if AI is only looking at top 3 stocks"""
        sector_counts = {}
        top_three_detected = {}
        
        for signal in signals:
            symbol = signal.get('symbol', '')
            
            # Check which sector this symbol belongs to
            for sector, top_three in self.top_three_bias.items():
                if symbol in top_three:
                    if sector not in sector_counts:
                        sector_counts[sector] = {'top_three': 0, 'others': 0}
                    sector_counts[sector]['top_three'] += 1
                    top_three_detected[sector] = True
        
        # Check bias
        biased_sectors = []
        for sector, counts in sector_counts.items():
            if counts['top_three'] >= 2 and counts['others'] == 0:
                biased_sectors.append(sector)
        
        return {
            'detected': len(biased_sectors) > 0,
            'description': f"Stuck on top-3 in: {', '.join(biased_sectors)}",
            'biased_sectors': biased_sectors
        }
    
    def _detect_sector_concentration(self, signals: List[Dict]) -> Dict:
        """Detect if too concentrated in one sector"""
        sector_distribution = {}
        
        for signal in signals:
            symbol = signal.get('symbol', '')
            sector = self._find_symbol_sector(symbol)
            if sector:
                sector_distribution[sector] = sector_distribution.get(sector, 0) + 1
        
        # Check if any sector > 50% of signals
        total_signals = len(signals)
        concentrated_sectors = []
        
        for sector, count in sector_distribution.items():
            if count / total_signals > 0.5:
                concentrated_sectors.append(f"{sector} ({count/total_signals:.1%})")
        
        return {
            'detected': len(concentrated_sectors) > 0,
            'description': f"Over-concentrated in: {', '.join(concentrated_sectors)}",
            'distribution': sector_distribution
        }
    
    def _detect_market_cap_bias(self, signals: List[Dict]) -> Dict:
        """Detect if only looking at large caps"""
        # Simplified - would integrate with market cap data
        large_cap_symbols = {'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA'}
        
        large_cap_count = sum(1 for s in signals if s.get('symbol', '') in large_cap_symbols)
        
        return {
            'detected': large_cap_count / len(signals) > 0.7 if signals else False,
            'description': f"{large_cap_count}/{len(signals)} are large caps",
            'large_cap_ratio': large_cap_count / len(signals) if signals else 0
        }
    
    def _detect_familiarity_bias(self, signals: List[Dict]) -> Dict:
        """Detect if only familiar stocks"""
        # Most commonly known stocks
        familiar_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'JNJ', 'WMT',
            'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'XOM', 'CVX', 'LLY', 'PFE'
        }
        
        familiar_count = sum(1 for s in signals if s.get('symbol', '') in familiar_stocks)
        
        return {
            'detected': familiar_count / len(signals) > 0.6 if signals else False,
            'description': f"{familiar_count}/{len(signals)} are familiar stocks",
            'familiar_ratio': familiar_count / len(signals) if signals else 0
        }
    
    def _generate_anti_bias_opportunities(self, biases: Dict) -> List[Dict]:
        """Generate opportunities to counter detected biases"""
        opportunities = []
        
        # Counter top-3 bias
        if 'top_three_only' in biases:
            for sector in biases['top_three_only']['biased_sectors']:
                # Find stocks beyond top 3 in this sector
                if sector in self.expanded_universe:
                    # Pick 5 random stocks beyond top 3
                    expanded = self.expanded_universe[sector]
                    top_three = self.top_three_bias.get(sector, [])
                    beyond_top_three = [s for s in expanded if s not in top_three]
                    
                    for symbol in random.sample(beyond_top_three, min(5, len(beyond_top_three))):
                        opportunities.append({
                            'symbol': symbol,
                            'title': f"BEYOND TOP-3: {symbol} in {sector}",
                            'summary': f"Expanding beyond {', '.join(top_three)} to find {sector} opportunities",
                            'confidence': 0.6,
                            'bias_correction': 'top_three_bias',
                            'sector': sector
                        })
        
        # Counter sector concentration
        if 'sector_concentration' in biases:
            # Find opportunities in underrepresented sectors
            underrepresented = ['BIOTECH', 'CRYPTO', 'SEMICONDUCTORS', 'ENERGY']
            
            for sector in underrepresented:
                if sector in self.expanded_universe:
                    for symbol in random.sample(self.expanded_universe[sector], 3):
                        opportunities.append({
                            'symbol': symbol,
                            'title': f"SECTOR DIVERSIFICATION: {symbol} ({sector})",
                            'summary': f"Adding exposure to underrepresented {sector} sector",
                            'confidence': 0.55,
                            'bias_correction': 'sector_concentration',
                            'sector': sector
                        })
        
        # Counter market cap bias
        if 'market_cap_bias' in biases:
            # Add small/mid cap opportunities
            small_cap_examples = [
                {'symbol': 'MESH', 'cap': 'micro', 'price': 6.80},
                {'symbol': 'QBIT', 'cap': 'micro', 'price': 9.20},
                {'symbol': 'TECH', 'cap': 'small', 'price': 8.75},
                {'symbol': 'BIOX', 'cap': 'small', 'price': 15.20},
                {'symbol': 'FINQ', 'cap': 'mid', 'price': 22.30}
            ]
            
            for stock in small_cap_examples:
                opportunities.append({
                    'symbol': stock['symbol'],
                    'title': f"CAP DIVERSIFICATION: {stock['symbol']} ({stock['cap']} cap)",
                    'summary': f"Adding {stock['cap']} cap opportunity at ${stock['price']}",
                    'confidence': 0.65,
                    'bias_correction': 'market_cap_bias'
                })
        
        # Counter familiarity bias
        if 'familiarity_bias' in biases:
            # Add truly unfamiliar stocks
            unfamiliar_examples = [
                {'symbol': 'RENU', 'description': 'Renewable Energy IPO'},
                {'symbol': 'NUWR', 'description': 'Nuclear Waste Solutions'},
                {'symbol': 'PYKT', 'description': 'Payment Technology'},
                {'symbol': 'ZAPX', 'description': 'EV Charging Network'},
                {'symbol': 'MESH', 'description': 'Mesh Networking'}
            ]
            
            for stock in unfamiliar_examples:
                opportunities.append({
                    'symbol': stock['symbol'],
                    'title': f"UNFAMILIAR OPPORTUNITY: {stock['symbol']}",
                    'summary': stock['description'],
                    'confidence': 0.7,
                    'bias_correction': 'familiarity_bias'
                })
        
        return opportunities
    
    def _find_symbol_sector(self, symbol: str) -> str:
        """Find which sector a symbol belongs to"""
        for sector, symbols in self.top_three_bias.items():
            if symbol in symbols:
                return sector
        
        # Check expanded universe
        for sector, symbols in self.expanded_universe.items():
            if symbol in symbols:
                return sector
        
        return None

# Integration function
def break_sector_bias(current_signals: List[Dict]) -> List[Dict]:
    """Break sector bias in current signals"""
    
    print("=" * 80)
    print("🚫 SECTOR BIAS BREAKER - Preventing Top-3 Mentality")
    print("=" * 80)
    print("Ensuring AI looks beyond the big names in each sector...")
    print("=" * 80)
    
    # Initialize
    from config.secure_config import config
    breaker = SectorBiasBreaker(config)
    
    # Break bias
    enhanced_signals = breaker.break_sector_bias(current_signals)
    
    return enhanced_signals

if __name__ == "__main__":
    # Test with biased signals
    biased_signals = [
        {'symbol': 'AAPL', 'confidence': 0.8},
        {'symbol': 'MSFT', 'confidence': 0.7},
        {'symbol': 'GOOGL', 'confidence': 0.6},
        {'symbol': 'JPM', 'confidence': 0.7},
        {'symbol': 'BAC', 'confidence': 0.6},
        {'symbol': 'WFC', 'confidence': 0.5}
    ]
    
    enhanced = break_sector_bias(biased_signals)
    
    print(f"\nOriginal signals: {len(biased_signals)}")
    print(f"Enhanced signals: {len(enhanced)}")
    print(f"Anti-bias additions: {len(enhanced) - len(biased_signals)}")
