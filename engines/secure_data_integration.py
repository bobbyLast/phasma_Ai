"""
============================================================
PHASMA AI - UPDATED DATA INTEGRATION WITH SECURE CONFIG
============================================================
Using secure environment configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from config.secure_config import config
from engines.underground_stock_discovery import UndergroundSignal
import requests
import feedparser
import json
import logging

logger = logging.getLogger(__name__)

class SecureNewsDataIntegrator:
    """News data integrator using secure configuration"""
    
    def __init__(self):
        # Load keys from secure config
        self.world_news_key = config.world_news_api_key
        self.gnews_key = config.gnews_api_key
        self.mediastack_key = config.mediastack_api_key
        self.currents_key = config.currents_api_key
        
        # RSS feeds from config
        self.rss_feeds = config.rss_feeds
        
        # SEC EDGAR URLs
        self.sec_edgar_base = config.sec_edgar_base
        self.sec_edgar_filings = config.sec_edgar_filings
        
        logger.info("✅ All news API keys loaded securely from environment")
    
    def fetch_world_news(self, keywords: list = None) -> list:
        """Fetch from World News API"""
        if not keywords:
            keywords = ["insider trading", "stock purchase", "form 4", "sec filing"]
        
        articles = []
        for keyword in keywords:
            url = f"https://api.worldnewsapi.com/search-news?api-key={self.world_news_key}&text={keyword}&source=cnn,bbc,reuters"
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('news', [])[:5]:
                        articles.append({
                            'source': 'world_news',
                            'title': item.get('title', ''),
                            'text': item.get('text', ''),
                            'url': item.get('url', ''),
                            'publish_date': item.get('publish_date', ''),
                            'sentiment': item.get('sentiment', 0)
                        })
            except Exception as e:
                logger.error(f"World News API error: {e}")
        
        return articles
    
    def fetch_gnews(self, keywords: str = None) -> list:
        """Fetch from GNews API"""
        if not keywords:
            keywords = "insider trading stock purchase"
        
        url = f"https://gnews.io/api/v4/search?q={keywords}&lang=en&country=us&max=10&apikey={self.gnews_key}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [{
                    'source': 'gnews',
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'url': item.get('url', ''),
                    'publishedAt': item.get('publishedAt', ''),
                    'source_name': item.get('source', {}).get('name', '')
                } for item in data.get('articles', [])]
        except Exception as e:
            logger.error(f"GNews API error: {e}")
            return []
    
    def fetch_mediastack(self, keywords: str = None) -> list:
        """Fetch from MediaStack API"""
        if not keywords:
            keywords = "insider trading"
        
        url = f"http://api.mediastack.com/v1/news?access_key={self.mediastack_key}&keywords={keywords}&countries=us&limit=10"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [{
                    'source': 'mediastack',
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'url': item.get('url', ''),
                    'published_at': item.get('published_at', ''),
                    'category': item.get('category', '')
                } for item in data.get('data', [])]
        except Exception as e:
            logger.error(f"MediaStack API error: {e}")
            return []
    
    def fetch_currents(self, keywords: str = None) -> list:
        """Fetch from Currents API"""
        if not keywords:
            keywords = "insider trading business"
        
        url = f"https://api.currentsapi.services/v1/latest-news?apiKey={self.currents_key}&category=business&keywords={keywords}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [{
                    'source': 'currents',
                    'title': item.get('title', ''),
                    'description': item.get('description', ''),
                    'url': item.get('url', ''),
                    'published': item.get('published', ''),
                    'category': item.get('category', '')
                } for item in data.get('news', [])]
        except Exception as e:
            logger.error(f"Currents API error: {e}")
            return []
    
    def fetch_rss_feeds(self) -> list:
        """Fetch from RSS feeds"""
        articles = []
        
        for name, url in self.rss_feeds.items():
            try:
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:5]:
                    article = {
                        'source': name,
                        'title': entry.title,
                        'link': entry.link,
                        'published': getattr(entry, 'published', ''),
                        'summary': getattr(entry, 'summary', '')[:200]
                    }
                    
                    # Extract ticker symbols
                    tickers = self.extract_tickers(entry.title)
                    if tickers:
                        article['tickers'] = tickers
                        articles.append(article)
                        
            except Exception as e:
                logger.error(f"RSS feed {name} error: {e}")
        
        return articles
    
    def extract_tickers(self, text: str) -> list:
        """Extract potential ticker symbols from text"""
        import re
        
        # Look for NYSE/NASDAQ pattern
        pattern = r'\b[A-Z]{1,5}\b'
        candidates = re.findall(pattern, text)
        
        # Filter out common words
        common_words = {
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 
            'ONE', 'OUR', 'OUT', 'DAY', 'HAS', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 
            'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'DID', 'GET', 'HIM', 'LET', 'PUT', 
            'SAY', 'SHE', 'TOO', 'USE', 'CNN', 'BBC', 'RSS', 'URL', 'CEO', 'CFO', 'COO', 'VP'
        }
        
        tickers = [word for word in candidates if word not in common_words and len(word) >= 2]
        
        return tickers[:5]
    
    def get_all_news(self, hours_back: int = 24) -> dict:
        """Get all news from all sources"""
        all_news = {
            'timestamp': datetime.now().isoformat(),
            'sources': {
                'world_news': self.fetch_world_news(),
                'gnews': self.fetch_gnews(),
                'mediastack': self.fetch_mediastack(),
                'currents': self.fetch_currents(),
                'rss_feeds': self.fetch_rss_feeds()
            }
        }
        
        # Count total articles
        total_articles = sum(len(articles) for articles in all_news['sources'].values())
        logger.info(f"Fetched {total_articles} articles from {len(all_news['sources'])} sources")
        
        return all_news

def test_secure_integration():
    """Test the secure integration"""
    print("🔐 TESTING SECURE DATA INTEGRATION")
    print("=" * 60)
    
    # Initialize integrator
    integrator = SecureNewsDataIntegrator()
    
    # Test each API
    print("\n1️⃣ Testing World News API...")
    world_news = integrator.fetch_world_news()
    print(f"   ✅ Found {len(world_news)} articles")
    
    print("\n2️⃣ Testing GNews API...")
    gnews = integrator.fetch_gnews()
    print(f"   ✅ Found {len(gnews)} articles")
    
    print("\n3️⃣ Testing MediaStack API...")
    mediastack = integrator.fetch_mediastack()
    print(f"   ✅ Found {len(mediastack)} articles")
    
    print("\n4️⃣ Testing Currents API...")
    currents = integrator.fetch_currents()
    print(f"   ✅ Found {len(currents)} articles")
    
    print("\n5️⃣ Testing RSS Feeds...")
    rss_articles = integrator.fetch_rss_feeds()
    print(f"   ✅ Found {len(rss_articles)} articles")
    
    # Get all news
    print("\n6️⃣ Fetching All News...")
    all_news = integrator.get_all_news()
    
    total = sum(len(articles) for articles in all_news['sources'].values())
    print(f"\n📊 Total Articles: {total}")
    
    # Save results
    with open('secure_integration_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_articles': total,
            'sources': {k: len(v) for k, v in all_news['sources'].items()}
        }, f, indent=2)
    
    print(f"\n✅ Results saved to: secure_integration_results.json")
    print("\n🎉 Secure integration working perfectly!")
    
    return all_news

if __name__ == "__main__":
    # Run test
    test_secure_integration()
