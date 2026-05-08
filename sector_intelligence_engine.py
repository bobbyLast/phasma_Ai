"""
Enhanced Sector Intelligence & Kalshi Correlation
Understands sector moves, good runs (not just moonshots), and cross-platform signals
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import List, Dict, Set, Tuple
import re

class SectorIntelligenceEngine:
    """Understands sector correlations and cross-platform opportunities"""
    
    def __init__(self, config):
        self.config = config
        
        # Sector/Industry mappings
        self.sector_mappings = {
            'TECHNOLOGY': {
                'tickers': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC', 'CSCO', 'ORCL', 'CRM'],
                'keywords': ['technology', 'software', 'cloud', 'ai', 'semiconductor', 'chip', 'tech'],
                'etfs': ['QQQ', 'XLK', 'VGT', 'IYW'],
                'kalshi_events': ['tech_sector_performance', 'ai_stocks', 'semiconductor_demand']
            },
            'DEFENSE/MILITARY': {
                'tickers': ['LMT', 'BA', 'RTX', 'NOC', 'GD', 'HII', 'LDOS', 'TXT', 'BWXT', 'AJRD'],
                'keywords': ['defense', 'military', 'weapons', 'aerospace', 'contractor', 'pentagon', 'war', 'conflict'],
                'etfs': ['ITA', 'XAR', 'PPA', 'DFEN'],
                'kalshi_events': ['defense_spending', 'military_conflict', 'weapons_demand', 'geopolitical_risk']
            },
            'ENERGY/OIL': {
                'tickers': ['XOM', 'CVX', 'COP', 'BP', 'SHEL', 'TOT', 'ENB', 'KMI', 'OXY', 'EOG'],
                'keywords': ['oil', 'energy', 'petroleum', 'gas', 'drilling', 'refinery', 'opec'],
                'etfs': ['XLE', 'VDE', 'USO', 'DBE'],
                'kalshi_events': ['oil_prices', 'energy_demand', 'geopolitical_oil']
            },
            'FINANCE': {
                'tickers': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'AXP', 'COF', 'USB'],
                'keywords': ['bank', 'financial', 'finance', 'insurance', 'credit', 'lending'],
                'etfs': ['XLF', 'VFH', 'KBE', 'KRE'],
                'kalshi_events': ['bank_stress', 'fed_rates', 'financial_performance']
            },
            'HEALTHCARE': {
                'tickers': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'MRK', 'MDT', 'ISRG', 'BIIB'],
                'keywords': ['healthcare', 'pharma', 'medical', 'drug', 'fda', 'biotech', 'hospital'],
                'etfs': ['XLV', 'VHT', 'IYH', 'XBI'],
                'kalshi_events': ['fda_approvals', 'healthcare_demand', 'drug_trials']
            },
            'CONSUMER': {
                'tickers': ['AMZN', 'WMT', 'TGT', 'HD', 'MCD', 'NKE', 'COST', 'SBUX', 'LOW', 'TJX'],
                'keywords': ['consumer', 'retail', 'shopping', 'ecommerce', 'brands', 'sales'],
                'etfs': ['XLY', 'VCR', 'IYC', 'RTH'],
                'kalshi_events': ['consumer_spending', 'retail_sales', 'holiday_sales']
            },
            'INDUSTRIAL': {
                'tickers': ['CAT', 'DE', 'MMM', 'GE', 'HON', 'UPS', 'BA', 'LMT', 'RTX', 'NOC'],
                'keywords': ['industrial', 'manufacturing', 'construction', 'machinery', 'aviation', 'transport'],
                'etfs': ['XLI', 'VIS', 'IYJ', 'DIA'],
                'kalshi_events': ['manufacturing', 'infrastructure', 'industrial_production']
            },
            'CRYPTO/DIGITAL': {
                'tickers': ['BTC', 'ETH', 'MSTR', 'COIN', 'MARA', 'RIOT', 'SQ', 'PYPL', 'HOOD', 'BKKT'],
                'keywords': ['crypto', 'bitcoin', 'blockchain', 'digital', 'mining', 'exchange'],
                'etfs': ['BITO', 'GBTC', 'MARA'],
                'kalshi_events': ['crypto_prices', 'bitcoin_adoption', 'blockchain_usage']
            },
            'COMMODITIES': {
                'tickers': ['GOLD', 'SLV', 'COPPER', 'PLAT', 'PALL', 'DBA', 'USO', 'UNG', 'WEAT', 'DBB'],
                'keywords': ['gold', 'silver', 'copper', 'commodity', 'metal', 'agriculture', 'wheat'],
                'etfs': ['GLD', 'SLV', 'DBA', 'USO', 'UNG'],
                'kalshi_events': ['gold_prices', 'silver_prices', 'commodity_demand', 'inflation_hedge']
            },
            'REAL ESTATE': {
                'tickers': ['SPG', 'AMT', 'PLD', 'CCI', 'EQIX', 'PRO', 'DLR', 'EXR', 'MAA', 'AVB'],
                'keywords': ['real estate', 'reit', 'property', 'rent', 'mortgage', 'housing'],
                'etfs': ['XLRE', 'VNQ', 'IYR', 'RWR'],
                'kalshi_events': ['housing_market', 'mortgage_rates', 'reit_performance']
            }
        }
        
        # Good run thresholds (not moonshots)
        self.good_run_thresholds = {
            'min_confidence': 0.40,  # 40% is good enough
            'min_gain_potential': 0.10,  # 10% gain is good
            'max_timeframe': 30,  # 30 days max
            'min_sources': 1  # 1 source is enough for good runs
        }
        
        # Kalshi event patterns
        self.kalshi_patterns = {
            'sector_performance': "Will {sector} ETF outperform the market in {days} days?",
            'event_impact': "Will {event} impact {sector} stocks positively?",
            'geopolitical': "Will {region} tensions boost {sector} stocks?",
            'earnings_season': "Will {sector} beat earnings expectations?",
            'fed_impact': "Will {sector} benefit from Fed decision?"
        }
    
    async def analyze_sector_opportunities(self, news_items: List[Dict]) -> List[Dict]:
        """Analyze news for sector-wide opportunities"""
        
        print("\n🏭 SECTOR INTELLIGENCE: Analyzing industry-wide opportunities...")
        print("-" * 60)
        
        # Group news by sector
        sector_signals = {}
        
        for item in news_items:
            sectors = self._identify_sectors(item)
            
            for sector in sectors:
                if sector not in sector_signals:
                    sector_signals[sector] = {
                        'tickers': set(),
                        'news_items': [],
                        'confidence_score': 0,
                        'event_type': None,
                        'urgency': 'normal'
                    }
                
                sector_signals[sector]['news_items'].append(item)
                sector_signals[sector]['confidence_score'] += item.get('confidence', 0.5)
                
                # Extract tickers
                symbol = item.get('symbol', '')
                if symbol and symbol in self.sector_mappings[sector]['tickers']:
                    sector_signals[sector]['tickers'].add(symbol)
        
        # Analyze each sector
        sector_opportunities = []
        
        for sector, data in sector_signals.items():
            if not data['news_items']:
                continue
            
            # Check if this is a good run (not moonshot)
            if self._is_good_run(data):
                opportunity = await self._create_sector_opportunity(sector, data)
                sector_opportunities.append(opportunity)
                
                print(f"   ✅ {sector}: {len(data['tickers'])} stocks | {data['confidence_score']:.1%} confidence")
        
        print(f"\n   Found {len(sector_opportunities)} sector opportunities")
        return sector_opportunities
    
    async def check_kalshi_correlations(self, sector_opportunities: List[Dict]) -> List[Dict]:
        """Check Kalshi for correlated events"""
        
        print("\n🎯 KALSHI CORRELATION: Checking for related events...")
        print("-" * 60)
        
        correlated_events = []
        
        for opp in sector_opportunities:
            sector = opp['sector']
            
            # Get relevant Kalshi events for this sector
            kalshi_events = self._find_kalshi_events(sector, opp)
            
            for event in kalshi_events:
                correlated_events.append({
                    'sector': sector,
                    'news_confidence': opp['confidence'],
                    'kalshi_event': event,
                    'correlation_score': self._calculate_correlation_score(opp, event),
                    'combined_signal': self._create_combined_signal(opp, event)
                })
                
                print(f"   ✅ {sector}: {event['title']} | {event['confidence']:.1%} confidence")
        
        print(f"\n   Found {len(correlated_events)} correlated Kalshi events")
        return correlated_events
    
    async def find_related_stocks(self, initial_signals: List[Dict]) -> List[Dict]:
        """Find related stocks in the same industry"""
        
        print("\n🔗 SECTOR CORRELATION: Finding related stocks...")
        print("-" * 60)
        
        related_opportunities = []
        
        for signal in initial_signals:
            symbol = signal.get('symbol', '')
            confidence = signal.get('confidence', 0)
            
            # Find which sector this stock belongs to
            sector = self._find_stock_sector(symbol)
            
            if sector and confidence >= self.good_run_thresholds['min_confidence']:
                # Find other stocks in the same sector
                sector_tickers = self.sector_mappings[sector]['tickers']
                
                for ticker in sector_tickers:
                    if ticker != symbol and ticker not in [s.get('symbol', '') for s in related_opportunities]:
                        # Create related opportunity
                        related = {
                            'symbol': ticker,
                            'sector': sector,
                            'triggered_by': symbol,
                            'confidence': confidence * 0.8,  # Slightly lower confidence
                            'reasoning': f"Correlated with {symbol} move in {sector}",
                            'trade_type': 'SECTOR_CORRELATION',
                            'expected_move': self._estimate_sector_move(sector, confidence)
                        }
                        
                        related_opportunities.append(related)
                
                print(f"   ✅ {symbol} ({sector}): Found {len(sector_tickers)-1} related stocks")
        
        print(f"\n   Total related opportunities: {len(related_opportunities)}")
        return related_opportunities
    
    def _identify_sectors(self, news_item: Dict) -> List[str]:
        """Identify which sectors the news item relates to"""
        text = f"{news_item.get('title', '')} {news_item.get('summary', '')}".lower()
        symbol = news_item.get('symbol', '').upper()
        
        identified_sectors = []
        
        # Check by keywords
        for sector, data in self.sector_mappings.items():
            for keyword in data['keywords']:
                if keyword in text:
                    identified_sectors.append(sector)
                    break
        
        # Check by symbol
        for sector, data in self.sector_mappings.items():
            if symbol in data['tickers']:
                if sector not in identified_sectors:
                    identified_sectors.append(sector)
        
        return identified_sectors
    
    def _is_good_run(self, sector_data: Dict) -> bool:
        """Check if this represents a good run (not necessarily moonshot)"""
        confidence = sector_data['confidence_score'] / len(sector_data['news_items'])
        
        # Good run criteria (lower than moonshot)
        if confidence >= self.good_run_thresholds['min_confidence']:
            return True
        
        # Check for catalyst
        for item in sector_data['news_items']:
            if 'catalyst' in item.get('title', '').lower() or 'breakout' in item.get('title', '').lower():
                return True
        
        return False
    
    async def _create_sector_opportunity(self, sector: str, data: Dict) -> Dict:
        """Create a sector-wide opportunity"""
        
        avg_confidence = data['confidence_score'] / len(data['news_items'])
        
        return {
            'sector': sector,
            'tickers': list(data['tickers']),
            'confidence': avg_confidence,
            'news_count': len(data['news_items']),
            'event_type': self._identify_event_type(data['news_items']),
            'etfs': self.sector_mappings[sector]['etfs'],
            'trade_type': 'SECTOR_WIDE',
            'urgency': 'high' if avg_confidence > 0.6 else 'normal'
        }
    
    def _identify_event_type(self, news_items: List[Dict]) -> str:
        """Identify the type of event driving the sector"""
        titles = ' '.join([item.get('title', '') for item in news_items]).lower()
        
        if any(word in titles for word in ['war', 'conflict', 'tension', 'geopolitical']):
            return 'GEOPOLITICAL'
        elif any(word in titles for word in ['fed', 'rate', 'inflation', 'economy']):
            return 'MACRO_ECONOMIC'
        elif any(word in titles for word in ['earnings', 'profit', 'revenue']):
            return 'EARNINGS'
        elif any(word in titles for word in ['fda', 'approval', 'drug', 'trial']):
            return 'REGULATORY'
        elif any(word in titles for word in ['partnership', 'merger', 'acquisition']):
            return 'M&A'
        else:
            return 'MARKET_SENTIMENT'
    
    def _find_kalshi_events(self, sector: str, opportunity: Dict) -> List[Dict]:
        """Find relevant Kalshi events for the sector"""
        
        events = []
        sector_data = self.sector_mappings[sector]
        
        # Check for specific event types
        event_type = opportunity.get('event_type', 'MARKET_SENTIMENT')
        
        if event_type == 'GEOPOLITICAL' and 'DEFENSE' in sector:
            events.append({
                'title': f"Will defense stocks rise due to geopolitical tensions?",
                'confidence': opportunity['confidence'] * 1.1,
                'type': 'geopolitical_defense'
            })
        
        if event_type == 'MACRO_ECONOMIC':
            events.append({
                'title': f"Will {sector} benefit from Fed decision?",
                'confidence': opportunity['confidence'],
                'type': 'fed_sector_impact'
            })
        
        # General sector performance
        if sector_data['etfs']:
            etf = sector_data['etfs'][0]
            events.append({
                'title': f"Will {etf} outperform the market in 14 days?",
                'confidence': opportunity['confidence'],
                'type': 'sector_performance'
            })
        
        return events
    
    def _calculate_correlation_score(self, opportunity: Dict, kalshi_event: Dict) -> float:
        """Calculate correlation strength between news and Kalshi event"""
        
        base_score = opportunity['confidence'] * kalshi_event['confidence']
        
        # Boost for specific correlations
        if opportunity['event_type'] == 'GEOPOLITICAL' and 'defense' in kalshi_event['type']:
            base_score *= 1.3
        
        if opportunity['event_type'] == 'MACRO_ECONOMIC' and 'fed' in kalshi_event['type']:
            base_score *= 1.2
        
        return min(base_score, 0.95)
    
    def _create_combined_signal(self, opportunity: Dict, kalshi_event: Dict) -> Dict:
        """Create a combined signal from news and Kalshi"""
        
        return {
            'type': 'COMBINED_NEWS_KALSHI',
            'sector': opportunity['sector'],
            'confidence': self._calculate_correlation_score(opportunity, kalshi_event),
            'news_sources': len(opportunity.get('news_items', [])),
            'kalshi_event': kalshi_event,
            'recommendation': 'TRADE' if kalshi_event['confidence'] > 0.6 else 'MONITOR'
        }
    
    def _find_stock_sector(self, symbol: str) -> str:
        """Find which sector a stock belongs to"""
        for sector, data in self.sector_mappings.items():
            if symbol in data['tickers']:
                return sector
        return None
    
    def _estimate_sector_move(self, sector: str, confidence: float) -> float:
        """Estimate potential move for sector stocks"""
        
        # Base move estimation
        base_move = 0.05  # 5% base
        
        # Adjust by confidence
        estimated_move = base_move + (confidence * 0.15)  # Up to 20%
        
        # Sector-specific adjustments
        if sector in ['CRYPTO/DIGITAL', 'COMMODITIES']:
            estimated_move *= 1.5  # Higher volatility
        elif sector in ['FINANCE', 'HEALTHCARE']:
            estimated_move *= 0.8  # Lower volatility
        
        return estimated_move

# Integration with main system
async def run_sector_intelligence(news_items: List[Dict]) -> Dict:
    """Run complete sector intelligence analysis"""
    
    print("=" * 80)
    print("🏭 SECTOR INTELLIGENCE & KALSHI CORRELATION")
    print("=" * 80)
    print("Understanding sector moves and cross-platform opportunities...")
    print("=" * 80)
    
    # Initialize
    from config.secure_config import config
    engine = SectorIntelligenceEngine(config)
    
    # Analyze sector opportunities
    sector_opps = await engine.analyze_sector_opportunities(news_items)
    
    # Check Kalshi correlations
    kalshi_correlations = await engine.check_kalshi_correlations(sector_opps)
    
    # Find related stocks
    initial_signals = news_items[:10]  # Top 10 signals
    related_stocks = await engine.find_related_stocks(initial_signals)
    
    # Combine all results
    results = {
        'sector_opportunities': sector_opps,
        'kalshi_correlations': kalshi_correlations,
        'related_stocks': related_stocks,
        'total_additional_opportunities': len(kalshi_correlations) + len(related_stocks)
    }
    
    # Display summary
    print("\n" + "=" * 80)
    print("📊 SECTOR INTELLIGENCE SUMMARY")
    print("=" * 80)
    print(f"Sector Opportunities: {len(sector_opps)}")
    print(f"Kalshi Correlations: {len(kalshi_correlations)}")
    print(f"Related Stocks: {len(related_stocks)}")
    print(f"Total Additional Opportunities: {results['total_additional_opportunities']}")
    
    if kalshi_correlations:
        print("\n🎯 TOP KALSHI CORRELATIONS:")
        for i, corr in enumerate(kalshi_correlations[:3], 1):
            print(f"{i}. {corr['sector']}: {corr['kalshi_event']['title']}")
            print(f"   Confidence: {corr['correlation_score']:.1%}")
    
    return results

if __name__ == "__main__":
    # Test with sample data
    sample_news = [
        {
            'title': 'Pentagon announces major weapons contract for defense contractors',
            'symbol': 'LMT',
            'confidence': 0.6,
            'summary': 'Defense spending increase expected'
        },
        {
            'title': 'Tech stocks rally on AI adoption news',
            'symbol': 'NVDA',
            'confidence': 0.7,
            'summary': 'Semiconductor demand surges'
        }
    ]
    
    results = asyncio.run(run_sector_intelligence(sample_news))
