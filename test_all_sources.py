"""
============================================================
PHASMA AI - TESTING ALL DATA SOURCES INDIVIDUALLY
============================================================
Testing each of the 42 integrated sources
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from config.secure_config import config
import requests
import feedparser
import json
import time

class AllSourcesTester:
    """Test each data source individually"""
    
    def __init__(self):
        print("=" * 80)
        print("🧪 PHASMA AI - TESTING ALL DATA SOURCES")
        print("=" * 80)
        
        # Load existing keys
        self.world_news_key = config.world_news_api_key
        self.gnews_key = config.gnews_api_key
        self.mediastack_key = config.mediastack_api_key
        self.currents_key = config.currents_api_key
        
        self.results = []
        self.test_count = 0
        self.success_count = 0
    
    def test_source(self, name, url, source_type, api_key=None, params=None):
        """Test a single source"""
        self.test_count += 1
        print(f"\n{self.test_count:2d}. Testing {name}...")
        print(f"    Type: {source_type}")
        print(f"    URL: {url[:80]}{'...' if len(url) > 80 else ''}")
        
        result = {
            'name': name,
            'url': url,
            'type': source_type,
            'status': 'unknown',
            'response_time': 0,
            'data_count': 0,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            if source_type == 'api':
                # Test API
                headers = {}
                if api_key:
                    if 'currents' in url.lower():
                        params['apiKey'] = api_key
                    else:
                        params['api_key'] = api_key
                
                response = requests.get(url, params=params, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data:
                        count = len(data['data'])
                    elif 'articles' in data:
                        count = len(data['articles'])
                    elif 'news' in data:
                        count = len(data['news'])
                    else:
                        count = 1
                    
                    result['status'] = 'success'
                    result['response_time'] = round(response_time, 2)
                    result['data_count'] = count
                    self.success_count += 1
                    
                    print(f"    ✅ SUCCESS - {count} items in {response_time:.2f}s")
                else:
                    result['status'] = 'error'
                    result['error'] = f"HTTP {response.status_code}"
                    print(f"    ❌ ERROR - HTTP {response.status_code}")
            
            elif source_type == 'rss':
                # Test RSS feed
                feed = feedparser.parse(url)
                response_time = time.time() - start_time
                
                if feed.bozo == 0 and len(feed.entries) > 0:
                    result['status'] = 'success'
                    result['response_time'] = round(response_time, 2)
                    result['data_count'] = len(feed.entries)
                    self.success_count += 1
                    
                    print(f"    ✅ SUCCESS - {len(feed.entries)} items in {response_time:.2f}s")
                else:
                    result['status'] = 'error'
                    result['error'] = 'Feed parse error or empty'
                    print(f"    ❌ ERROR - Feed parse error or empty")
            
            elif source_type == 'html':
                # Test HTML page
                response = requests.get(url, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    result['status'] = 'success'
                    result['response_time'] = round(response_time, 2)
                    result['data_count'] = len(response.text)
                    self.success_count += 1
                    
                    print(f"    ✅ SUCCESS - {len(response.text)} chars in {response_time:.2f}s")
                else:
                    result['status'] = 'error'
                    result['error'] = f"HTTP {response.status_code}"
                    print(f"    ❌ ERROR - HTTP {response.status_code}")
            
            elif source_type == 'placeholder':
                # Placeholder for APIs that need keys
                result['status'] = 'needs_key'
                result['error'] = 'API key required'
                print(f"    ⚠️  NEEDS KEY - API key required")
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"    ❌ ERROR - {str(e)[:50]}...")
        
        self.results.append(result)
        time.sleep(0.5)  # Be respectful
    
    def test_all_sources(self):
        """Test all 42 sources"""
        
        print("\n📰 TESTING ORIGINAL NEWS APIS...")
        print("-" * 40)
        
        # 1. Original News APIs
        self.test_source(
            "World News API",
            "https://api.worldnewsapi.com/search-news?api-key=370a193337cf422b9e4df80b0d37613d&text=insider%20trading",
            "api",
            self.world_news_key,
            {'text': 'insider trading', 'source': 'cnn,bbc,reuters'}
        )
        
        self.test_source(
            "GNews API",
            "https://gnews.io/api/v4/search",
            "api",
            self.gnews_key,
            {'q': 'insider trading', 'lang': 'en', 'country': 'us', 'max': 10}
        )
        
        self.test_source(
            "MediaStack API",
            "http://api.mediastack.com/v1/news",
            "api",
            self.mediastack_key,
            {'keywords': 'insider trading', 'countries': 'us', 'limit': 10}
        )
        
        self.test_source(
            "Currents API",
            "https://api.currentsapi.services/v1/latest-news",
            "api",
            self.currents_key,
            {'category': 'business', 'keywords': 'insider trading'}
        )
        
        print("\n📊 TESTING SEC EDGAR RSS FEEDS...")
        print("-" * 40)
        
        # 2. SEC EDGAR RSS Feeds
        self.test_source(
            "SEC EDGAR All Filings",
            "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=100",
            "html"
        )
        
        self.test_source(
            "SEC Structured Disclosure",
            "https://www.sec.gov/structureddata/rss-feeds",
            "html"
        )
        
        print("\n📰 TESTING FINANCIAL RSS FEEDS...")
        print("-" * 40)
        
        # 3. Financial RSS Feeds (testing key ones)
        rss_feeds = [
            ("Seeking Alpha", "https://seekingalpha.com/feed.xml"),
            ("MarketWatch", "https://www.marketwatch.com/rss/topstories"),
            ("Benzinga", "https://www.benzinga.com/feed"),
            ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
            ("Financial Times", "https://www.ft.com/rss/home"),
            ("Reuters Business", "https://www.reuters.com/rssFeed/businessNews"),
            ("Bloomberg Markets", "https://www.bloomberg.com/markets/rss"),
            ("CNBC Markets", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
            ("Wall Street Journal", "https://feeds.wsjonline.com/wsj/xml/rss/3_7014.xml"),
            ("Investopedia", "https://www.investopedia.com/feed.rss"),
            ("Motley Fool", "https://www.fool.com/feed.rss"),
            ("Zacks Investment", "https://www.zacks.com/commentary/rss"),
            ("Fidelity Market", "https://www.fidelity.com/market-news/market-news-rss"),
            ("Charles Schwab", "https://www.schwab.com/rss/marketNews.xml"),
            ("E*TRADE News", "https://us.etrade.com/e/t/etnews/etnews.rss"),
            ("StockTwits", "https://stocktwits.com/streams.rss")
        ]
        
        for name, url in rss_feeds:
            self.test_source(name, url, "rss")
        
        print("\n🌐 TESTING FREE NEWS APIS...")
        print("-" * 40)
        
        # 4. Free News APIs (placeholders)
        free_apis = [
            ("Marketaux API", "https://api.marketaux.com/v1/news", "api", None, {'symbols': 'AAPL,TSLA', 'limit': 10}),
            ("NewsAPI.org", "https://newsapi.org/v2/everything", "api", None, {'q': 'insider trading', 'language': 'en'}),
            ("Newsdata.io", "https://newsdata.io/api/1/news", "api", None, {'q': 'insider trading', 'language': 'en'}),
            ("Finlight API", "https://api.finlight.me/v1/news", "api", None, {'limit': 10}),
            ("EarningsAPI.com", "https://www.earningsapi.com/api/v1/earnings", "api", None, {'date': 'today'}),
            ("API Ninjas Earnings", "https://api.api-ninjas.com/v1/earningscalendar", "api", None, {})
        ]
        
        for name, url, _, key, params in free_apis:
            self.test_source(name, url, "api", key, params)
        
        print("\n💼 TESTING INSIDER TRADING APIS...")
        print("-" * 40)
        
        # 5. Insider Trading APIs
        self.test_source(
            "OpenInsider",
            "http://openinsider.com/screener.php",
            "html",
            None,
            {'s': 'aa_ticker', 'o': 'pltranh'}
        )
        
        self.test_source(
            "SEC-API.io",
            "https://api.sec-api.io/insider-ownership",
            "placeholder",
            None,
            {'ticker': 'AAPL'}
        )
        
        self.test_source(
            "Fintel",
            "https://fintel.io/api/v1/insiders/screener",
            "placeholder",
            None,
            {'minMarketCap': 1000000}
        )
        
        print("\n📊 TESTING OPTIONS SOURCES...")
        print("-" * 40)
        
        # 6. Options Sources
        self.test_source(
            "Unusual Whales",
            "https://api.unusualwhales.com/v1/flow",
            "placeholder",
            None,
            {'limit': 10}
        )
        
        self.test_source(
            "Benzinga Options",
            "https://www.benzinga.com/options/news",
            "html"
        )
        
        self.test_source(
            "FlowAlgo",
            "https://flowalgo.com/api/flow",
            "placeholder",
            None,
            {}
        )
        
        print("\n🛠️ TESTING ADDITIONAL TOOLS...")
        print("-" * 40)
        
        # 7. Additional Tools
        tools = [
            ("EdgarTools GitHub", "https://github.com/nickatnight/edgartools", "html"),
            ("edgarParser GitHub", "https://github.com/nickatnight/edgarParser", "html"),
            ("Visualping", "https://visualping.io", "html"),
            ("n8n Workflows", "https://n8n.io", "html"),
            ("IFTTT", "https://ifttt.com", "html"),
            ("Huginn", "https://github.com/huginn/huginn", "html"),
            ("RSSHub", "https://github.com/DIYgod/RSSHub", "html")
        ]
        
        for name, url, _ in tools:
            self.test_source(name, url, "html")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        # Count by status
        success = len([r for r in self.results if r['status'] == 'success'])
        error = len([r for r in self.results if r['status'] == 'error'])
        needs_key = len([r for r in self.results if r['status'] == 'needs_key'])
        
        print(f"\nTotal Sources Tested: {self.test_count}")
        print(f"✅ Working: {success}")
        print(f"❌ Errors: {error}")
        print(f"⚠️  Need Keys: {needs_key}")
        print(f"📈 Success Rate: {(success/self.test_count)*100:.1f}%")
        
        # Show successful sources
        print("\n✅ SUCCESSFUL SOURCES:")
        print("-" * 40)
        for result in self.results:
            if result['status'] == 'success':
                print(f"   • {result['name']}: {result['data_count']} items ({result['response_time']}s)")
        
        # Show sources needing keys
        if needs_key > 0:
            print("\n⚠️  SOURCES NEEDING API KEYS:")
            print("-" * 40)
            for result in self.results:
                if result['status'] == 'needs_key':
                    print(f"   • {result['name']}: Add key to .env")
        
        # Show errors
        if error > 0:
            print("\n❌ SOURCES WITH ERRORS:")
            print("-" * 40)
            for result in self.results:
                if result['status'] == 'error':
                    print(f"   • {result['name']}: {result['error']}")
        
        # Save results
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tested': self.test_count,
                'success': success,
                'errors': error,
                'needs_key': needs_key,
                'success_rate': (success/self.test_count)*100
            },
            'detailed_results': self.results
        }
        
        with open('all_sources_test_results.json', 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: all_sources_test_results.json")
        
        return test_results

def main():
    """Run all tests"""
    tester = AllSourcesTester()
    tester.test_all_sources()
    results = tester.print_summary()
    
    print("\n🎉 TESTING COMPLETE!")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    main()
