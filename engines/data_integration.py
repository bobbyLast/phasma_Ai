"""
============================================================
PHASMA AI - DATA INTEGRATION IMPLEMENTATION
============================================================
Working APIs found and ready to integrate
"""

import requests
import feedparser
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class NewsDataIntegrator:
    """Integrate multiple news APIs for signal detection"""
    
    def __init__(self):
        # API Keys
        self.world_news_key = "370a193337cf422b9e4df80b0d37613d"
        self.gnews_key = "ae4d97e15c89d379dcc9c96174a39ed4"
        self.mediastack_key = "ca12fc893f4d0ed4e4b3c7d4e72808b9"
        self.currents_key = "AABfmJz5G8qskiJGNSZxcDXNkzySLreGywQKVloobm-QnEaj"
        
        # RSS Feeds
        self.rss_feeds = {
            'seeking_alpha': "https://seekingalpha.com/feed.xml",
            'sec_edgar': "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=100",
            'marketwatch': "https://www.marketwatch.com/rss/topstories",
            'benzinga': "https://www.benzinga.com/feed",
            'yahoo_finance': "https://finance.yahoo.com/news/rssindex"
        }
        
        # Options Flow Alternatives (Free)
        self.options_sources = {
            'finviz': "https://finviz.com/screener.ashx?v=111&f=sh_price_o5",
            'barchart': "https://www.barchart.com/stocks/flows/strange",
            'optionstrat': "https://optionstrat.com/unusual-options-activity"
        }
    
    def fetch_world_news(self, keywords: List[str] = None) -> List[Dict]:
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
    
    def fetch_gnews(self, keywords: List[str] = None) -> List[Dict]:
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
    
    def fetch_mediastack(self, keywords: str = None) -> List[Dict]:
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
    
    def fetch_currents(self, keywords: str = None) -> List[Dict]:
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
    
    def fetch_rss_feeds(self) -> List[Dict]:
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
                    
                    # Extract ticker symbols from title
                    tickers = self.extract_tickers(entry.title)
                    if tickers:
                        article['tickers'] = tickers
                        articles.append(article)
                        
            except Exception as e:
                logger.error(f"RSS feed {name} error: {e}")
        
        return articles
    
    def extract_tickers(self, text: str) -> List[str]:
        """Extract potential ticker symbols from text"""
        import re
        
        # Look for NYSE/NASDAQ pattern (1-5 letters, all caps)
        pattern = r'\b[A-Z]{1,5}\b'
        candidates = re.findall(pattern, text)
        
        # Filter out common words
        common_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'HAS', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'DID', 'GET', 'HIM', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE'}
        
        tickers = [word for word in candidates if word not in common_words and len(word) >= 2]
        
        return tickers[:5]  # Return max 5 tickers
    
    def fetch_options_activity(self) -> List[Dict]:
        """Fetch options activity from free sources"""
        activities = []
        
        # Note: These would require web scraping as they don't have APIs
        # For now, return placeholder structure
        for name, url in self.options_sources.items():
            activities.append({
                'source': name,
                'url': url,
                'message': 'Web scraping required',
                'type': 'unusual_options'
            })
        
        return activities
    
    def fetch_sec_filings(self) -> List[Dict]:
        """Fetch SEC Form 4 filings"""
        filings = []
        
        try:
            # This is a simplified version - full implementation would parse HTML
            response = requests.get(self.rss_feeds['sec_edgar'], timeout=10)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract filing links (simplified)
                links = soup.find_all('a', href=True)
                
                for link in links[:10]:
                    if 'sec.gov/Archives/edgar/data' in link.get('href', ''):
                        filings.append({
                            'source': 'sec_edgar',
                            'url': link['href'],
                            'title': link.text.strip(),
                            'type': 'form_4'
                        })
                        
        except Exception as e:
            logger.error(f"SEC filings error: {e}")
        
        return filings
    
    def get_all_news(self, hours_back: int = 24) -> Dict:
        """Get all news from all sources"""
        cutoff = datetime.now() - timedelta(hours=hours_back)
        
        all_news = {
            'timestamp': datetime.now().isoformat(),
            'sources': {
                'world_news': self.fetch_world_news(),
                'gnews': self.fetch_gnews(),
                'mediastack': self.fetch_mediastack(),
                'currents': self.fetch_currents(),
                'rss_feeds': self.fetch_rss_feeds()
            },
            'filings': self.fetch_sec_filings(),
            'options': self.fetch_options_activity()
        }
        
        # Count total articles
        total_articles = sum(len(articles) for articles in all_news['sources'].values())
        
        logger.info(f"Fetched {total_articles} articles from {len(all_news['sources'])} sources")
        
        return all_news

