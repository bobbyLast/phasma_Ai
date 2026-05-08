#!/usr/bin/env python3
"""
Real-Time Geopolitical News Monitor
Connects to news APIs and analyzes events for stock impacts
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from engines.geopolitical_analyzer import GeopoliticalImpactAnalyzer

class GeopoliticalNewsMonitor:
    """Monitors news for geopolitical events"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.analyzer = GeopoliticalImpactAnalyzer()

        def _normalize_key(value: Optional[str]) -> Optional[str]:
            if value is None:
                return None
            key = str(value).strip()
            if not key:
                return None
            lowered = key.lower()
            if lowered.startswith('your_') or lowered.endswith('_here') or lowered.endswith('here'):
                return None
            return key
        
        # News API configuration
        self.news_api_key = _normalize_key(os.environ.get('NEWS_API_KEY') or self.config.get('news_api_key'))
        self.bing_api_key = _normalize_key(os.environ.get('BING_API_KEY') or self.config.get('bing_api_key'))
        
        # Keywords for geopolitical events
        self.geopolitical_keywords = {
            'conflict': ['war', 'attack', 'invasion', 'military', 'strike', 'conflict', 'tension'],
            'sanctions': ['sanction', 'embargo', 'restriction', 'ban', 'prohibit'],
            'energy': ['oil', 'gas', 'energy', 'petroleum', 'opec', 'production'],
            'countries': ['venezuela', 'russia', 'china', 'iran', 'ukraine', 'israel', 'gaza', 'taiwan'],
            'actions': ['seize', 'takeover', 'nationalize', 'control', 'secure']
        }
    
    def scan_news_headlines(self, hours_back: int = 24) -> List[Dict]:
        """Scan recent news for geopolitical events"""
        print(f"\n📰 SCANNING NEWS (Last {hours_back} hours)...")
        print("-" * 60)
        
        events = []
        
        # Try NewsAPI
        if self.news_api_key:
            events.extend(self._scan_newsapi(hours_back))
        
        # Try Bing News API
        if self.bing_api_key:
            events.extend(self._scan_bing_news(hours_back))
        
        # If no APIs, use demo data
        if not events:
            print("⚠️ No API keys found - using demo data")
            events = self._get_demo_events()
        
        return events
    
    def _scan_newsapi(self, hours_back: int) -> List[Dict]:
        """Scan using NewsAPI"""
        events = []
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': self.news_api_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'from': (datetime.now() - timedelta(hours=hours_back)).isoformat(),
                'q': ' OR '.join(self.geopolitical_keywords['countries'] + 
                                 self.geopolitical_keywords['conflict'][:3]),
                'pageSize': 20
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for article in data.get('articles', []):
                    if self._is_geopolitical(article.get('title', '') + 
                                          article.get('description', '')):
                        events.append({
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'source': article.get('source', {}).get('name', 'NewsAPI'),
                            'url': article.get('url', ''),
                            'timestamp': article.get('publishedAt', ''),
                            'relevance': self._calculate_relevance(
                                article.get('title', '') + 
                                article.get('description', '')
                            )
                        })
                
                print(f"✅ NewsAPI: Found {len(events)} geopolitical events")
            
        except Exception as e:
            print(f"❌ NewsAPI error: {e}")
        
        return events
    
    def _scan_bing_news(self, hours_back: int) -> List[Dict]:
        """Scan using Bing News API"""
        events = []
        
        try:
            headers = {'Ocp-Apim-Subscription-Key': self.bing_api_key}
            query = " OR ".join(self.geopolitical_keywords['countries'])
            
            url = "https://api.bing.microsoft.com/v7.0/news/search"
            params = {
                'q': query,
                'freshness': 'Day',
                'count': 20,
                'sortBy': 'Date'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for article in data.get('value', []):
                    if self._is_geopolitical(article.get('name', '') + 
                                          article.get('description', '')):
                        events.append({
                            'title': article.get('name', ''),
                            'description': article.get('description', ''),
                            'source': article.get('provider', [{}])[0].get('name', 'Bing'),
                            'url': article.get('url', ''),
                            'timestamp': article.get('datePublished', ''),
                            'relevance': self._calculate_relevance(
                                article.get('name', '') + 
                                article.get('description', '')
                            )
                        })
                
                print(f"✅ Bing News: Found {len(events)} geopolitical events")
            
        except Exception as e:
            print(f"❌ Bing News error: {e}")
        
        return events
    
    def _is_geopolitical(self, text: str) -> bool:
        """Check if text is about geopolitical events"""
        text_lower = text.lower()
        
        # Must have at least one country AND one action/conflict keyword
        has_country = any(country in text_lower for country in self.geopolitical_keywords['countries'])
        has_conflict = any(word in text_lower for word in 
                          self.geopolitical_keywords['conflict'] + 
                          self.geopolitical_keywords['actions'])
        
        return has_country and has_conflict
    
    def _calculate_relevance(self, text: str) -> float:
        """Calculate relevance score for an article"""
        text_lower = text.lower()
        score = 0
        
        # Check for high-impact keywords
        high_impact = ['war', 'invasion', 'attack', 'military', 'nuclear']
        for word in high_impact:
            if word in text_lower:
                score += 30
        
        # Check for countries
        for country in self.geopolitical_keywords['countries']:
            if country in text_lower:
                score += 20
        
        # Check for energy impact
        energy_words = ['oil', 'gas', 'energy', 'supply']
        for word in energy_words:
            if word in text_lower:
                score += 15
        
        return min(100, score)
    
    def _get_demo_events(self) -> List[Dict]:
        """Get demo events when no API is available"""
        return [
            {
                'title': 'US Deploys Additional Forces to Venezuelan Border',
                'description': 'Pentagon confirms deployment of 5,000 troops amid escalating tensions over oil facilities',
                'source': 'Demo News',
                'url': '#',
                'timestamp': datetime.now().isoformat(),
                'relevance': 85
            },
            {
                'title': 'Venezuelan Oil Production Halts Amid Conflict',
                'description': 'State oil company PDVSA suspends all exports as US forces secure facilities',
                'source': 'Demo News',
                'url': '#',
                'timestamp': datetime.now().isoformat(),
                'relevance': 90
            },
            {
                'title': 'Oil Prices Surge on Venezuela Supply Concerns',
                'description': 'Brent crude jumps 10% as markets react to potential supply disruption',
                'source': 'Demo News',
                'url': '#',
                'timestamp': datetime.now().isoformat(),
                'relevance': 75
            }
        ]
    
    def analyze_events(self, events: List[Dict]) -> List[Dict]:
        """Analyze found events for stock impacts"""
        print("\n🎯 ANALYZING STOCK IMPACTS...")
        print("-" * 60)
        
        analyses = []
        
        # Sort by relevance
        events.sort(key=lambda x: x['relevance'], reverse=True)
        
        for event in events[:5]:  # Top 5 events
            print(f"\n📰 {event['title']}")
            print(f"   Source: {event['source']} | Relevance: {event['relevance']}/100")
            
            # Analyze the event
            analysis = self.analyzer.analyze_event(event['description'])
            analysis['news_event'] = event
            analyses.append(analysis)
        
        return analyses
    
    def get_top_opportunities(self, analyses: List[Dict], limit: int = 10) -> List[Dict]:
        """Get top investment opportunities from all analyses"""
        all_opportunities = []
        
        for analysis in analyses:
            all_opportunities.extend(analysis['stock_opportunities'])
        
        # Remove duplicates and sort by score
        seen = set()
        unique_opps = []
        
        for opp in all_opportunities:
            symbol = opp['symbol']
            if symbol not in seen:
                seen.add(symbol)
                unique_opps.append(opp)
        
        unique_opps.sort(key=lambda x: x['score'], reverse=True)
        
        return unique_opps[:limit]

def main():
    """Run the geopolitical news monitor"""
    print("🌍 REAL-TIME GEOPOLITICAL NEWS MONITOR")
    print("=" * 60)
    print("Scanning news for investment opportunities...\n")
    
    # Initialize
    config = {
        # Add your API keys here or use environment variables
        # 'news_api_key': 'your_newsapi_key',
        # 'bing_api_key': 'your_bing_api_key'
    }
    
    monitor = GeopoliticalNewsMonitor(config)
    
    # Scan news
    events = monitor.scan_news_headlines(hours_back=24)
    
    if not events:
        print("No geopolitical events found.")
        return
    
    # Analyze events
    analyses = monitor.analyze_events(events)
    
    # Get top opportunities
    opportunities = monitor.get_top_opportunities(analyses)
    
    # Display results
    print("\n🎯 TOP INVESTMENT OPPORTUNITIES")
    print("=" * 60)
    
    for i, opp in enumerate(opportunities, 1):
        print(f"\n{i}. {opp['symbol']} - {opp['name']}")
        print(f"   Price: ${opp['price']:.2f} ({opp['change_pct']:+.1f}%)")
        print(f"   Score: {opp['score']:.0f}/100 | Direction: {opp['direction'].title()}")
        print(f"   Sector: {opp['sector']}")
        print(f"   Market Cap: ${opp['market_cap']/1000000000:.0f}B")
    
    print("\n⚠️  RISKS TO CONSIDER:")
    print("- Geopolitical events are unpredictable")
    print("- Markets may overreact initially")
    print("- Consider hedging positions")
    print("- Monitor news closely for updates")
    
    print("\n💡 NEXT STEPS:")
    print("1. Research top opportunities thoroughly")
    print("2. Consider entry points carefully")
    print("3. Set stop-losses for protection")
    print("4. Diversify across sectors")

if __name__ == "__main__":
    main()
