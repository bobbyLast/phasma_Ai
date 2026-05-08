#!/usr/bin/env python3
"""
Geopolitical Impact Analyzer
Analyzes real-world events and finds stock opportunities
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import yfinance as yf
import pandas as pd

class GeopoliticalImpactAnalyzer:
    """Analyzes geopolitical events and their impact on stocks"""
    
    def __init__(self):
        self.news_sources = [
            "https://newsapi.org/v2/everything",
            "https://api.bing.microsoft.com/v7.0/news/search"
        ]
        self.sector_mappings = {
            # Oil & Energy
            'oil': ['XOM', 'CVX', 'COP', 'SLB', 'HAL', 'BP', 'TOT'],
            'energy': ['XOM', 'CVX', 'COP', 'SLB', 'HAL', 'BP', 'TOT'],
            'oil_services': ['SLB', 'HAL', 'BKR', 'NBR', 'FTI'],
            'domestic_energy': ['XOM', 'CVX', 'COP', 'OXY', 'EOG', 'PXD'],
            'renewables': ['ENPH', 'SEDG', 'FSLR', 'RUN', 'NEE', 'SRE'],

            # Defense & Aerospace
            'defense': ['LMT', 'BA', 'GD', 'NOC', 'RTX', 'TDG', 'HII'],
            'aerospace': ['BA', 'LMT', 'NOC', 'RTX', 'TXT', 'HEI'],
            'weapons': ['LMT', 'GD', 'NOC', 'RTX', 'AXON'],

            # Materials & Commodities
            'steel': ['NUE', 'STLD', 'X', 'CLF', 'TMST'],
            'copper': ['FCX', 'SCCO', 'RIO', 'BHP'],
            'aluminum': ['AA', 'CENX', 'KALU'],
            'gold': ['GLD', 'GDX', 'NEM', 'AEM', 'GOLD'],
            'commodities': ['GLD', 'SLV', 'GDX', 'DBA', 'USO'],
            'materials': ['FCX', 'NEM', 'AA', 'X', 'CLF'],

            # Shipping & Logistics
            'shipping': ['SBLK', 'DRYS', 'NAT', 'TK', 'FRO'],
            'logistics': ['UPS', 'FDX', 'XPO', 'CHRW', 'EXPD'],
            'domestic_manufacturing': ['CAT', 'DE', 'MMM', 'GE', 'HON'],

            # Financial Services
            'banks': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP'],
            'insurance': ['BRK-B', 'AIG', 'MET', 'PRU', 'ALL'],
            'financial_services': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'V'],
            'currencies': ['UUP', 'FXE', 'FXY', 'FXB'],
            'bonds': ['TLT', 'IEF', 'SHY', 'GOVT'],

            # Technology & Cyber
            'cybersecurity': ['CRWD', 'ZS', 'PANW', 'FTNT', 'OKTA'],
            'semiconductors': ['NVDA', 'AMD', 'INTC', 'MU', 'LRCX'],
            'ai_defense': ['PLTR', 'MSFT', 'GOOGL', 'AMZN'],
            'technology': ['MSFT', 'GOOGL', 'AMZN', 'META', 'AAPL', 'NVDA'],

            # Consumer & Retail
            'retail': ['WMT', 'TGT', 'COST', 'HD', 'LOW'],
            'consumer': ['PG', 'KO', 'PEP', 'MCD', 'NKE'],
            'travel': ['DAL', 'UAL', 'AAL', 'JBLU', 'MAR'],
            'airlines': ['DAL', 'UAL', 'AAL', 'JBLU', 'LUV'],
            'transportation': ['UPS', 'FDX', 'UNP', 'NSC', 'CSX'],
            'automotive': ['TSLA', 'F', 'GM', 'STLA', 'HMC'],

            # Other Sectors
            'emerging_markets': ['EEM', 'VWO', 'IEMG', 'FXI'],
            'trade': ['XLI', 'XLB', 'XLE', 'XLF', 'XLK'],
            'local_producers': ['XOM', 'CVX', 'COP', 'CAT', 'DE'],
            'international_companies': ['NKE', 'SAP', 'ASML', 'TM', 'SONY'],
            'energy_intensive_industries': ['NUE', 'AA', 'CLF', 'FCX', 'X'],
            'all_sectors': ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI'],
            'exporters': ['CAT', 'DE', 'BA', 'MMM', 'HON'],
            'importers': ['WMT', 'TGT', 'COST', 'HD', 'LOW'],
            'domestic_producers': ['XOM', 'CVX', 'COP', 'NUE', 'FCX'],
            'alternatives': ['ENPH', 'SEDG', 'FSLR', 'RUN', 'NEE'],
            'water': ['AWK', 'WTRG', 'XYL', 'PHO', 'FIW'],
            'agriculture': ['DBA', 'MOO', 'POT', 'MOS', 'CF'],
            'real_estate': ['VNQ', 'O', 'PLD', 'AMT', 'EQIX'],

            # Latin America Focus
            'latin_america': ['BBA', 'ITUB', 'BBVA', 'SAN', 'BSBR'],
            'brazil': ['BBA', 'ITUB', 'ABEV3.SA', 'PETR4.SA'],
            'venezuela': ['None'], # No direct US-listed Venezuelan stocks
        }
        
        # Impact patterns
        self.impact_patterns = {
            'war_conflict': {
                'positive': ['defense', 'weapons', 'energy', 'cybersecurity'],
                'negative': ['travel', 'consumer', 'banks'],
                'volatile': ['oil', 'gold', 'materials']
            },
            'sanctions': {
                'positive': ['domestic_energy', 'local_producers'],
                'negative': ['international_companies', 'shipping'],
                'volatile': ['currencies', 'commodities']
            },
            'oil_supply_disruption': {
                'positive': ['oil', 'energy', 'oil_services'],
                'negative': ['airlines', 'transportation', 'consumer'],
                'volatile': ['all_sectors']
            },
            'geopolitical_tension': {
                'positive': ['gold', 'defense', 'cybersecurity'],
                'negative': ['emerging_markets', 'trade'],
                'volatile': ['currencies', 'bonds']
            },
            'supply_chain_disruption': {
                'positive': ['shipping', 'logistics', 'domestic_manufacturing'],
                'negative': ['retail', 'consumer', 'automotive'],
                'volatile': ['all_sectors']
            },
            'energy_security': {
                'positive': ['oil', 'energy', 'oil_services', 'renewables'],
                'negative': ['energy_intensive_industries'],
                'volatile': ['all_sectors']
            },
            'cyber_warfare': {
                'positive': ['cybersecurity', 'defense', 'ai_defense'],
                'negative': ['technology', 'financial_services'],
                'volatile': ['all_sectors']
            },
            'currency_war': {
                'positive': ['gold', 'commodities', 'exporters'],
                'negative': ['importers', 'international_companies'],
                'volatile': ['currencies', 'bonds']
            },
            'resource_risk': {
                'positive': ['domestic_producers', 'alternatives'],
                'negative': ['technology', 'manufacturing', 'defense'],
                'volatile': ['commodities', 'materials']
            },
            'political_instability': {
                'positive': ['gold', 'defense', 'cybersecurity'],
                'negative': ['emerging_markets', 'commodities'],
                'volatile': ['currencies', 'bonds']
            },
            'climate_geopolitics': {
                'positive': ['renewables', 'water', 'agriculture'],
                'negative': ['insurance', 'real_estate', 'energy'],
                'volatile': ['commodities', 'agriculture']
            }
        }
    
    def analyze_event(self, event_description: str) -> Dict:
        """Analyze a geopolitical event and find affected stocks"""
        print(f"\n🌍 ANALYZING GEOPOLITICAL EVENT:")
        print(f"Event: {event_description}")
        print("-" * 60)
        
        # Extract key entities and impacts
        analysis = {
            'event': event_description,
            'timestamp': datetime.now().isoformat(),
            'entities': self._extract_entities(event_description),
            'impact_type': self._classify_impact(event_description),
            'affected_sectors': [],
            'stock_opportunities': [],
            'risk_factors': []
        }
        
        # Determine impact type
        impact_type = analysis['impact_type']
        print(f"Impact Type: {impact_type}")
        
        # Find affected sectors
        if impact_type in self.impact_patterns:
            patterns = self.impact_patterns[impact_type]
            
            print("\n📊 SECTOR IMPACTS:")
            for direction, sectors in patterns.items():
                print(f"  {direction.title()}: {', '.join(sectors)}")
                analysis['affected_sectors'].extend(sectors)
            
            # Find specific stocks
            print("\n🎯 STOCK OPPORTUNITIES:")
            for direction, sectors in patterns.items():
                for sector in sectors:
                    if sector in self.sector_mappings:
                        stocks = self.sector_mappings[sector]
                        for symbol in stocks[:3]:  # Top 3 per sector
                            opportunity = self._analyze_stock_impact(symbol, direction, event_description)
                            if opportunity:
                                analysis['stock_opportunities'].append(opportunity)
        
        # Add risk factors
        analysis['risk_factors'] = self._identify_risks(event_description, impact_type)
        
        return analysis
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract key entities from event description"""
        entities = []
        text_lower = text.lower()
        
        # Countries
        countries = ['venezuela', 'united states', 'russia', 'china', 'iran', 'ukraine', 'israel', 'gaza']
        for country in countries:
            if country in text_lower:
                entities.append(country.title())
        
        # Commodities
        commodities = ['oil', 'gas', 'gold', 'copper', 'steel']
        for commodity in commodities:
            if commodity in text_lower:
                entities.append(commodity.title())
        
        # Actions
        actions = ['attack', 'invasion', 'sanctions', 'embargo', 'conflict', 'war']
        for action in actions:
            if action in text_lower:
                entities.append(action.title())
        
        return entities
    
    def _classify_impact(self, text: str) -> str:
        """Classify the type of geopolitical impact"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['war', 'attack', 'invasion', 'conflict', 'military action']):
            return 'war_conflict'
        elif any(word in text_lower for word in ['sanction', 'embargo', 'restriction']):
            return 'sanctions'
        elif any(word in text_lower for word in ['oil', 'supply', 'disruption', 'production', 'oil region']):
            return 'oil_supply_disruption'
        elif any(word in text_lower for word in ['supply chain', 'shipping', 'logistics', 'red sea', 'panama canal']):
            return 'supply_chain_disruption'
        elif any(word in text_lower for word in ['energy security', 'natural gas', 'power', 'electricity', 'winter']):
            return 'energy_security'
        elif any(word in text_lower for word in ['cyber', 'hacking', 'infrastructure', 'state-sponsored']):
            return 'cyber_warfare'
        elif any(word in text_lower for word in ['currency', 'devaluation', 'central bank', 'competitive']):
            return 'currency_war'
        elif any(word in text_lower for word in ['rare earth', 'critical minerals', 'restricts exports', 'supply chain risk']):
            return 'resource_risk'
        elif any(word in text_lower for word in ['political instability', 'election', 'resource nationalism', 'uncertainty']):
            return 'political_instability'
        elif any(word in text_lower for word in ['climate', 'water scarcity', 'extreme weather', 'migration']):
            return 'climate_geopolitics'
        else:
            return 'geopolitical_tension'
    
    def _analyze_stock_impact(self, symbol: str, direction: str, event: str) -> Optional[Dict]:
        """Analyze specific stock impact"""
        try:
            # Get stock data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get recent price movement
            hist = ticker.history(period="5d")
            if len(hist) < 2:
                return None
            
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change_pct = ((current_price - prev_price) / prev_price) * 100
            
            # Calculate opportunity score
            score = 0
            if direction == 'positive' and change_pct > 0:
                score = min(100, 50 + abs(change_pct) * 5)
            elif direction == 'negative' and change_pct < 0:
                score = min(100, 50 + abs(change_pct) * 5)
            elif direction == 'volatile' and abs(change_pct) > 2:
                score = min(100, 40 + abs(change_pct) * 3)
            
            if score < 50:
                return None
            
            opportunity = {
                'symbol': symbol,
                'name': info.get('shortName', symbol),
                'price': current_price,
                'change_pct': change_pct,
                'direction': direction,
                'score': score,
                'volume': hist['Volume'].iloc[-1],
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'Unknown'),
                'thesis': self._generate_thesis(symbol, direction, event)
            }
            
            print(f"  {symbol}: ${current_price:.2f} ({change_pct:+.1f}%) - Score: {score:.0f}/100")
            
            return opportunity
            
        except Exception as e:
            return None
    
    def _generate_thesis(self, symbol: str, direction: str, event: str) -> str:
        """Generate investment thesis for the stock"""
        thesis = f"INVESTMENT THESIS - {symbol}\n"
        thesis += f"Event: {event}\n"
        thesis += f"Impact: {direction.title()}\n\n"
        
        if direction == 'positive':
            thesis += "Why it's positive:\n"
            thesis += "- Increased demand from geopolitical tensions\n"
            thesis += "- Higher prices expected due to supply concerns\n"
            thesis += "- Government contracts likely to increase\n"
        elif direction == 'negative':
            thesis += "Why it's negative:\n"
            thesis += "- Supply chain disruptions\n"
            thesis += "- Reduced demand in affected regions\n"
            thesis += "- Regulatory risks increased\n"
        else:
            thesis += "Why it's volatile:\n"
            thesis += "- High uncertainty in the region\n"
            thesis += "- Price swings expected\n"
            thesis += "- Risk/reward elevated\n"
        
        return thesis
    
    def _identify_risks(self, event: str, impact_type: str) -> List[str]:
        """Identify risk factors"""
        risks = [
            "Escalation risk - Conflict could spread",
            "Market volatility - Expect large swings",
            "Regulatory risk - New sanctions possible",
            "Supply chain disruption - Global impact"
        ]
        
        if 'oil' in event.lower():
            risks.append("Oil price shock - Inflation risk")
        
        if 'united states' in event.lower():
            risks.append("Political risk - Election impact")
        
        return risks
    
    def get_real_time_events(self) -> List[Dict]:
        """Get real-time geopolitical events (simulation)"""
        # In production, this would connect to news APIs
        events = [
            {
                'title': 'US Military Action in Venezuela',
                'description': 'United States forces secure Venezuelan oil facilities',
                'source': 'Breaking News',
                'timestamp': datetime.now().isoformat()
            },
            {
                'title': 'Oil Supply Disruption',
                'description': 'Venezuelan oil production halted amid conflict',
                'source': 'Energy News',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        return events

def main():
    """Demo the geopolitical analyzer"""
    print("🌍 GEOPOLITICAL IMPACT ANALYZER")
    print("=" * 60)
    print("Analyzing real-world events for stock opportunities\n")
    
    analyzer = GeopoliticalImpactAnalyzer()
    
    # Example scenario
    event = "United States attacking Venezuela and taking control of oil production"
    analysis = analyzer.analyze_event(event)
    
    # Show top opportunities
    print("\n🎯 TOP INVESTMENT OPPORTUNITIES:")
    print("=" * 60)
    
    # Sort by score
    opportunities = sorted(analysis['stock_opportunities'], key=lambda x: x['score'], reverse=True)
    
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"\n{i}. {opp['symbol']} - {opp['name']}")
        print(f"   Price: ${opp['price']:.2f} ({opp['change_pct']:+.1f}%)")
        print(f"   Score: {opp['score']:.0f}/100")
        print(f"   Direction: {opp['direction'].title()}")
        print(f"   Market Cap: ${opp['market_cap']/1000000000:.0f}B")
        print(f"   \nThesis Preview:")
        thesis_lines = opp['thesis'].split('\n')[:5]
        for line in thesis_lines:
            if line:
                print(f"     {line}")
    
    print("\n⚠️ RISK FACTORS:")
    for risk in analysis['risk_factors']:
        print(f"  • {risk}")
    
    print("\n💡 RECOMMENDATION:")
    print("Focus on defense and energy stocks during conflicts.")
    print("Consider cybersecurity for modern warfare exposure.")
    print("Always hedge with diversified positions.")

if __name__ == "__main__":
    main()