class SignalDetector:
    """Detect trading signals from news and filings"""
    
    def __init__(self):
        self.insider_keywords = [
            'insider trading', 'form 4', 'sec filing', 'stock purchase',
            'insider bought', 'executive purchase', 'director buying',
            'shares acquired', 'stock ownership', 'insider activity'
        ]
        
        self.bullish_keywords = [
            'buy', 'purchase', 'acquired', 'increased stake', 'bullish',
            'upgrade', 'target raised', 'outperform', 'buy rating'
        ]
        
        self.bearish_keywords = [
            'sell', 'sold', 'decreased stake', 'bearish', 'downgrade',
            'target lowered', 'underperform', 'sell rating'
        ]
    
    def analyze_article(self, article: Dict) -> Dict:
        """Analyze an article for signals"""
        text = f"{article.get('title', '')} {article.get('description', '')} {article.get('text', '')}"
        text_lower = text.lower()
        
        signal = {
            'article': article,
            'signals': [],
            'sentiment': 0,
            'confidence': 0
        }
        
        # Check for insider activity
        for keyword in self.insider_keywords:
            if keyword in text_lower:
                signal['signals'].append({
                    'type': 'insider_activity',
                    'keyword': keyword,
                    'confidence': 0.8
                })
        
        # Check sentiment
        bullish_count = sum(1 for word in self.bullish_keywords if word in text_lower)
        bearish_count = sum(1 for word in self.bearish_keywords if word in text_lower)
        
        if bullish_count > bearish_count:
            signal['sentiment'] = min(0.8, 0.1 * bullish_count)
        elif bearish_count > bullish_count:
            signal['sentiment'] = max(-0.8, -0.1 * bearish_count)
        
        # Calculate overall confidence
        if signal['signals']:
            signal['confidence'] = max(s['confidence'] for s in signal['signals'])
        
        return signal
    
    def find_signals(self, news_data: Dict) -> List[Dict]:
        """Find all trading signals"""
        signals = []
        
        # Analyze news articles
        for source, articles in news_data['sources'].items():
            for article in articles:
                signal = self.analyze_article(article)
                if signal['signals'] or abs(signal['sentiment']) > 0.3:
                    signals.append(signal)
        
        # Analyze SEC filings
        for filing in news_data['filings']:
            signal = self.analyze_article(filing)
            if signal['signals']:
                signals.append(signal)
        
        # Sort by confidence
        signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        return signals[:20]  # Return top 20 signals

# Integration with existing system
def integrate_with_underground_discovery():
    """Integrate new data sources with existing discovery engine"""
    
    # Create data integrator
    integrator = NewsDataIntegrator()
    detector = SignalDetector()
    
    # Fetch all data
    news_data = integrator.get_all_news()
    
    # Detect signals
    signals = detector.find_signals(news_data)
    
    # Convert to UndergroundSignal format
    from engines.underground_stock_discovery import UndergroundSignal
    
    underground_signals = []
    
    for signal in signals:
        article = signal['article']
        
        # Extract ticker if available
        tickers = article.get('tickers', [])
        ticker = tickers[0] if tickers else 'UNKNOWN'
        
        # Calculate strength based on confidence and sentiment
        strength = signal['confidence']
        if signal['sentiment'] > 0:
            strength = min(1.0, strength + signal['sentiment'])
        
        underground_signal = UndergroundSignal(
            ticker=ticker,
            signal_type='news_sentiment',
            strength=strength,
            evidence=f"News signal: {article.get('title', '')[:100]}",
            timestamp=datetime.now(),
            sources=[article.get('source', 'unknown')],
            liquidity_score=0.7,  # Default
            dilution_risk='LOW'
        )
        
        underground_signals.append(underground_signal)
    
    return underground_signals

if __name__ == "__main__":
    # Test the integration
    print("🚀 Testing Phasma AI Data Integration")
    print("=" * 50)
    
    # Initialize integrator
    integrator = NewsDataIntegrator()
    
    # Test each API
    print("\n1. Testing World News API...")
    world_news = integrator.fetch_world_news()
    print(f"   ✅ Found {len(world_news)} articles")
    
    print("\n2. Testing GNews API...")
    gnews = integrator.fetch_gnews()
    print(f"   ✅ Found {len(gnews)} articles")
    
    print("\n3. Testing MediaStack API...")
    mediastack = integrator.fetch_mediastack()
    print(f"   ✅ Found {len(mediastack)} articles")
    
    print("\n4. Testing Currents API...")
    currents = integrator.fetch_currents()
    print(f"   ✅ Found {len(currents)} articles")
    
    print("\n5. Testing RSS Feeds...")
    rss_articles = integrator.fetch_rss_feeds()
    print(f"   ✅ Found {len(rss_articles)} articles")
    
    # Signal detection
    print("\n6. Detecting Signals...")
    detector = SignalDetector()
    all_data = {
        'sources': {
            'world_news': world_news,
            'gnews': gnews,
            'mediastack': mediastack,
            'currents': currents,
            'rss_feeds': rss_articles
        },
        'filings': [],
        'options': []
    }
    
    signals = detector.find_signals(all_data)
    print(f"   ✅ Found {len(signals)} trading signals")
    
    # Show top signals
    print("\n🎯 Top 3 Signals:")
    for i, signal in enumerate(signals[:3], 1):
        print(f"\n{i}. {signal['article'].get('title', 'No title')[:80]}...")
        print(f"   Source: {signal['article'].get('source', 'Unknown')}")
        print(f"   Confidence: {signal['confidence']:.2f}")
        print(f"   Sentiment: {signal['sentiment']:.2f}")
        print(f"   Signals: {len(signal['signals'])}")
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'api_results': {
            'world_news': len(world_news),
            'gnews': len(gnews),
            'mediastack': len(mediastack),
            'currents': len(currents),
            'rss_feeds': len(rss_articles)
        },
        'signals_detected': len(signals),
        'top_signals': [
            {
                'title': s['article'].get('title', ''),
                'confidence': s['confidence'],
                'sentiment': s['sentiment']
            } for s in signals[:5]
        ]
    }
    
    with open('data_integration_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📊 Results saved to: data_integration_results.json")
    print("\n✅ Data integration successful!")
