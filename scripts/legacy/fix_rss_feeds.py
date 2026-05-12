"""
============================================================
PHASMA AI - FIXING RSS FEEDS WITH PROPER HEADERS
============================================================
Getting the remaining RSS feeds working
"""

import requests
import feedparser
import time

def fix_rss_feeds():
    """Fix all RSS feeds with proper headers"""
    
    print("🔧 FIXING RSS FEEDS WITH PROPER HEADERS")
    print("=" * 60)
    
    # Headers that work with most sites
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # RSS feeds to fix
    rss_feeds = [
        ("Benzinga", "https://www.benzinga.com/feed"),
        ("Reuters Business", "https://www.reuters.com/rssFeed/businessNews"),
        ("Bloomberg Markets", "https://www.bloomberg.com/markets/rss"),
        ("Wall Street Journal", "https://feeds.wsjonline.com/wsj/xml/rss/3_7014.xml"),
        ("Investopedia", "https://www.investopedia.com/feed.rss"),
        ("Motley Fool", "https://www.fool.com/feed.rss"),
        ("Zacks Investment", "https://www.zacks.com/commentary/rss"),
        ("Fidelity Market", "https://www.fidelity.com/market-news/market-news-rss"),
        ("Charles Schwab", "https://www.schwab.com/rss/marketNews.xml"),
        ("E*TRADE News", "https://us.etrade.com/e/t/etnews/etnews.rss"),
        ("StockTwits", "https://stocktwits.com/streams.rss")
    ]
    
    fixed_count = 0
    total_count = len(rss_feeds)
    
    for name, url in rss_feeds:
        print(f"\n🔧 Testing {name}...")
        
        try:
            # Try with headers
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse the feed
                feed = feedparser.parse(response.content)
                
                if feed.bozo == 0 and len(feed.entries) > 0:
                    print(f"   ✅ SUCCESS - {len(feed.entries)} items")
                    fixed_count += 1
                else:
                    # Try alternative approach
                    print(f"   ⚠️  Trying alternative method...")
                    
                    # Some sites need different approach
                    if 'reuters.com' in url:
                        # Reuters needs specific URL
                        alt_url = "https://www.reuters.com/rssfeed/businessNews"
                        response = requests.get(alt_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            feed = feedparser.parse(response.content)
                            if len(feed.entries) > 0:
                                print(f"   ✅ SUCCESS (alternative) - {len(feed.entries)} items")
                                fixed_count += 1
                    
                    elif 'bloomberg.com' in url:
                        # Bloomberg might need different URL
                        alt_url = "https://www.bloomberg.com/feed"
                        response = requests.get(alt_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            feed = feedparser.parse(response.content)
                            if len(feed.entries) > 0:
                                print(f"   ✅ SUCCESS (alternative) - {len(feed.entries)} items")
                                fixed_count += 1
                    
                    elif 'wsj.com' in url:
                        # WSJ might need subscription
                        print(f"   ❌ Requires subscription")
                    
                    else:
                        print(f"   ❌ Still not working")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")
        
        time.sleep(1)  # Be respectful
    
    print(f"\n📊 RSS FIX SUMMARY:")
    print(f"   Fixed: {fixed_count}/{total_count}")
    print(f"   Success Rate: {(fixed_count/total_count)*100:.1f}%")
    
    return fixed_count

# Alternative RSS feeds that definitely work
alternative_feeds = {
    "CNN Business": "https://rss.cnn.com/rss/money_news_international.rss",
    "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "CNBC World": "https://www.cnbc.com/id/100003114/device/rss/rss.xml",
    "Financial Times": "https://www.ft.com/rss/home",
    "Economic Times": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "Business Insider": "https://feeds.businessinsider.com/all",
    "MarketWatch": "https://www.marketwatch.com/rss/topstories",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Seeking Alpha": "https://seekingalpha.com/feed.xml",
    "The Street": "https://www.thestreet.com/rss/1056"
}

def test_alternative_feeds():
    """Test alternative RSS feeds that definitely work"""
    
    print("\n🔄 TESTING ALTERNATIVE RSS FEEDS")
    print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    working_count = 0
    
    for name, url in alternative_feeds.items():
        print(f"\n🔍 Testing {name}...")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                if feed.bozo == 0 and len(feed.entries) > 0:
                    print(f"   ✅ WORKING - {len(feed.entries)} items")
                    working_count += 1
                else:
                    print(f"   ❌ Parse error")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")
        
        time.sleep(0.5)
    
    print(f"\n📊 ALTERNATIVE FEEDS SUMMARY:")
    print(f"   Working: {working_count}/{len(alternative_feeds)}")
    print(f"   Success Rate: {(working_count/len(alternative_feeds))*100:.1f}%")
    
    return working_count

if __name__ == "__main__":
    # Fix original RSS feeds
    fixed = fix_rss_feeds()
    
    # Test alternatives
    alt_working = test_alternative_feeds()
    
    print("\n" + "=" * 60)
    print("🎉 FINAL RSS SUMMARY")
    print("=" * 60)
    print(f"Original feeds fixed: {fixed}/11")
    print(f"Alternative feeds working: {alt_working}/10")
    print(f"Total RSS feeds available: {fixed + alt_working}")
    print(f"\nRecommendation: Use the {alt_working} alternative feeds that work reliably!")
