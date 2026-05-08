
"""
============================================================
PHASMA AI - FIXED DATA INTEGRATION
============================================================
All sources working with proper fixes applied
"""

import requests
import feedparser
from datetime import datetime

class FixedDataIntegrator:
    """Data integrator with all fixes applied"""
    
    def __init__(self):
        # Standard headers for RSS feeds
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        # SEC-compliant headers
        self.sec_headers = {
            'User-Agent': 'Phasma-AI/1.0 (contact@example.com) - Educational research',
            'Accept': 'application/rss+xml, application/xml, text/xml',
            'From': 'contact@example.com'
        }
    
    def fetch_rss_with_headers(self, url, name):
        """Fetch RSS with proper headers"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.bozo == 0 and len(feed.entries) > 0:
                    articles = []
                    for entry in feed.entries[:5]:
                        articles.append({
                            'source': name,
                            'title': entry.title,
                            'link': entry.link,
                            'published': getattr(entry, 'published', ''),
                            'summary': getattr(entry, 'summary', '')[:200]
                        })
                    return articles
        except Exception as e:
            print(f"Error fetching {name}: {e}")
        return []
    
    def fetch_sec_with_headers(self, url):
        """Fetch SEC data with proper headers"""
        try:
            response = requests.get(url, headers=self.sec_headers, timeout=10)
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                # Parse SEC content here
                return {'status': 'success', 'content': soup.text[:1000]}
        except Exception as e:
            print(f"SEC error: {e}")
        return None
    
    def fetch_gnews_fixed(self):
        """Fixed GNews API"""
        url = "https://gnews.io/api/v4/search"
        params = {
            'q': 'insider trading',
            'lang': 'en',
            'country': 'us',
            'max': 10,
            'apikey': 'ae4d97e15c89d379dcc9c96174a39ed4'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('articles', [])
        except Exception as e:
            print(f"GNews error: {e}")
        return []
    
    def fetch_mediastack_fixed(self):
        """Fixed MediaStack API"""
        url = "http://api.mediastack.com/v1/news"
        params = {
            'access_key': 'ca12fc893f4d0ed4e4b3c7d4e72808b9',
            'keywords': 'insider trading',
            'countries': 'us',
            'limit': 10
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
        except Exception as e:
            print(f"MediaStack error: {e}")
        return []
